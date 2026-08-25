import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user
from app.services.usage_service import usage_service

router = APIRouter(prefix="/usage", tags=["Usage"])
logger = logging.getLogger(__name__)


@router.get("/current", response_model=ResponseEnvelope[dict])
def get_current_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current month usage statistics for the dashboard.
    Includes execution counts, compute seconds, and plan limits.
    """
    stats = usage_service.get_current_usage(db, current_user)
    return ResponseEnvelope(success=True, data=stats)
