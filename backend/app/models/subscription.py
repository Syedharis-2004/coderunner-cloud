"""
Subscription Model
==================
Tracks user subscriptions with Stripe integration.
Manages subscription lifecycle and billing periods.
"""
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses"""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"
    PAUSED = "paused"


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    # Relations
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # SafePay integration
    safepay_tracker  = Column(String(255), nullable=True, index=True)
    safepay_order_id = Column(String(255), nullable=True, index=True)
    
    # Status
    status = Column(SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE)
    
    # Billing period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Cancellation
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Trial
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    plan = relationship("Plan")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription provides active benefits"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    @property
    def is_past_due(self) -> bool:
        """Check if payment is past due"""
        return self.status == SubscriptionStatus.PAST_DUE
    
    @property
    def allows_api_access(self) -> bool:
        """Check if subscription allows production API key generation"""
        # Only ACTIVE and TRIALING subscriptions with paid plans get API access
        return self.is_active and self.plan_id is not None
