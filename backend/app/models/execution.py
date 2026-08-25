from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Text, Float, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    MEMORY_LIMIT = "MEMORY_LIMIT"
    CPU_LIMIT = "CPU_LIMIT"
    CANCELLED = "CANCELLED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class ExecutionSource(str, Enum):
    WEB_EDITOR = "WEB_EDITOR"
    REST_API = "REST_API"


class Execution(Base, TimestampMixin):
    __tablename__ = "executions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    api_key_id = Column(String(36), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)

    language = Column(String(50), nullable=False, index=True)
    code = Column(Text, nullable=False)
    stdin_data = Column(Text, nullable=True, default="")

    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.QUEUED, nullable=False, index=True)
    source = Column(SQLEnum(ExecutionSource), default=ExecutionSource.WEB_EDITOR, nullable=False)

    stdout = Column(Text, nullable=True, default="")
    stderr = Column(Text, nullable=True, default="")
    exit_code = Column(Integer, nullable=True)
    execution_time = Column(Float, nullable=True)       # seconds
    memory_used_bytes = Column(Integer, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="executions")
    project = relationship("Project", back_populates="executions")
    api_key = relationship("APIKey", back_populates="executions")
