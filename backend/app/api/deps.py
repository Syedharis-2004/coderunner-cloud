from typing import Optional, Tuple
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, hash_api_key
from app.models.user import User
from app.models.api_key import APIKey

# ── Security schemes ───────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ── JWT dependency ─────────────────────────────────────────────────────────────
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency — validates JWT Bearer token and returns the authenticated user.
    Use this on any endpoint that requires a logged-in browser user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer JWT token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    return user


# ── Dual auth dependency (JWT or API key) ─────────────────────────────────────
def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    raw_api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> Tuple[User, Optional[APIKey]]:
    """
    FastAPI dependency — accepts either:
      - Authorization: Bearer <jwt>  (browser dashboard)
      - X-API-Key: cr_live_xxx       (developer REST API)

    Returns: (User, APIKey | None)
    The API key object is returned so callers can track usage by key.
    """
    # 1. Try API Key first
    if raw_api_key:
        key_hash = hash_api_key(raw_api_key.strip())
        api_key = (
            db.query(APIKey)
            .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
            .first()
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API key.",
            )

        # Touch last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        db.commit()

        user = db.query(User).filter(User.id == api_key.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with this API key is inactive.",
            )
        return user, api_key

    # 2. Try JWT Bearer
    if credentials:
        user = get_current_user(credentials, db)
        return user, None

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a Bearer JWT token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Admin-only dependency ──────────────────────────────────────────────────────
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that ensures the caller has the ADMIN role."""
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user
