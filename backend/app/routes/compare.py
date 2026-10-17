from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.schema import Document, User
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.api_models import CompareRequest, CompareResponse
from backend.app.services.diff_engine import diff_engine

router = APIRouter(prefix="/compare", tags=["Revision Comparison"])


@router.post("", response_model=CompareResponse, summary="Compare Two AUTOSAR HLD Document Revisions for Current User")
def compare_documents(
    req: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc_a = db.query(Document).filter(Document.id == req.doc_a_id, Document.user_id == current_user.id).first()
    doc_b = db.query(Document).filter(Document.id == req.doc_b_id, Document.user_id == current_user.id).first()
    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both document revisions not found or access is denied.")

    try:
        diff_report = diff_engine.compare_revisions(
            doc_a_id=req.doc_a_id,
            doc_b_id=req.doc_b_id,
            db=db,
        )
        return diff_report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
