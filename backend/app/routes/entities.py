from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.schema import AutosarEntity, Document, User
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.api_models import AutosarEntityResponse

router = APIRouter(prefix="/entities", tags=["AUTOSAR Architecture Entities"])


@router.get("", response_model=List[AutosarEntityResponse], summary="List Extracted AUTOSAR Entities for Current User")
def get_entities(
    document_id: Optional[int] = Query(None, description="Filter by Document ID"),
    project_id: Optional[int] = Query(None, description="Filter by Project ID"),
    entity_type: Optional[str] = Query(None, description="Filter by Component, Port, Interface, Signal"),
    search: Optional[str] = Query(None, description="Search by entity name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AutosarEntity).join(Document).filter(Document.user_id == current_user.id)

    if document_id:
        query = query.filter(AutosarEntity.document_id == document_id)
    elif project_id:
        query = query.filter(Document.project_id == project_id)

    if entity_type:
        query = query.filter(AutosarEntity.entity_type == entity_type)

    if search:
        query = query.filter(AutosarEntity.name.ilike(f"%{search}%"))

    return query.all()
