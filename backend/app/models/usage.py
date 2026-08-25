from sqlalchemy import Column, String, ForeignKey, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class UsageRecord(Base, TimestampMixin):
    """Monthly usage aggregation per user (format: YYYY-MM)."""
    __tablename__ = "usage_records"
    __table_args__ = (
        UniqueConstraint("user_id", "billing_period", name="uq_usage_user_period"),
    )

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    billing_period = Column(String(7), nullable=False, index=True)  # "2025-08"

    total_executions = Column(Integer, default=0, nullable=False)
    successful_executions = Column(Integer, default=0, nullable=False)
    failed_executions = Column(Integer, default=0, nullable=False)
    api_executions = Column(Integer, default=0, nullable=False)
    total_compute_seconds = Column(Float, default=0.0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="usage_records")
