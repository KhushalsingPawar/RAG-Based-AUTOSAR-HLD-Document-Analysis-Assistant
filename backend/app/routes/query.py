from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.api_models import QueryRequest, QueryResponse
from backend.app.services.rag_engine import rag_engine
from backend.app.models.schema import AuditLog, Document, Project, User
from backend.app.auth.dependencies import get_current_user

router = APIRouter(prefix="/query", tags=["Semantic RAG Querying"])


@router.post("", response_model=QueryResponse, summary="Query the AUTOSAR HLD Knowledge Base for Current User")
def query_documents(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Determine documents accessible to this user
    doc_query = db.query(Document.id).filter(Document.user_id == current_user.id)
    if req.project_id:
        # Verify project belongs to current user
        proj = db.query(Project).filter(Project.id == req.project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or access denied.")
        doc_query = doc_query.filter(Document.project_id == req.project_id)

    allowed_doc_ids = [r[0] for r in doc_query.all()]

    if req.document_id and req.document_id not in allowed_doc_ids:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    result = rag_engine.query(
        question=req.question,
        project_id=req.project_id,
        document_id=req.document_id,
        allowed_document_ids=allowed_doc_ids,
        top_k=req.top_k,
    )

    if req.project_id:
        audit = AuditLog(
            project_id=req.project_id,
            action="RAG_QUERY",
            details=f"User '{current_user.username}' query: '{req.question[:60]}...' | Confidence: {result['grounding_confidence']}",
        )
        db.add(audit)
        db.commit()

    return result
