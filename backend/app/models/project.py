from sqlalchemy import Column, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(50), nullable=False, default="python")
    code = Column(Text, nullable=False, default="")
    stdin_data = Column(Text, nullable=True, default="")
    is_public = Column(Boolean, default=False, nullable=False)
    public_share_id = Column(String(36), nullable=True, unique=True, index=True)

    # Relationships
    user = relationship("User", back_populates="projects")
    executions = relationship("Execution", back_populates="project", cascade="all, delete-orphan")
