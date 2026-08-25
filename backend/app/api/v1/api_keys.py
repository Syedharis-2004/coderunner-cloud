import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import generate_api_key
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ResponseEnvelope[APIKeyCreatedResponse], status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a new API Key for programmatic REST API access.
    The raw key is returned exactly once and is never stored in plain text.
    
    IMPORTANT: Requires an active paid subscription.
    """
    from app.services.subscription_service import subscription_service
    
    # Check if user can generate API key (subscription check)
    can_create, reason = subscription_service.can_generate_api_key(db, current_user)
    
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )
    
    # Get user's plan to check max API keys limit
    plan = subscription_service.get_user_plan(db, current_user)
    
    # Count active keys
    active_keys_count = db.query(APIKey).filter(
        APIKey.user_id == current_user.id, 
        APIKey.is_active == True
    ).count()

    if active_keys_count >= plan.max_api_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key limit reached ({plan.max_api_keys} keys for {plan.name} plan). Revoke an existing key or upgrade your plan.",
        )

    raw_key, key_prefix, key_hash = generate_api_key()

    api_key_record = APIKey(
        user_id=current_user.id,
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)

    logger.info(f"API key '{payload.name}' generated for user {current_user.id} (plan: {plan.key})")

    return ResponseEnvelope(
        success=True,
        message="API Key created. Please save the raw_key now; it will never be shown again.",
        data=APIKeyCreatedResponse(
            id=api_key_record.id,
            name=api_key_record.name,
            key_prefix=api_key_record.key_prefix,
            is_active=api_key_record.is_active,
            last_used_at=api_key_record.last_used_at,
            revoked_at=api_key_record.revoked_at,
            created_at=api_key_record.created_at,
            raw_key=raw_key,
        ),
    )


@router.get("", response_model=ResponseEnvelope[List[APIKeyResponse]])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all API keys owned by the user (both active and revoked)."""
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc()).all()
    
    return ResponseEnvelope(
        success=True,
        data=[APIKeyResponse.model_validate(k) for k in keys]
    )


@router.delete("/{key_id}", response_model=ResponseEnvelope[dict])
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke an API key. 
    It is kept in the database for audit/history, but marked inactive.
    """
    key = db.query(APIKey).filter(
        APIKey.id == key_id, 
        APIKey.user_id == current_user.id
    ).first()

    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found.")

    if not key.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API Key is already revoked.")

    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"API key {key_id} revoked by user {current_user.id}")

    return ResponseEnvelope(
        success=True,
        message="API Key has been successfully revoked.",
        data={"key_id": key_id, "status": "revoked"}
    )
