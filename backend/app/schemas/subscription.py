"""
Subscription Schemas
====================
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.plan import PlanPublic


class SubscriptionCreate(BaseModel):
    user_id: str
    plan_id: str
    safepay_tracker: Optional[str] = None
    safepay_order_id: Optional[str] = None
    status: str = "incomplete"


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    status: Optional[str] = None
    safepay_tracker: Optional[str] = None
    safepay_order_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None


class SubscriptionRead(BaseModel):
    """Schema for reading subscription data."""
    id: str
    user_id: str
    plan_id: str
    status: str
    safepay_tracker: Optional[str] = None
    safepay_order_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = False
    allows_api_access: bool = False

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_safe(cls, obj) -> "SubscriptionRead":
        """Safe ORM conversion that reads computed properties explicitly."""
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            plan_id=obj.plan_id,
            status=obj.status.value if hasattr(obj.status, "value") else str(obj.status),
            safepay_tracker=getattr(obj, "safepay_tracker", None),
            safepay_order_id=getattr(obj, "safepay_order_id", None),
            current_period_start=obj.current_period_start,
            current_period_end=obj.current_period_end,
            cancel_at_period_end=obj.cancel_at_period_end,
            canceled_at=obj.canceled_at,
            ended_at=obj.ended_at,
            trial_start=obj.trial_start,
            trial_end=obj.trial_end,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            is_active=obj.is_active,
            allows_api_access=obj.allows_api_access,
        )


class SubscriptionWithPlan(SubscriptionRead):
    """Subscription with full plan details embedded."""
    plan: Optional[PlanPublic] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_safe(cls, obj) -> "SubscriptionWithPlan":
        base = SubscriptionRead.from_orm_safe(obj)
        return cls(
            **base.model_dump(),
            plan=PlanPublic.model_validate(obj.plan) if obj.plan else None,
        )


class SubscriptionStatus(BaseModel):
    """Simple subscription status for dashboard display."""
    has_subscription: bool
    is_active: bool
    plan_name: Optional[str] = None
    plan_key: Optional[str] = None
    status: Optional[str] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    allows_api_access: bool = False


class CancelSubscriptionRequest(BaseModel):
    cancel_at_period_end: bool = True
    reason: Optional[str] = Field(None, max_length=500)
