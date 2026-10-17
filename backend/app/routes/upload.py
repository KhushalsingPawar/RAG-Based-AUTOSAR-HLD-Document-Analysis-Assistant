import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from backend.app.config import settings, UPLOAD_DIR, SAMPLE_HLD_DIR
from backend.app.database import get_db
from backend.app.models.schema import Project, Document, DocumentChunk, AutosarEntity, AuditLog, User
from backend.app.auth.dependencies import get_current_user
from backend.app.services.pdf_parser import pdf_parser
from backend.app.services.chunker import chunker
from backend.app.services.vector_store import vector_store
from backend.app.services.entity_extractor import entity_extractor

router = APIRouter(prefix="/upload", tags=["Document Ingestion"])


def _process_and_index_pdf(
    file_path: str,
    filename: str,
    version: str,
    project_id: int,
    user_id: int,
    db: Session,
) -> Document:
    # 1. Parse PDF
    parsed_data = pdf_parser.parse_pdf(file_path)

    # 2. Create Document record in DB tied to user_id
    doc_record = Document(
        project_id=project_id,
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        version=version,
        total_pages=parsed_data["total_pages"],
        file_size_kb=parsed_data["file_size_kb"],
        status="Processing",
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 3. Contextual Chunking
    chunks_data = chunker.chunk_document(parsed_data)

    # 4. Save Chunks to SQLite
    db_chunks = []
    for c in chunks_data:
        chunk_rec = DocumentChunk(
            document_id=doc_record.id,
            chunk_index=c["chunk_index"],
            page_number=c["page_number"],
            section_title=c["section_title"],
            content=c["content"],
            token_count=c["token_count"],
        )
        db_chunks.append(chunk_rec)
    db.add_all(db_chunks)

    # 5. Extract AUTOSAR Entities and save to SQLite
    extracted_entities = entity_extractor.extract_from_pages(parsed_data["pages"], doc_record.id)
    db_entities = []
    for ent in extracted_entities:
        db_entities.append(
            AutosarEntity(
                document_id=doc_record.id,
                entity_type=ent["entity_type"],
                name=ent["name"],
                port_type=ent["port_type"],
                interface_name=ent["interface_name"],
                data_type=ent["data_type"],
                parent_component=ent["parent_component"],
                source_page=ent["source_page"],
                section_title=ent["section_title"],
                description=ent["description"],
            )
        )
    db.add_all(db_entities)

    # 6. Index into ChromaDB with user_id metadata
    vector_store.add_chunks(
        chunks=chunks_data,
        document_id=doc_record.id,
        document_name=filename,
        project_id=project_id,
        version=version,
        user_id=user_id,
    )

    doc_record.status = "Indexed"

    audit = AuditLog(
        project_id=project_id,
        action="DOCUMENT_INGESTION",
        details=f"User ID {user_id} ingested {filename} (v{version}): {len(chunks_data)} chunks, {len(extracted_entities)} entities.",
    )
    db.add(audit)
    db.commit()
    db.refresh(doc_record)

    return doc_record


@router.post("", summary="Upload and Index an AUTOSAR HLD PDF for Current User")
async def upload_pdf(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    version: str = Form("1.0.0"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Specified project does not exist or access is denied.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    dest_path = UPLOAD_DIR / f"u{current_user.id}_p{project_id}_{file.filename}"
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = _process_and_index_pdf(
        file_path=str(dest_path),
        filename=file.filename,
        version=version,
        project_id=project_id,
        user_id=current_user.id,
        db=db,
    )

    return {
        "message": f"Successfully ingested and indexed {file.filename}",
        "document_id": doc.id,
        "filename": doc.filename,
        "version": doc.version,
        "total_pages": doc.total_pages,
        "status": doc.status,
    }


@router.post("/sample", summary="Load Pre-packaged Sample AUTOSAR HLD Document for Current User")
async def load_sample_hld(
    sample_name: str = Form("Brake_System_HLD_v2.1.pdf"),
    project_id: int = Form(...),
    version: str = Form("v2.1.0"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Specified project does not exist or access is denied.")

    sample_path = SAMPLE_HLD_DIR / sample_name
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample file {sample_name} not found.")

    dest_path = UPLOAD_DIR / f"u{current_user.id}_p{project_id}_{sample_name}"
    shutil.copy(sample_path, dest_path)

    doc = _process_and_index_pdf(
        file_path=str(dest_path),
        filename=sample_name,
        version=version,
        project_id=project_id,
        user_id=current_user.id,
        db=db,
    )

    return {
        "message": f"Sample {sample_name} successfully ingested and indexed.",
        "document_id": doc.id,
        "filename": doc.filename,
        "version": doc.version,
        "total_pages": doc.total_pages,
        "status": doc.status,
    }
