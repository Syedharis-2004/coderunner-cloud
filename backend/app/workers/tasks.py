"""
CodeRunner Cloud — Celery Execution Worker
==========================================
Processes sandboxed code execution jobs from the Redis queue.

Flow:
    POST /executions/queue
        → DB record (status=QUEUED)
        → Redis queue
        → This worker picks the job
        → Docker sandbox execution
        → DB record updated (status=SUCCESS/FAILED/TIMEOUT/...)
"""
import logging
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.execution import Execution, ExecutionStatus

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    """Open a fresh sync DB session for the worker process."""
    return SessionLocal()


@celery_app.task(
    bind=True,
    name="run_sandboxed_execution",
    max_retries=1,
    default_retry_delay=5,
)
def run_sandboxed_execution(self, execution_id: str) -> dict:
    """
    Celery task — picks an execution record from the queue, runs it inside
    a Docker sandbox, and persists the result back to the database.

    Args:
        execution_id: UUID of the Execution row to process.
    """
    logger.info(f"[Worker] Received execution job: {execution_id}")
    db = _get_db()

    try:
        # ── 1. Fetch execution record ──────────────────────────────────────────
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            logger.error(f"[Worker] Execution {execution_id} not found in DB.")
            return {"error": "not_found"}

        if execution.status not in (ExecutionStatus.QUEUED,):
            logger.warning(
                f"[Worker] Execution {execution_id} already processed "
                f"(status={execution.status}). Skipping."
            )
            return {"status": execution.status}

        # ── 2. Mark as RUNNING ─────────────────────────────────────────────────
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        db.commit()

        # ── 3. Import and run sandboxed execution ──────────────────────────────
        # Import here to avoid circular imports at module load time
        from app.services.execution_service import execution_service

        result = execution_service.execute(
            language_key=execution.language,
            code=execution.code,
            stdin_data=execution.stdin_data or "",
        )

        # ── 4. Persist result ──────────────────────────────────────────────────
        execution.status = result.status
        execution.stdout = result.stdout
        execution.stderr = result.stderr
        execution.exit_code = result.exit_code
        execution.execution_time = result.execution_time
        execution.memory_used_bytes = result.memory_used_bytes
        execution.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"[Worker] Execution {execution_id} completed → "
            f"status={result.status} time={result.execution_time}s"
        )
        return result.to_dict()

    except SoftTimeLimitExceeded:
        logger.warning(f"[Worker] Soft time limit exceeded for {execution_id}.")
        try:
            execution = db.query(Execution).filter(Execution.id == execution_id).first()
            if execution:
                execution.status = ExecutionStatus.TIMEOUT
                execution.stderr = "Worker process soft time limit exceeded."
                execution.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        return {"status": ExecutionStatus.TIMEOUT}

    except Exception as exc:
        logger.exception(f"[Worker] Unexpected error for {execution_id}: {exc}")
        try:
            execution = db.query(Execution).filter(Execution.id == execution_id).first()
            if execution:
                execution.status = ExecutionStatus.SYSTEM_ERROR
                execution.stderr = f"Worker error: {str(exc)}"
                execution.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass

        # Retry once after 5 seconds
        try:
            raise self.retry(exc=exc, countdown=5)
        except self.MaxRetriesExceededError:
            return {"status": ExecutionStatus.SYSTEM_ERROR}

    finally:
        db.close()
