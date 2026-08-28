"""
Subscriptions API Router
=========================
Manage user subscriptions and subscription status.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionWithPlan,
    SubscriptionStatus,
    CancelSubscriptionRequest,
)
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
logger = logging.getLogger(__name__)


@router.get(
    "/current",
    response_model=ResponseEnvelope[Optional[SubscriptionWithPlan]],
    summary="Get current user's subscription",
)
def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = subscription_service.get_user_subscription(db, current_user.id)
    if not subscription:
        return ResponseEnvelope(success=True, message="No active subscription (free tier)", data=None)
    return ResponseEnvelope(
        success=True,
        message="Subscription retrieved successfully",
        data=SubscriptionWithPlan.from_orm_safe(subscription),
    )


@router.get(
    "/status",
    response_model=ResponseEnvelope[SubscriptionStatus],
    summary="Get subscription status summary",
)
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = subscription_service.get_user_subscription(db, current_user.id)

    if not subscription:
        return ResponseEnvelope(
            success=True,
            message="Free tier user",
            data=SubscriptionStatus(
                has_subscription=False,
                is_active=False,
                plan_name="Free",
                plan_key="free",
                status=None,
                current_period_end=None,
                cancel_at_period_end=False,
                allows_api_access=False,
            ),
        )

    plan = subscription.plan
    return ResponseEnvelope(
        success=True,
        message="Subscription status retrieved",
        data=SubscriptionStatus(
            has_subscription=True,
            is_active=subscription.is_active,
            plan_name=plan.name,
            plan_key=plan.key,
            status=subscription.status.value,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            allows_api_access=subscription.allows_api_access,
        ),
    )


@router.post(
    "/cancel",
    response_model=ResponseEnvelope[dict],
    summary="Cancel subscription",
)
def cancel_subscription(
    cancel_request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success, message = subscription_service.cancel_subscription(
        db,
        current_user.id,
        cancel_at_period_end=cancel_request.cancel_at_period_end,
        reason=cancel_request.reason,
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    logger.info(f"User {current_user.id} canceled subscription")
    return ResponseEnvelope(
        success=True,
        message=message,
        data={"canceled_at_period_end": cancel_request.cancel_at_period_end},
    )


@router.post(
    "/reactivate",
    response_model=ResponseEnvelope[dict],
    summary="Reactivate a canceled subscription",
)
def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Undo cancel_at_period_end — keep subscription active (SafePay version)."""
    subscription = subscription_service.get_user_subscription(db, current_user.id)

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found")

    if not subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not scheduled for cancellation",
        )

    subscription.cancel_at_period_end = False
    subscription.canceled_at = None
    subscription.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"User {current_user.id} reactivated subscription")
    return ResponseEnvelope(success=True, message="Subscription reactivated successfully", data={"reactivated": True})
