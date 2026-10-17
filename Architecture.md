# Software Architecture Document
## AUTOSAR HLD Document Analysis Assistant
---
## 1. System Context & Overview
The application follows a modular, local-first client-server architecture. The user interacts with a **Streamlit** web frontend, which communicates via HTTP REST API endpoints hosted on a **FastAPI** backend service. The backend orchestrates PDF parsing, embedding generation, vector storage, and local LLM inference.
```mermaid
graph TD
    User([Engineer / Architect]) -->|Browser| UI[Streamlit Frontend]
    UI -->|REST API / JSON| API[FastAPI Backend Service]
    API -->|Extract Text/Tables| PDFEngine[PyMuPDF & Tesseract OCR]
    API -->|Store Metadata| SQLite[(SQLite / SQLAlchemy)]
    API -->|Generate Embeddings| Embedder[Sentence Transformers: bge-small-en-v1.5]
    Embedder -->|Store/Query Vectors| ChromaDB[(ChromaDB Vector Store)]
    API -->|Prompt + Context| LLM[Ollama Local Runtime: llama3.2]
2. Component & Container Architecture
Core Layers
Presentation Layer (Streamlit): Multi-page UI supporting HLD uploads, document summary views, entity inspection, RAG querying, version comparison, and validation reports.
API & Services Layer (FastAPI): Exposes REST routes (/upload, /query, /entities, /compare, /validate) with Pydantic validation.
Data & Storage Layer:
SQLite: Stores relational metadata (Project, Document, Review, AuditLog, AutosarEntity).
ChromaDB: Stores vector embeddings and document chunk metadata.
AI / ML Execution Layer: Runs embedding models locally via Sentence Transformers and interfaces with a local Ollama instance.
3. Data Flow: RAG Question Answering
Code snippet
sequenceDiagram
    participant User as Engineer
    participant UI as Streamlit UI
    participant API as FastAPI Backend
    participant DB as ChromaDB
    participant Ollama as Ollama LLM (llama3.2)
    User->>UI: Enter query ("Identify interface for VehicleSpeed")
    UI->>API: POST /api/query (question, project_id)
    API->>DB: Query semantic similarity (embedding of question)
    DB-->>API: Return top-k relevant document chunks with metadata
    API->>Ollama: Send prompt (Context + Question + Grounding Rules)
    Ollama-->>API: Generated response with citations
    API-->>UI: JSON response (answer, citations, source sections)
    UI-->>User: Display formatted answer and page references
4. Current Limitations & Target-State Evolution
State Management: Current document analysis stores temporary state in-memory (DOCUMENT_STORE), which is vulnerable to backend restarts. Target state requires robust SQLite persistence for all chunk mappings.
Authentication: Current implementation runs without authentication or authorization. Target state introduces OAuth2 / JWT role-based access control and strict project isolation.
Graph Traceability: Entity relationships (Port  Interface  Signal  Component) are currently extracted heuristically; target state incorporates a lightweight graph database or structured relational foreign-key mapping.