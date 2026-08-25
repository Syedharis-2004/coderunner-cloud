"""
Admin API Router
================
Endpoints strictly reserved for users with the ADMIN role.
Provides system-wide metrics, user management, subscription overview.
"""
import logging
from typing import List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.execution import Execution
from app.models.usage import UsageRecord
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.payment import Payment, PaymentStatus
from app.models.plan import Plan
from app.schemas.common import ResponseEnvelope
from app.schemas.user import UserRead
from app.api.deps import require_admin
from app.services.docker_engine import docker_engine
from app.services.usage_service import _current_period

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)

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

    # Execution metrics
    total_executions = db.query(func.count(Execution.id)).scalar() or 0

    # Usage metrics (current month)
    monthly_usage_records = db.query(UsageRecord).filter(UsageRecord.billing_period == period).all()
    monthly_executions = sum(r.total_executions for r in monthly_usage_records)
    monthly_compute_seconds = sum(r.total_compute_seconds for r in monthly_usage_records)

    # Subscription metrics
    active_subscriptions = db.query(func.count(Subscription.id)).filter(
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    ).scalar() or 0

    total_subscriptions = db.query(func.count(Subscription.id)).scalar() or 0

    # Revenue metrics (succeeded payments)
    monthly_revenue_result = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.SUCCEEDED,
        func.to_char(Payment.created_at, 'YYYY-MM') == period
    ).scalar()
    monthly_revenue = float(monthly_revenue_result or 0)

    total_revenue_result = db.query(func.sum(Payment.amount)).filter(
        Payment.status == PaymentStatus.SUCCEEDED
    ).scalar()
    total_revenue = float(total_revenue_result or 0)

    # Plan breakdown
    plan_breakdown = []
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    for plan in plans:
        count = db.query(func.count(Subscription.id)).filter(
            Subscription.plan_id == plan.id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
        ).scalar() or 0
        plan_breakdown.append({
            "plan": plan.name,
            "key": plan.key,
            "active_subscriptions": count,
            "mrr": float(plan.price_monthly) * count,
        })

    # API keys
    from app.models.api_key import APIKey
    total_api_keys = db.query(func.count(APIKey.id)).filter(APIKey.is_active == True).scalar() or 0

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
            "subscriptions": {
                "active": active_subscriptions,
                "total": total_subscriptions,
                "plan_breakdown": plan_breakdown,
            },
            "revenue": {
                "monthly": round(monthly_revenue, 2),
                "total": round(total_revenue, 2),
            },
            "api_keys": {
                "active": total_api_keys,
            },
            "system": {
                "docker": docker_status,
            },
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
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return ResponseEnvelope(
        success=True,
        data=[UserRead.model_validate(u) for u in users],
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
    db: Session = Depends(get_db),
):
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
        data=UserRead.model_validate(user),
    )


@router.get(
    "/subscriptions",
    response_model=ResponseEnvelope[List[dict]],
    dependencies=router_dependencies,
    summary="List all subscriptions",
)
def list_all_subscriptions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Admin view of all subscriptions with user and plan info."""
    subs = (
        db.query(Subscription)
        .order_by(Subscription.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for s in subs:
        result.append({
            "id": s.id,
            "user_id": s.user_id,
            "user_email": s.user.email if s.user else None,
            "plan_name": s.plan.name if s.plan else None,
            "plan_key": s.plan.key if s.plan else None,
            "status": s.status,
            "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
            "cancel_at_period_end": s.cancel_at_period_end,
            "created_at": s.created_at.isoformat(),
        })

    return ResponseEnvelope(
        success=True,
        message=f"Retrieved {len(result)} subscriptions",
        data=result,
    )


@router.get(
    "/payments",
    response_model=ResponseEnvelope[List[dict]],
    dependencies=router_dependencies,
    summary="List recent payments",
)
def list_recent_payments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .order_by(Payment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for p in payments:
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "user_email": p.user.email if p.user else None,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "payment_type": p.payment_type,
            "description": p.description,
            "receipt_url": p.receipt_url,
            "created_at": p.created_at.isoformat(),
        })

    return ResponseEnvelope(
        success=True,
        message=f"Retrieved {len(result)} payments",
        data=result,
    )
