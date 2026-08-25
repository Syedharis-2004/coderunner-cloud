from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Stored as prefix (e.g. "cr_live_AbCd...") for display purposes only
    key_prefix = Column(String(32), nullable=False)

    # HMAC-SHA256 hash of the full raw key — NEVER store the raw key
    key_hash = Column(String(128), unique=True, index=True, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    executions = relationship("Execution", back_populates="api_key")
