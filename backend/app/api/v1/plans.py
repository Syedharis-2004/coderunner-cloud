"""
Plans API Router
================
Public endpoints for listing available subscription plans.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.plan import Plan
from app.schemas.plan import PlanPublic, PlanRead, PlanCreate, PlanUpdate
from app.schemas.common import ResponseEnvelope
from app.api.deps import require_admin

router = APIRouter(prefix="/plans", tags=["Plans"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=ResponseEnvelope[List[PlanPublic]],
    summary="List all active public plans",
)
def list_plans(db: Session = Depends(get_db)):
    plans = (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.is_public == True)
        .order_by(Plan.sort_order)
        .all()
    )
    return ResponseEnvelope(success=True, message="Plans retrieved successfully", data=plans)


# NOTE: /key/{plan_key} MUST be registered before /{plan_id} to avoid shadowing
@router.get(
    "/key/{plan_key}",
    response_model=ResponseEnvelope[PlanPublic],
    summary="Get a plan by key (e.g., 'starter', 'pro')",
)
def get_plan_by_key(plan_key: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.key == plan_key, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_key}' not found")
    return ResponseEnvelope(success=True, message="Plan retrieved successfully", data=plan)


@router.get(
    "/{plan_id}",
    response_model=ResponseEnvelope[PlanPublic],
    summary="Get a specific plan by ID",
)
def get_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return ResponseEnvelope(success=True, message="Plan retrieved successfully", data=plan)


# ══════════════════════════════════════════════════════════════════════════════
# Admin Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/all",
    response_model=ResponseEnvelope[List[PlanRead]],
    summary="List all plans (admin only)",
    dependencies=[Depends(require_admin)],
)
def list_all_plans_admin(db: Session = Depends(get_db)):
    """Admin endpoint to list all plans including inactive ones"""
    plans = db.query(Plan).order_by(Plan.sort_order).all()
    
    return ResponseEnvelope(
        success=True,
        message=f"Retrieved {len(plans)} plans",
        data=plans,
    )


@router.post(
    "/admin/create",
    response_model=ResponseEnvelope[PlanRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new plan (admin only)",
    dependencies=[Depends(require_admin)],
)
def create_plan_admin(plan_data: PlanCreate, db: Session = Depends(get_db)):
    """Admin endpoint to create a new plan"""
    import uuid
    from datetime import datetime, timezone
    
    # Check if plan key already exists
    existing = db.query(Plan).filter(Plan.key == plan_data.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with key '{plan_data.key}' already exists"
        )
    
    plan = Plan(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        **plan_data.model_dump()
    )    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Admin created plan: {plan.key} ({plan.id})")
    
    return ResponseEnvelope(
        success=True,
        message="Plan created successfully",
        data=plan,
    )


@router.patch(
    "/admin/{plan_id}",
    response_model=ResponseEnvelope[PlanRead],
    summary="Update a plan (admin only)",
    dependencies=[Depends(require_admin)],
)
def update_plan_admin(
    plan_id: str,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db)
):
    """Admin endpoint to update a plan"""
    from datetime import datetime, timezone
    
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Update only provided fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Admin updated plan: {plan.key} ({plan.id})")
    
    return ResponseEnvelope(
        success=True,
        message="Plan updated successfully",
        data=plan,
    )
