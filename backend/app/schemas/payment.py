"""
Payment Schemas
===============
Request/response schemas for SafePay payment transactions.
"""
from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    """Request to create a SafePay checkout session."""
    plan_id:     str           = Field(..., description="ID of the plan to subscribe to")
    success_url: Optional[str] = Field(None, description="URL to redirect on success")
    cancel_url:  Optional[str] = Field(None, description="URL to redirect on cancel")


class CheckoutSessionResponse(BaseModel):
    """Response containing SafePay checkout URL and tracker token."""
    checkout_url: str
    session_id:   str   # SafePay beacon/tracker token


class PaymentRead(BaseModel):
    """Schema for reading payment data."""
    id:               str
    user_id:          str
    subscription_id:  Optional[str]
    safepay_tracker:  Optional[str]
    safepay_order_id: Optional[str]
    amount:           Decimal
    currency:         str
    status:           str
    payment_type:     str
    description:      Optional[str]
    failure_reason:   Optional[str]
    receipt_url:      Optional[str]
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}
