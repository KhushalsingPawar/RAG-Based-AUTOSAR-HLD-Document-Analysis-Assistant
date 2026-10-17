from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.schema import Document, User
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.api_models import ValidationResponse
from backend.app.services.validation_engine import validation_engine

router = APIRouter(prefix="/validate", tags=["Architectural Validation"])


@router.post("", response_model=ValidationResponse, summary="Run Architectural Consistency & Mismatch Checks for Current User")
def validate_hld(
    document_id: int = Query(..., description="Target Document ID to validate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access is denied.")

    try:
        report = validation_engine.validate_document(document_id=document_id, db=db)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
