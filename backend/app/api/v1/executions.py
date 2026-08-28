"""
Executions API Router
=====================
Handles both browser (JWT) and developer API (X-API-Key) execution requests.

Endpoints:
    POST   /executions/run      — Synchronous execution (result returned immediately)
    POST   /executions/queue    — Async via Celery/Redis (returns execution_id)
    GET    /executions/{id}     — Get result by ID (polling endpoint)
    GET    /executions          — List execution history with filters
    POST   /executions/{id}/cancel — Cancel a queued/running execution
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.core.rate_limiter import limiter, get_plan_rate_limit
from app.models.user import User
from app.models.api_key import APIKey
from app.models.execution import Execution, ExecutionStatus, ExecutionSource
from app.schemas.execution import (
    CodeExecutionRequest,
    ExecutionResult,
    ExecutionQueueResponse,
    ExecutionSummary,
)
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user, get_current_user_or_api_key
from app.services.language_registry import language_registry
from app.services.execution_service import execution_service
from app.services.usage_service import usage_service

router = APIRouter(prefix="/executions", tags=["Executions"])
logger = logging.getLogger(__name__)


# ── POST /executions/run — synchronous ────────────────────────────────────────
@router.post(
    "/run",
    response_model=ResponseEnvelope[ExecutionResult],
    summary="Execute code (synchronous)",
)
@limiter.limit("30/minute")
def run_code(
    request: Request,  # Required for rate limiter
    payload: CodeExecutionRequest,
    auth_data: Tuple[User, Optional[APIKey]] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
):
    """
    Execute code in a sandboxed Docker container and return the result immediately.
    Accepts both JWT (browser editor) and X-API-Key (developer API).
    """
    user, api_key = auth_data
    is_api = api_key is not None

    # 1. Language validation
    if not language_registry.is_supported(payload.language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{payload.language}' is not supported.",
        )

    # 2. Usage quota check
    can_run, reason = usage_service.can_execute(db, user, is_api=is_api)
    if not can_run:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    # 3. Create execution record
    execution = Execution(
        user_id=user.id,
        project_id=payload.project_id,
        api_key_id=api_key.id if api_key else None,
        language=payload.language,
        code=payload.code,
        stdin_data=payload.stdin or "",
        status=ExecutionStatus.RUNNING,
        source=ExecutionSource.REST_API if is_api else ExecutionSource.WEB_EDITOR,
        started_at=datetime.now(timezone.utc),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 4. Run in Docker sandbox
    from app.services.subscription_service import subscription_service
    plan = subscription_service.get_user_plan(db, user)
    timeout = payload.timeout_seconds or plan.timeout_seconds

    result = execution_service.execute(
        language_key=execution.language,
        code=execution.code,
        stdin_data=execution.stdin_data or "",
        timeout_override=timeout,
    )

    # 5. Persist result
    execution.status = result.status
    execution.stdout = result.stdout
    execution.stderr = result.stderr
    execution.exit_code = result.exit_code
    execution.execution_time = result.execution_time
    execution.memory_used_bytes = result.memory_used_bytes
    execution.completed_at = datetime.now(timezone.utc)
    db.commit()

    # 6. Record usage
    usage_service.record_execution(
        db=db,
        user_id=user.id,
        execution_time=result.execution_time or 0.0,
        is_api=is_api,
        success=(result.exit_code == 0),
    )

    logger.info(
        f"[Execution] id={execution.id} user={user.id} "
        f"lang={execution.language} status={result.status} "
        f"time={result.execution_time}s"
    )

    return ResponseEnvelope(
        success=True,
        message=f"Execution completed: {result.status}",
        data=ExecutionResult(
            execution_id=execution.id,
            status=execution.status,
            language=execution.language,
            stdout=execution.stdout or "",
            stderr=execution.stderr or "",
            exit_code=execution.exit_code,
            execution_time=execution.execution_time,
            memory_used_bytes=execution.memory_used_bytes,
            created_at=execution.created_at,
            completed_at=execution.completed_at,
        ),
    )


# ── POST /executions/queue — async via Celery ─────────────────────────────────
@router.post(
    "/queue",
    response_model=ResponseEnvelope[ExecutionQueueResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue code execution (async)",
)
@limiter.limit("30/minute")
def queue_execution(
    request: Request,  # Required for rate limiter
    payload: CodeExecutionRequest,
    auth_data: Tuple[User, Optional[APIKey]] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
):
    """
    Submit code execution to the Redis queue. Returns execution_id for polling.
    Use GET /executions/{id} to retrieve results.
    """
    user, api_key = auth_data
    is_api = api_key is not None

    if not language_registry.is_supported(payload.language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{payload.language}' is not supported.",
        )

    can_run, reason = usage_service.can_execute(db, user, is_api=is_api)
    if not can_run:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=reason)

    execution = Execution(
        user_id=user.id,
        project_id=payload.project_id,
        api_key_id=api_key.id if api_key else None,
        language=payload.language,
        code=payload.code,
        stdin_data=payload.stdin or "",
        status=ExecutionStatus.QUEUED,
        source=ExecutionSource.REST_API if is_api else ExecutionSource.WEB_EDITOR,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Dispatch to Celery worker (falls back to inline if Redis is down)
    try:
        from app.workers.tasks import run_sandboxed_execution
        run_sandboxed_execution.delay(execution.id)
        logger.info(f"[Queue] Dispatched execution {execution.id} to Celery")
    except Exception as exc:
        logger.warning(f"[Queue] Celery unavailable ({exc}), running inline fallback")
        from app.services.subscription_service import subscription_service
        plan = subscription_service.get_user_plan(db, user)
        timeout = payload.timeout_seconds or plan.timeout_seconds
        result = execution_service.execute(
            language_key=execution.language,
            code=execution.code,
            stdin_data=execution.stdin_data or "",
            timeout_override=timeout,
        )
        execution.status = result.status
        execution.stdout = result.stdout
        execution.stderr = result.stderr
        execution.exit_code = result.exit_code
        execution.execution_time = result.execution_time
        execution.memory_used_bytes = result.memory_used_bytes
        execution.completed_at = datetime.now(timezone.utc)
        db.commit()
        usage_service.record_execution(db, user.id, result.execution_time or 0.0, is_api)

    return ResponseEnvelope(
        success=True,
        data=ExecutionQueueResponse(
            execution_id=execution.id,
            status=execution.status,
            message="Execution queued. Poll GET /executions/{id} for results.",
        ),
    )


# ── GET /executions/{id} — polling endpoint ───────────────────────────────────
@router.get(
    "/{execution_id}",
    response_model=ResponseEnvelope[ExecutionResult],
    summary="Get execution result",
)
def get_execution(
    execution_id: str,
    auth_data: Tuple[User, Optional[APIKey]] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
):
    """Fetch execution result by ID. Use for polling async executions."""
    user, _ = auth_data
    execution = (
        db.query(Execution)
        .filter(Execution.id == execution_id, Execution.user_id == user.id)
        .first()
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or access denied.",
        )

    return ResponseEnvelope(
        success=True,
        data=ExecutionResult(
            execution_id=execution.id,
            status=execution.status,
            language=execution.language,
            stdout=execution.stdout or "",
            stderr=execution.stderr or "",
            exit_code=execution.exit_code,
            execution_time=execution.execution_time,
            memory_used_bytes=execution.memory_used_bytes,
            created_at=execution.created_at,
            completed_at=execution.completed_at,
        ),
    )


# ── GET /executions — history list ────────────────────────────────────────────
@router.get(
    "",
    response_model=ResponseEnvelope[dict],
    summary="List execution history",
)
def list_executions(
    language: Optional[str] = Query(None),
    exec_status: Optional[str] = Query(None, alias="status"),
    project_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    auth_data: Tuple[User, Optional[APIKey]] = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db),
):
    """Return paginated execution history with optional filters."""
    user, _ = auth_data

    query = db.query(Execution).filter(Execution.user_id == user.id)
    if language:
        query = query.filter(Execution.language == language.lower())
    if exec_status:
        query = query.filter(Execution.status == exec_status.upper())
    if project_id:
        query = query.filter(Execution.project_id == project_id)

    total = query.count()
    items = query.order_by(desc(Execution.created_at)).offset((page - 1) * size).limit(size).all()

    return ResponseEnvelope(
        success=True,
        data={
            "items": [
                ExecutionResult(
                    execution_id=e.id,
                    status=e.status,
                    language=e.language,
                    stdout=e.stdout or "",
                    stderr=e.stderr or "",
                    exit_code=e.exit_code,
                    execution_time=e.execution_time,
                    memory_used_bytes=e.memory_used_bytes,
                    created_at=e.created_at,
                    completed_at=e.completed_at,
                )
                for e in items
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": max(1, (total + size - 1) // size),
        },
    )


# ── POST /executions/{id}/cancel ─────────────────────────────────────────────
@router.post(
    "/{execution_id}/cancel",
    response_model=ResponseEnvelope[dict],
    summary="Cancel a queued or running execution",
)
def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an execution that is still QUEUED or RUNNING."""
    execution = (
        db.query(Execution)
        .filter(Execution.id == execution_id, Execution.user_id == current_user.id)
        .first()
    )
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found.")

    if execution.status not in (ExecutionStatus.QUEUED, ExecutionStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution with status '{execution.status}'.",
        )

    execution.status = ExecutionStatus.CANCELLED
    execution.completed_at = datetime.now(timezone.utc)
    db.commit()

    return ResponseEnvelope(
        success=True,
        message="Execution cancelled.",
        data={"execution_id": execution_id, "status": ExecutionStatus.CANCELLED},
    )
