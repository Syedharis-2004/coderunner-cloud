import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

import bcrypt

# ── Password hashing ───────────────────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")


# ── JWT tokens ─────────────────────────────────────────────────────────────────
def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token for a user (subject = user ID)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT token.
    Returns the user ID (sub claim) or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── API Key generation & hashing ───────────────────────────────────────────────
def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a cryptographically secure API key.

    Returns:
        (raw_key, key_prefix, key_hash)
        - raw_key:    Full key shown ONCE to the user (e.g. cr_live_9f83b1...)
        - key_prefix: Short display label for the UI (e.g. cr_live_9f83...)
        - key_hash:   SHA-256 hash stored in the database — NEVER the raw key
    """
    random_part = secrets.token_hex(32)          # 64 hex chars = 256 bits entropy
    raw_key = f"cr_live_{random_part}"
    key_prefix = raw_key[:16] + "..."            # e.g. "cr_live_9f83b1..."
    key_hash = hashlib.sha256(
        (raw_key + settings.API_KEY_SECRET).encode("utf-8")
    ).hexdigest()
    return raw_key, key_prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    """Hash an incoming raw API key for secure database lookup."""
    return hashlib.sha256(
        (raw_key + settings.API_KEY_SECRET).encode("utf-8")
    ).hexdigest()
