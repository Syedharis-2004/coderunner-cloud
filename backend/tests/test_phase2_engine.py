"""
Phase 2 Test — Verify Language Registry and Execution Service load correctly.
Run with: python -m pytest tests/test_phase2_engine.py -v
"""
import pytest
from app.services.language_registry import language_registry
from app.services.execution_service import ExecutionService, ExecutionStatus


class TestLanguageRegistry:
    def test_all_languages_registered(self):
        langs = language_registry.list_all()
        keys = [l["key"] for l in langs]
        assert "python" in keys
        assert "javascript" in keys
        assert "cpp" in keys
        assert "typescript" in keys
        assert "csharp" in keys

    def test_get_python(self):
        lang = language_registry.get("python")
        assert lang is not None
        assert lang.image == "python:3.11-slim"
        assert lang.source_filename == "main.py"
        assert lang.compile_cmd is None

    def test_get_cpp(self):
        lang = language_registry.get("cpp")
        assert lang is not None
        assert lang.compile_cmd is not None
        assert "g++" in lang.compile_cmd

    def test_unsupported_language(self):
        lang = language_registry.get("brainfuck")
        assert lang is None

    def test_is_supported(self):
        assert language_registry.is_supported("python") is True
        assert language_registry.is_supported("ruby") is False

    def test_case_insensitive_lookup(self):
        assert language_registry.get("PYTHON") is not None
        assert language_registry.get("JavaScript") is not None


class TestExecutionServiceValidation:
    def test_unsupported_language_returns_error(self):
        result = ExecutionService.execute("brainfuck", "+++")
        assert result.status == ExecutionStatus.SYSTEM_ERROR
        assert result.exit_code == 1

    def test_code_too_large_returns_error(self):
        huge_code = "x = 1\n" * 20000  # Way over 64KB
        result = ExecutionService.execute("python", huge_code)
        assert result.status == ExecutionStatus.FAILED
        assert "exceeds" in result.stderr

    def test_execution_result_has_required_fields(self):
        result = ExecutionService.execute("python", 'print("hello")')
        assert hasattr(result, "status")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "exit_code")
        assert hasattr(result, "execution_time")
        assert hasattr(result, "memory_used_bytes")

    def test_to_dict(self):
        result = ExecutionService.execute("brainfuck", "")
        d = result.to_dict()
        assert "status" in d
        assert "stdout" in d
        assert "stderr" in d
        assert "exit_code" in d
