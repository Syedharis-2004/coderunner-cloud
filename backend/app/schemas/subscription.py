"""
Subscription Schemas
====================
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.schemas.plan import PlanPublic


class SubscriptionCreate(BaseModel):
    user_id: str
    plan_id: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
    status: str = "incomplete"


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    status: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_price_id: Optional[str] = None
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
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed from ORM properties
    is_active: bool = False
    allows_api_access: bool = False

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_computed(cls, data):
        """Populate is_active and allows_api_access from ORM object properties."""
        if hasattr(data, "is_active"):
            # It's an ORM object — pull computed properties explicitly
            values = {
                "is_active": data.is_active,
                "allows_api_access": data.allows_api_access,
            }
            # Convert to dict for further processing
            return values | {
                col: getattr(data, col)
                for col in [
                    "id", "user_id", "plan_id", "status",
                    "stripe_customer_id", "stripe_subscription_id",
                    "current_period_start", "current_period_end",
                    "cancel_at_period_end", "canceled_at", "ended_at",
                    "trial_start", "trial_end", "created_at", "updated_at",
                ]
            }
        return data


class SubscriptionWithPlan(SubscriptionRead):
    """Subscription with full plan details embedded."""
    plan: Optional[PlanPublic] = None

    model_config = {"from_attributes": True}


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
