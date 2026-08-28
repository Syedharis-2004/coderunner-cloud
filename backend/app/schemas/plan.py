"""
Plan Schemas
============
Request/response schemas for subscription plans.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PlanBase(BaseModel):
    """Base plan fields"""
    key: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_monthly: float = Field(..., ge=0)
    monthly_executions: int = Field(..., ge=0)
    max_api_keys: int = Field(..., ge=0)
    timeout_seconds: int = Field(..., ge=1)
    memory_limit_mb: int = Field(..., ge=64)
    rate_limit_per_minute: int = Field(..., ge=1)
    api_access_enabled: bool = False
    priority_execution: bool = False
    support_level: str = Field(default="community")


class PlanCreate(PlanBase):
    """Schema for creating a new plan (admin only)"""
    is_active: bool = True
    is_public: bool = True
    sort_order: int = 0


class PlanUpdate(BaseModel):
    """Schema for updating a plan (admin only)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price_monthly: Optional[float] = Field(None, ge=0)
    monthly_executions: Optional[int] = Field(None, ge=0)
    max_api_keys: Optional[int] = Field(None, ge=0)
    timeout_seconds: Optional[int] = Field(None, ge=1)
    memory_limit_mb: Optional[int] = Field(None, ge=64)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    api_access_enabled: Optional[bool] = None
    priority_execution: Optional[bool] = None
    support_level: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanRead(PlanBase):
    """Schema for reading plan data"""
    id: str
    is_active: bool
    is_public: bool
    sort_order: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanPublic(BaseModel):
    """Public plan info for pricing page (no Stripe IDs exposed)"""
    id: str
    key: str
    name: str
    description: Optional[str]
    price_monthly: float
    monthly_executions: int
    max_api_keys: int
    timeout_seconds: int
    api_access_enabled: bool
    priority_execution: bool
    support_level: str

    model_config = {"from_attributes": True}
