from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from app.models.execution import ExecutionStatus


class CodeExecutionRequest(BaseModel):
    """Request body for submitting code for execution."""
    language: str
    code: str
    stdin: Optional[str] = ""
    project_id: Optional[str] = None
    timeout_seconds: Optional[int] = None

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Code cannot be empty.")
        return v


class ExecutionResult(BaseModel):
    """Full execution result returned to the client."""
    execution_id: str
    status: ExecutionStatus
    language: str
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    memory_used_bytes: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExecutionQueueResponse(BaseModel):
    """Lightweight response when an execution is queued asynchronously."""
    execution_id: str
    status: ExecutionStatus
    message: str = "Execution queued."


class ExecutionSummary(BaseModel):
    """Summary row used in list/history views."""
    execution_id: str
    language: str
    status: ExecutionStatus
    execution_time: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
