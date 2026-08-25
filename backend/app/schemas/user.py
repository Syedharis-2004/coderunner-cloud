from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


# Keep LoginRequest as an alias so any existing imports don't break
LoginRequest = UserLogin


class UserRead(BaseModel):
    """Public-safe user representation."""
    id: str
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Allowed fields for profile updates (name only — plan changes go through billing)."""
    name: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token + user profile returned after login/register."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead
