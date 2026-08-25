"""
Admin API Router
================
Endpoints strictly reserved for users with the ADMIN role.
Provides system-wide metrics, user management, and health checks.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User, UserRole, UserPlan
from app.models.execution import Execution
from app.models.usage import UsageRecord
from app.schemas.common import ResponseEnvelope
from app.schemas.user import UserRead
from app.api.deps import require_admin
from app.services.docker_engine import docker_engine
from app.services.usage_service import _current_period

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

# Apply require_admin dependency to all routes in this router
router_dependencies = [Depends(require_admin)]


@router.get(
    "/metrics",
    response_model=ResponseEnvelope[dict],
    dependencies=router_dependencies,
    summary="Get system-wide metrics",
)
def get_system_metrics(db: Session = Depends(get_db)):
    """Retrieve high-level system metrics for the admin dashboard."""
    period = _current_period()

    # User metrics
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    
    # Execution metrics (All time)
    total_executions = db.query(func.count(Execution.id)).scalar() or 0
    
    # Usage metrics (Current month)
    monthly_usage_records = db.query(UsageRecord).filter(UsageRecord.billing_period == period).all()
    monthly_executions = sum(record.total_executions for record in monthly_usage_records)
    monthly_compute_seconds = sum(record.total_compute_seconds for record in monthly_usage_records)

    # Docker health
    docker_status = "connected" if docker_engine.is_available() else "unavailable"

    return ResponseEnvelope(
        success=True,
        data={
            "period": period,
            "users": {
                "total": total_users,
                "active": active_users,
            },
            "executions": {
                "total_all_time": total_executions,
                "current_month": monthly_executions,
                "monthly_compute_seconds": round(monthly_compute_seconds, 2),
            },
            "system": {
                "docker": docker_status,
            }
        }
    )


@router.get(
    "/users",
    response_model=ResponseEnvelope[List[UserRead]],
    dependencies=router_dependencies,
    summary="List all users",
)
def list_all_users(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    """Retrieve a paginated list of all registered users."""
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return ResponseEnvelope(
        success=True,
        data=[UserRead.model_validate(u) for u in users]
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=ResponseEnvelope[UserRead],
    dependencies=router_dependencies,
    summary="Activate/Deactivate a user",
)
def toggle_user_status(
    user_id: str,
    is_active: bool,
    db: Session = Depends(get_db)
):
    """Enable or disable a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Cannot deactivate admin accounts")

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    
    logger.info(f"[Admin] User {user_id} active status set to {is_active}")
    
    return ResponseEnvelope(
        success=True,
        message=f"User account {'activated' if is_active else 'deactivated'}",
        data=UserRead.model_validate(user)
    )

@router.patch(
    "/users/{user_id}/plan",
    response_model=ResponseEnvelope[UserRead],
    dependencies=router_dependencies,
    summary="Upgrade/Downgrade a user's plan",
)
def change_user_plan(
    user_id: str,
    plan: UserPlan,
    db: Session = Depends(get_db)
):
    """Change a user's billing/access plan."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan = plan
    db.commit()
    db.refresh(user)
    
    logger.info(f"[Admin] User {user_id} plan changed to {plan.value}")
    
    return ResponseEnvelope(
        success=True,
        message=f"User plan updated to {plan.value}",
        data=UserRead.model_validate(user)
    )
