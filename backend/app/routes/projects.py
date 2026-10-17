from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.schema import Project, User
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.api_models import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Project Management"])


@router.get("", response_model=List[ProjectResponse], summary="List All Engineering Projects for Current User")
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.asc()).all()
    if not projects:
        # Auto-seed a personal default project for this user (starts completely clean with 0 files)
        user_display = current_user.full_name or current_user.username
        default_proj = Project(
            name=f"{user_display}'s Workspace",
            vehicle_program="Tata Automotive Architecture",
            description=f"Personal AUTOSAR architecture analysis workspace for {user_display}.",
            user_id=current_user.id,
        )
        db.add(default_proj)
        db.commit()
        db.refresh(default_proj)
        return [default_proj]
    return projects


@router.post("", response_model=ProjectResponse, summary="Create a New Project for Current User")
def create_project(
    req: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Project).filter(Project.name == req.name, Project.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="A project with this name already exists in your workspace.")

    proj = Project(
        name=req.name,
        vehicle_program=req.vehicle_program,
        description=req.description,
        user_id=current_user.id,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj
