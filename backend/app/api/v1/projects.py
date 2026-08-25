import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead, ProjectSummary
from app.schemas.common import ResponseEnvelope, PaginatedResponse
from app.api.deps import get_current_user
from app.services.language_registry import language_registry

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ResponseEnvelope[ProjectRead], status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new code project for the current user."""
    if not language_registry.is_supported(payload.language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{payload.language}' is not supported.",
        )

    project = Project(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        language=payload.language,
        code=payload.code or "",
        stdin_data=payload.stdin_data or "",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(f"Project created: {project.id} by user {current_user.id}")
    return ResponseEnvelope(
        success=True,
        message="Project created successfully",
        data=ProjectRead.model_validate(project),
    )


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[ProjectSummary]])
def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    language: Optional[str] = Query(None, description="Filter by language"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List projects owned by the current user."""
    query = db.query(Project).filter(Project.user_id == current_user.id)
    if language:
        query = query.filter(Project.language == language.lower().strip())

    total = query.count()
    projects = (
        query.order_by(desc(Project.updated_at))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    items = [ProjectSummary.model_validate(p) for p in projects]
    pages = (total + size - 1) // size if size > 0 else 1

    return ResponseEnvelope(
        success=True,
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        ),
    )


@router.get("/shared/{share_id}", response_model=ResponseEnvelope[ProjectRead])
def get_shared_project(share_id: str, db: Session = Depends(get_db)):
    """Retrieve a public project by its share ID (No auth required)."""
    project = (
        db.query(Project)
        .filter(Project.public_share_id == share_id, Project.is_public == True)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public project not found or access denied.",
        )

    return ResponseEnvelope(
        success=True,
        data=ProjectRead.model_validate(project),
    )


@router.get("/{project_id}", response_model=ResponseEnvelope[ProjectRead])
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific project owned by the current user."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ResponseEnvelope(
        success=True,
        data=ProjectRead.model_validate(project),
    )


@router.patch("/{project_id}", response_model=ResponseEnvelope[ProjectRead])
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing project."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.language is not None and not language_registry.is_supported(payload.language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{payload.language}' is not supported.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle public sharing logic
    if "is_public" in update_data:
        if update_data["is_public"] and not project.public_share_id:
            # Generate a new share ID when making public
            project.public_share_id = str(uuid.uuid4())
        elif not update_data["is_public"]:
            # Optional: Clear share ID when making private, or keep it so the link works if made public again
            # For strictness, we'll keep the ID but the query in `get_shared_project` enforces `is_public == True`
            pass

    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return ResponseEnvelope(
        success=True,
        message="Project updated successfully",
        data=ProjectRead.model_validate(project),
    )


@router.delete("/{project_id}", response_model=ResponseEnvelope[dict])
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return ResponseEnvelope(
        success=True,
        message="Project deleted successfully",
        data={"project_id": project_id},
    )
