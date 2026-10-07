import os
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from pydantic import BaseModel

from app.services.pdf_service import (
    extract_pdf_text
)

from app.services.structure_service import (
    extract_tables_from_pdf,
    process_document_pages
)

from app.services.entity_service import (
    extract_autosar_entities
)

from app.services.chunk_service import (
    create_document_chunks
)

from app.services.embedding_service import (
    generate_document_embeddings
)

from app.services.vector_service import (
    store_embeddings,
    get_collection_info
)

from app.services.retrieval_service import (
    retrieve_relevant_chunks
)

from app.services.rag_service import (
    ask_rag_question
)

from app.services.comparison_service import (
    compare_documents
)

from app.services.validation_service import (
    validate_document
)


# ============================================================
# IN-MEMORY DOCUMENT STORE
# ============================================================

DOCUMENT_STORE = {}


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    document_id: str | None = None


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: str | None = None


class CompareRequest(BaseModel):
    old_document_id: str
    new_document_id: str


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = "uploads"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# HELPER
# ============================================================

def get_stored_document(document_id: str):

    document = DOCUMENT_STORE.get(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return document


# ============================================================
# VECTOR DATABASE STATUS
# ============================================================

@router.get("/vector-db")
async def vector_db_status():

    return get_collection_info()


# ============================================================
# UPLOAD + ANALYZE HLD
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    # ========================================================
    # 1. FILE VALIDATION
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )


    # ========================================================
    # 2. DOCUMENT ID
    # ========================================================

    document_id = str(
        uuid.uuid4()
    )


    safe_filename = (
        f"{document_id}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        safe_filename
    )


    # ========================================================
    # 3. SAVE PDF
    # ========================================================

    try:

        contents = await file.read()

        with open(
            file_path,
            "wb"
        ) as output_file:

            output_file.write(
                contents
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save PDF: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # 4. MODULE 1
    # PDF TEXT EXTRACTION
    # ========================================================

    try:

        pages = extract_pdf_text(
            file_path
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF text extraction failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # 5. MODULE 2
    # STRUCTURE EXTRACTION
    # ========================================================

    try:

        tables = extract_tables_from_pdf(
            file_path
        )

    except Exception as error:

        print(
            f"Table extraction warning: {error}"
        )

        tables = []


    structured_pages = process_document_pages(
        pages,
        tables
    )


    # ========================================================
    # 6. MODULE 3
    # AUTOSAR ENTITY EXTRACTION
    # ========================================================

    try:

        entities = extract_autosar_entities(
            structured_pages
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "AUTOSAR entity extraction failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # 7. MODULE 4
    # CHUNKING + METADATA
    # ========================================================

    try:

        chunks = create_document_chunks(

            document_id=document_id,

            filename=file.filename,

            structured_pages=structured_pages,

            entities=entities

        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document chunking failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # CHUNK STATISTICS
    # ========================================================

    section_chunk_count = len(
        chunks.get(
            "section_chunks",
            []
        )
    )

    entity_chunk_count = len(
        chunks.get(
            "entity_chunks",
            []
        )
    )

    total_chunk_count = (
        section_chunk_count
        + entity_chunk_count
    )

    print(
        "========== CHUNK ANALYSIS =========="
    )

    print(
        "Section chunks:",
        section_chunk_count
    )

    print(
        "Entity chunks:",
        entity_chunk_count
    )

    print(
        "Total chunks:",
        total_chunk_count
    )

    print(
        "===================================="
    )


    # ========================================================
    # 8. MODULE 5
    # EMBEDDINGS
    # ========================================================

    try:

        embeddings = generate_document_embeddings(

            section_chunks=chunks[
                "section_chunks"
            ],

            entity_chunks=chunks[
                "entity_chunks"
            ]

        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Embedding generation failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # EMBEDDING STATISTICS
    # ========================================================

    embedding_chunk_count = embeddings.get(
        "total_chunks",
        0
    )

    embedding_model = embeddings.get(
        "embedding_model",
        ""
    )

    embedding_dimension = embeddings.get(
        "embedding_dimension",
        0
    )


    print(
        "===== EMBEDDING ANALYSIS ====="
    )

    print(
        "Embedding chunks:",
        embedding_chunk_count
    )

    print(
        "Embedding model:",
        embedding_model
    )

    print(
        "Embedding dimension:",
        embedding_dimension
    )

    print(
        "=============================="
    )


    # ========================================================
    # 9. MODULE 6
    # VECTOR DATABASE
    # ========================================================

    all_embedded_chunks = (
        embeddings["section_chunks"]
        + embeddings["entity_chunks"]
    )


    try:

        vector_store = store_embeddings(
            all_embedded_chunks
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Vector database storage failed: "
                f"{str(error)}"
            )
        )


    # ========================================================
    # 10. SAVE COMPLETE DOCUMENT INFORMATION
    # ========================================================

    DOCUMENT_STORE[document_id] = {

        "document_id": document_id,

        "filename": file.filename,

        "document_type": "AUTOSAR HLD",

        "total_pages": len(pages),

        "structured_pages": structured_pages,

        "entities": entities,

        # -----------------------------
        # CHUNK INFORMATION
        # -----------------------------

        "chunks": {

            "section_chunks": chunks[
                "section_chunks"
            ],

            "entity_chunks": chunks[
                "entity_chunks"
            ],

            "total_chunks": total_chunk_count
        },

        # -----------------------------
        # EMBEDDING INFORMATION
        # -----------------------------

        "embeddings": {

            "total_chunks": embedding_chunk_count,

            "embedding_model": embedding_model,

            "embedding_dimension": embedding_dimension
        },

        # -----------------------------
        # VECTOR STORE
        # -----------------------------

        "vector_store": vector_store
    }


    # ========================================================
    # 11. FINAL RESPONSE
    # ========================================================

    return {

        "document_id": document_id,

        "filename": file.filename,

        "document_type": "AUTOSAR HLD",

        "total_pages": len(pages),

        # -----------------------------
        # STRUCTURED DATA
        # -----------------------------

        "pages": structured_pages,

        # -----------------------------
        # ENTITIES
        # -----------------------------

        "entities": entities,

        # -----------------------------
        # CHUNKS
        # -----------------------------

        "chunks": {

            "section_chunks": chunks[
                "section_chunks"
            ],

            "entity_chunks": chunks[
                "entity_chunks"
            ],

            "total_chunks": total_chunk_count
        },

        # -----------------------------
        # EMBEDDINGS
        # -----------------------------

        "embeddings": {

            "total_chunks": embedding_chunk_count,

            "embedding_model": embedding_model,

            "embedding_dimension": embedding_dimension
        },

        # -----------------------------
        # VECTOR STORE
        # -----------------------------

        "vector_store": vector_store
    }


# ============================================================
# RETRIEVE DOCUMENT CHUNKS
# ============================================================

@router.post("/retrieve")
async def retrieve_documents(
    request: RetrievalRequest
):

    if not request.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty."
        )

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1."
        )

    if request.top_k > 20:

        raise HTTPException(
            status_code=400,
            detail="top_k cannot exceed 20."
        )


    chunks = retrieve_relevant_chunks(

        query=request.query,

        top_k=request.top_k,

        document_id=request.document_id

    )


    return {

        "query": request.query,

        "top_k": request.top_k,

        "results_count": len(chunks),

        "results": chunks

    }


# ============================================================
# RAG QUESTION ANSWERING
# ============================================================

@router.post("/ask")
async def ask_question(
    request: AskRequest
):

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1."
        )

    if request.top_k > 10:

        raise HTTPException(
            status_code=400,
            detail="top_k cannot exceed 10."
        )


    try:

        result = ask_rag_question(

            question=request.question,

            top_k=request.top_k,

            document_id=request.document_id

        )


        return {

            "question": request.question,

            "answer": result["answer"],

            "citations": result["citations"],

            "sources": result["sources"]

        }


    except RuntimeError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "RAG processing failed: "
                f"{str(error)}"
            )
        )


# ============================================================
# COMPONENTS
# ============================================================

@router.get("/components")
async def get_components(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    components = document[
        "entities"
    ].get(
        "software_components",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(components),

        "components": components

    }


# ============================================================
# INTERFACES
# ============================================================

@router.get("/interfaces")
async def get_interfaces(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    interfaces = document[
        "entities"
    ].get(
        "interfaces",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(interfaces),

        "interfaces": interfaces

    }


# ============================================================
# PORTS
# ============================================================

@router.get("/ports")
async def get_ports(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    ports = document[
        "entities"
    ].get(
        "ports",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(ports),

        "ports": ports

    }


# ============================================================
# SIGNALS
# ============================================================

@router.get("/signals")
async def get_signals(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    signals = document[
        "entities"
    ].get(
        "signals",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(signals),

        "signals": signals

    }


# ============================================================
# DEPENDENCIES
# ============================================================

@router.get("/dependencies")
async def get_dependencies(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    dependencies = document[
        "entities"
    ].get(
        "dependencies",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(dependencies),

        "dependencies": dependencies

    }


# ============================================================
# FUNCTIONAL FLOWS
# ============================================================

@router.get("/functional-flows")
async def get_functional_flows(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    flows = document[
        "entities"
    ].get(
        "functional_flows",
        []
    )

    return {

        "document_id": document_id,

        "filename": document["filename"],

        "count": len(flows),

        "functional_flows": flows

    }


# ============================================================
# ARCHITECTURE REPORT
# ============================================================

@router.get("/report")
async def get_architecture_report(
    document_id: str
):

    document = get_stored_document(
        document_id
    )

    entities = document[
        "entities"
    ]


    return {

        "document_id": document_id,

        "filename": document[
            "filename"
        ],

        "total_pages": document[
            "total_pages"
        ],

        # -----------------------------
        # PROCESSING INFORMATION
        # -----------------------------

        "processing": {

            "total_chunks": document[
                "chunks"
            ].get(
                "total_chunks",
                0
            ),

            "embedding_model": document[
                "embeddings"
            ].get(
                "embedding_model",
                ""
            ),

            "embedding_dimension": document[
                "embeddings"
            ].get(
                "embedding_dimension",
                0
            )
        },

        # -----------------------------
        # ENTITY SUMMARY
        # -----------------------------

        "summary": {

            "software_components": len(
                entities.get(
                    "software_components",
                    []
                )
            ),

            "interfaces": len(
                entities.get(
                    "interfaces",
                    []
                )
            ),

            "ports": len(
                entities.get(
                    "ports",
                    []
                )
            ),

            "signals": len(
                entities.get(
                    "signals",
                    []
                )
            ),

            "dependencies": len(
                entities.get(
                    "dependencies",
                    []
                )
            ),

            "functional_flows": len(
                entities.get(
                    "functional_flows",
                    []
                )
            )
        },

        "entities": entities
    }


# ============================================================
# COMPARE HLD VERSIONS
# ============================================================

@router.post("/compare")
async def compare_hld_documents(
    request: CompareRequest
):

    old_document = DOCUMENT_STORE.get(
        request.old_document_id
    )

    if not old_document:

        raise HTTPException(
            status_code=404,
            detail="Old document not found."
        )


    new_document = DOCUMENT_STORE.get(
        request.new_document_id
    )

    if not new_document:

        raise HTTPException(
            status_code=404,
            detail="New document not found."
        )


    if (
        request.old_document_id
        == request.new_document_id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Old and new document IDs "
                "must be different."
            )
        )


    try:

        result = compare_documents(

            old_document=old_document,

            new_document=new_document

        )

        return result


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document comparison failed: "
                f"{str(error)}"
            )
        )


# ============================================================
# VALIDATE HLD
# ============================================================

@router.get("/validate/{document_id}")
async def validate_hld_document(
    document_id: str
):

    document = DOCUMENT_STORE.get(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )


    try:

        entities = document.get(
            "entities",
            {}
        )


        validation_result = validate_document(
            entities
        )


        return {

            "document_id": document.get(
                "document_id"
            ),

            "filename": document.get(
                "filename"
            ),

            "total_pages": document.get(
                "total_pages"
            ),

            "processing": {

                "total_chunks": document[
                    "chunks"
                ].get(
                    "total_chunks",
                    0
                ),

                "embedding_model": document[
                    "embeddings"
                ].get(
                    "embedding_model",
                    ""
                ),

                "embedding_dimension": document[
                    "embeddings"
                ].get(
                    "embedding_dimension",
                    0
                )
            },

            "validation": validation_result
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document validation failed: "
                f"{str(error)}"
            )
        )