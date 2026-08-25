from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    @property
    def current_plan(self):
        """Get the user's current plan (via subscription or default to free)"""
        if self.subscription and self.subscription.is_active:
            return self.subscription.plan
        # Return None if no active subscription - frontend/backend will handle free tier
        return None
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has an active paid subscription"""
        return self.subscription is not None and self.subscription.is_active
