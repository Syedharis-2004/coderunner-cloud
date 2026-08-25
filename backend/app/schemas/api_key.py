from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class APIKeyCreatedResponse(APIKeyResponse):
    """Returned ONLY ONCE upon creation. Contains the unhashed raw key."""
    raw_key: str
