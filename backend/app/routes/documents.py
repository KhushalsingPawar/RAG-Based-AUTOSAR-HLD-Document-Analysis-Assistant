import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.schema import Document, DocumentChunk, AuditLog, User
from backend.app.auth.dependencies import get_current_user
from backend.app.schemas.api_models import DocumentResponse, DocumentChunkResponse
from backend.app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Document Management"])


@router.get("", response_model=List[DocumentResponse], summary="List Documents for Current User")
def list_documents(
    project_id: Optional[int] = Query(None, description="Filter by Project ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    return query.order_by(Document.uploaded_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get Document Details")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")
    return doc


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse], summary="Inspect Document Chunks")
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc()).all()
    return chunks


@router.delete("/{document_id}", summary="Delete Document, Physical File, and Associated Vectors")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied.")

    doc_filename = doc.filename
    project_id = doc.project_id
    file_path = doc.file_path

    # 1. Remove vector embeddings from ChromaDB
    try:
        vector_store.delete_document_chunks(document_id)
    except Exception as e:
        print(f"Warning: Failed to delete vector chunks for doc {document_id}: {e}")

    # 2. Remove physical file from disk if present
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Warning: Failed to delete physical file {file_path}: {e}")

    # 3. Log audit event
    audit = AuditLog(
        project_id=project_id,
        action="DOCUMENT_DELETED",
        details=f"User '{current_user.username}' deleted document '{doc_filename}' (ID: {document_id}).",
    )
    db.add(audit)

    # 4. Remove from SQLite (cascade deletes chunks and entities)
    db.delete(doc)
    db.commit()

    return {
        "message": f"Document '{doc_filename}' and all associated indexed data deleted successfully.",
        "deleted_id": document_id,
    }
