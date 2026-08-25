from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    language: str
    code: Optional[str] = ""
    stdin_data: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name cannot be empty.")
        return v.strip()

    @field_validator("language")
    @classmethod
    def language_format(cls, v: str) -> str:
        return v.lower().strip()


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    code: Optional[str] = None
    stdin_data: Optional[str] = None
    is_public: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Project name cannot be empty.")
            return v.strip()
        return v


class ProjectRead(BaseModel):
    id: str
    name: str
    description: Optional[str]
    language: str
    code: str
    stdin_data: Optional[str]
    is_public: bool
    public_share_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    """Lighter version for list views."""
    id: str
    name: str
    language: str
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
