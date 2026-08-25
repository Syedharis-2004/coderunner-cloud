"""
CodeRunner Cloud — Core Execution Service
==========================================
Orchestrates isolated Docker container creation, resource limiting,
code injection, execution, output capture, and cleanup.

Architecture:
    ExecutionRequest → ExecutionService → DockerEngine → Container → ExecutionResult

Security Controls Enforced:
    - Containers run as non-root UID 1000
    - All Linux capabilities dropped (cap_drop=ALL)
    - no-new-privileges secopt applied
    - Network disabled (network_disabled=True)
    - CPU quota enforced (cpu_quota)
    - Memory limit enforced (mem_limit)
    - PID limit enforced to prevent fork bombs (pids_limit)
    - tmpfs with noexec,nosuid for /tmp
    - Source code injected via tarball (no host directory mounts)
    - Container forcibly removed after execution
    - Temporary files cleaned up regardless of outcome
"""

import io
import os
import time
import tarfile
import tempfile
import shutil
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.docker_engine import docker_engine
from app.services.language_registry import language_registry, LanguageConfig

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Execution Status Enum (matches DB model)
# ──────────────────────────────────────────────────────────────────────────────
class ExecutionStatus:
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    MEMORY_LIMIT = "MEMORY_LIMIT"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    CANCELLED = "CANCELLED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class ExecutionResult:
    """Structured result from a code execution run."""
    status: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    memory_used_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "memory_used_bytes": self.memory_used_bytes,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Core Execution Service
# ──────────────────────────────────────────────────────────────────────────────
class ExecutionService:
    """
    Primary entry point for code execution.
    Automatically selects Docker (preferred) or local fallback.
    """

    @classmethod
    def execute(
        cls,
        language_key: str,
        code: str,
        stdin_data: str = "",
        timeout_override: Optional[int] = None,
    ) -> ExecutionResult:
        """
        Execute code in a fully sandboxed Docker container.

        Args:
            language_key:     e.g. "python", "javascript", "cpp"
            code:             Raw source code string
            stdin_data:       Optional stdin input string
            timeout_override: Override the default timeout (seconds)

        Returns:
            ExecutionResult with all execution metadata
        """
        # 1. Validate language
        lang_config = language_registry.get(language_key)
        if not lang_config:
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                stdout="",
                stderr=f"Unsupported language: '{language_key}'",
                exit_code=1,
                execution_time=0.0,
                memory_used_bytes=0,
            )

        # 2. Validate source code size
        code_bytes = len(code.encode("utf-8"))
        if code_bytes > settings.MAX_SOURCE_CODE_SIZE_BYTES:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr=(
                    f"Source code size ({code_bytes} bytes) exceeds the "
                    f"maximum limit of {settings.MAX_SOURCE_CODE_SIZE_BYTES} bytes."
                ),
                exit_code=1,
                execution_time=0.0,
                memory_used_bytes=0,
            )

        # 3. Resolve timeout — per-language override > user override > system default
        timeout = (
            lang_config.timeout_override
            or timeout_override
            or settings.DEFAULT_EXECUTION_TIMEOUT
        )

        # 4. Dispatch to Docker or local fallback
        client = docker_engine.get_client()
        if client is not None:
            logger.info(f"Executing [{language_key}] in Docker sandbox (timeout={timeout}s)")
            return cls._execute_in_docker(client, lang_config, code, stdin_data, timeout)
        else:
            logger.warning(
                "Docker unavailable — using local subprocess fallback "
                "(NOT SAFE FOR PRODUCTION)."
            )
            return cls._execute_in_local_process(lang_config, code, stdin_data, timeout)

    # ──────────────────────────────────────────────────────────────────────────
    # Docker Sandbox Execution
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _execute_in_docker(
        cls,
        client: Any,
        lang_config: LanguageConfig,
        code: str,
        stdin_data: str,
        timeout: int,
    ) -> ExecutionResult:
        """
        Execute inside an isolated Docker container with strict security bounds.

        Security model:
        - Non-root user (UID 1000)
        - All capabilities dropped
        - Network disabled
        - CPU and memory limits applied
        - PID limit to prevent fork bombs
        - tmpfs with noexec for /tmp
        - Code injected via tarball stream (no bind mounts)
        - Container force-removed after execution
        """
        temp_dir = tempfile.mkdtemp(prefix="crc_exec_")
        container = None
        start_time = time.perf_counter()

        try:
            # Write source code
            source_path = os.path.join(temp_dir, lang_config.source_filename)
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Write stdin data to a file for redirection
            stdin_path = os.path.join(temp_dir, "stdin.txt")
            with open(stdin_path, "w", encoding="utf-8") as f:
                f.write(stdin_data or "")

            # Build execution command (compile + run or just run)
            if lang_config.compile_cmd:
                full_cmd = (
                    f"sh -c '{lang_config.compile_cmd} "
                    f"&& {lang_config.run_cmd} < stdin.txt'"
                )
            else:
                full_cmd = f"sh -c '{lang_config.run_cmd} < stdin.txt'"

            # Create sandboxed container (NOT yet started)
            container = client.containers.create(
                image=lang_config.image,
                command=full_cmd,
                working_dir="/home/sandboxuser",
                network_disabled=True,
                mem_limit=lang_config.memory_limit_override or settings.DEFAULT_MEMORY_LIMIT,
                cpu_quota=settings.DEFAULT_CPU_QUOTA,
                pids_limit=settings.DEFAULT_PIDS_LIMIT,
                user=1000,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                tmpfs={"/tmp": "rw,noexec,nosuid,size=32m"},
            )

            # Inject source files via tarball stream (avoids bind mounts)
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                for fname in os.listdir(temp_dir):
                    tar.add(os.path.join(temp_dir, fname), arcname=fname)
            tar_stream.seek(0)
            container.put_archive("/home/sandboxuser", tar_stream)

            # Start container
            container.start()

            # Wait with timeout enforcement
            try:
                result = container.wait(timeout=timeout)
                elapsed = time.perf_counter() - start_time
                exit_code = result.get("StatusCode", 0)

                stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

                # Truncate to max output size
                if len(stdout) > settings.MAX_OUTPUT_SIZE_BYTES:
                    stdout = stdout[:settings.MAX_OUTPUT_SIZE_BYTES] + "\n... [Output Truncated]"
                if len(stderr) > settings.MAX_OUTPUT_SIZE_BYTES:
                    stderr = stderr[:settings.MAX_OUTPUT_SIZE_BYTES] + "\n... [Error Truncated]"

                # Determine status
                if exit_code == 0:
                    status = ExecutionStatus.SUCCESS
                else:
                    # Heuristic: distinguish compile errors from runtime errors
                    status = (
                        ExecutionStatus.COMPILE_ERROR
                        if lang_config.compile_cmd and "error:" in stderr.lower()
                        else ExecutionStatus.RUNTIME_ERROR
                        if exit_code != 0
                        else ExecutionStatus.FAILED
                    )

                # Collect memory stats
                memory_bytes = 0
                try:
                    stats = container.stats(stream=False)
                    memory_bytes = stats.get("memory_stats", {}).get("usage", 0)
                except Exception:
                    pass

                return ExecutionResult(
                    status=status,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    execution_time=round(elapsed, 4),
                    memory_used_bytes=memory_bytes,
                )

            except Exception:
                # Timeout — kill the container
                elapsed = time.perf_counter() - start_time
                try:
                    container.kill()
                except Exception:
                    pass

                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds.",
                    exit_code=124,
                    execution_time=round(elapsed, 4),
                    memory_used_bytes=0,
                )

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Docker execution error: {exc}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                stdout="",
                stderr=f"Container runtime error: {str(exc)}",
                exit_code=1,
                execution_time=round(elapsed, 4),
                memory_used_bytes=0,
            )

        finally:
            # Always force-remove the container and clean up temp files
            if container is not None:
                try:
                    container.remove(force=True)
                    logger.debug(f"Container {container.id[:12]} removed.")
                except Exception:
                    pass
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Local Subprocess Fallback (Development Only)
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def _execute_in_local_process(
        cls,
        lang_config: LanguageConfig,
        code: str,
        stdin_data: str,
        timeout: int,
    ) -> ExecutionResult:
        """
        Fallback execution via subprocess when Docker is unavailable.
        ⚠️  NOT SAFE FOR PRODUCTION — runs code directly on the host.
        """
        temp_dir = tempfile.mkdtemp(prefix="crc_local_")
        start_time = time.perf_counter()

        try:
            source_path = os.path.join(temp_dir, lang_config.source_filename)
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Build local command
            key = lang_config.key
            if key == "python":
                cmd = ["python", source_path]
            elif key in ("javascript", "nodejs"):
                cmd = ["node", source_path]
            elif key == "cpp":
                bin_path = os.path.join(temp_dir, "main_bin")
                compile_result = subprocess.run(
                    ["g++", "-O2", "-std=c++20", source_path, "-o", bin_path],
                    capture_output=True, text=True, timeout=timeout, cwd=temp_dir,
                )
                if compile_result.returncode != 0:
                    elapsed = time.perf_counter() - start_time
                    return ExecutionResult(
                        status=ExecutionStatus.COMPILE_ERROR,
                        stdout="",
                        stderr=compile_result.stderr,
                        exit_code=compile_result.returncode,
                        execution_time=round(elapsed, 4),
                        memory_used_bytes=0,
                    )
                cmd = [bin_path]
            else:
                return ExecutionResult(
                    status=ExecutionStatus.SYSTEM_ERROR,
                    stdout="",
                    stderr=f"Local runtime not available for '{lang_config.key}'.",
                    exit_code=1,
                    execution_time=0.0,
                    memory_used_bytes=0,
                )

            proc = subprocess.run(
                cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=temp_dir,
            )
            elapsed = time.perf_counter() - start_time
            status = ExecutionStatus.SUCCESS if proc.returncode == 0 else ExecutionStatus.RUNTIME_ERROR

            return ExecutionResult(
                status=status,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                execution_time=round(elapsed, 4),
                memory_used_bytes=0,
            )

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds.",
                exit_code=124,
                execution_time=round(elapsed, 4),
                memory_used_bytes=0,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                status=ExecutionStatus.SYSTEM_ERROR,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                execution_time=round(elapsed, 4),
                memory_used_bytes=0,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Module-level singleton
execution_service = ExecutionService()
