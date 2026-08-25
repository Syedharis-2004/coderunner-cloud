import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserRead, TokenResponse, UserUpdate
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=ResponseEnvelope[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new Code Cloud account. Returns a JWT token on success."""
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user = User(
        email=payload.email.lower().strip(),
        name=payload.name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.email} (id={user.id})")
    token = create_access_token(user.id)

    return ResponseEnvelope(
        success=True,
        message="Account created successfully.",
        data=TokenResponse(access_token=token, user=UserRead.model_validate(user)),
    )


@router.post(
    "/login",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Login with email and password",
)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT access token."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact support.",
        )

    token = create_access_token(user.id)
    logger.info(f"User logged in: {user.email}")

    return ResponseEnvelope(
        success=True,
        message="Login successful.",
        data=TokenResponse(access_token=token, user=UserRead.model_validate(user)),
    )


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserRead],
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return ResponseEnvelope(success=True, data=UserRead.model_validate(current_user))


@router.patch(
    "/me",
    response_model=ResponseEnvelope[UserRead],
    summary="Update current user profile",
)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update allowed profile fields (name only)."""
    if payload.name is not None:
        current_user.name = payload.name.strip()

    db.commit()
    db.refresh(current_user)

    return ResponseEnvelope(
        success=True,
        message="Profile updated.",
        data=UserRead.model_validate(current_user),
    )
