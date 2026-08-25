"""
Payment Model
=============
Payment transaction history for auditing and accounting (SafePay).
"""
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class PaymentStatus(str, Enum):
    PENDING   = "pending"
    SUCCEEDED = "succeeded"
    FAILED    = "failed"
    REFUNDED  = "refunded"
    CANCELED  = "canceled"


class PaymentType(str, Enum):
    SUBSCRIPTION = "subscription"
    UPGRADE      = "upgrade"
    DOWNGRADE    = "downgrade"
    REFUND       = "refund"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    # Relations
    user_id         = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),      nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    # SafePay identifiers
    safepay_tracker  = Column(String(255), nullable=True, index=True, unique=True)
    safepay_order_id = Column(String(255), nullable=True, index=True)

    # Payment details
    amount       = Column(Numeric(10, 2), nullable=False)
    currency     = Column(String(3),      nullable=False, default="USD")
    status       = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_type = Column(SQLEnum(PaymentType),   nullable=False, default=PaymentType.SUBSCRIPTION)

    # Metadata
    description    = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    receipt_url    = Column(Text, nullable=True)

    # Relationships
    user         = relationship("User")
    subscription = relationship("Subscription", back_populates="payments")
