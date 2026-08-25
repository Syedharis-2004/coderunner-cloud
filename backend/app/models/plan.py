"""
Plan Model
==========
Configurable subscription plans with pricing and limits.
Allows dynamic plan management without code changes.
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text
from app.core.database import Base
from app.models.base import TimestampMixin


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    # Plan identification
    key = Column(String(50), unique=True, index=True, nullable=False)  # e.g. "free", "starter", "pro"
    name = Column(String(100), nullable=False)  # Display name
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Numeric(10, 2), nullable=False, default=0)  # USD
    
    # Limits
    monthly_executions = Column(Integer, nullable=False, default=100)
    max_api_keys = Column(Integer, nullable=False, default=0)
    timeout_seconds = Column(Integer, nullable=False, default=10)
    memory_limit_mb = Column(Integer, nullable=False, default=128)
    rate_limit_per_minute = Column(Integer, nullable=False, default=20)
    
    # Features
    api_access_enabled = Column(Boolean, nullable=False, default=False)  # Production API access
    priority_execution = Column(Boolean, nullable=False, default=False)
    support_level = Column(String(50), nullable=False, default="community")  # community, email, priority
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_public = Column(Boolean, nullable=False, default=True)  # Show on pricing page
    sort_order = Column(Integer, nullable=False, default=0)  # Display order on pricing page
