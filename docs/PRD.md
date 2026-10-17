# Product Requirements Document (PRD)
## AUTOSAR High-Level Design (HLD) Document Analysis Assistant
**Version:** 1.0.0  
**Status:** Draft / Interview Evaluation Release  
**Target System:** Automotive Engineering AI / Embedded Software Validation  
---
## 1. Executive Summary
AUTOSAR High-Level Design (HLD) documents are hundreds of pages of unstructured or semi-structured PDF content detailing software components, interfaces, ports, signals, dependencies, and functional flows. Engineers manually review these specifications, leading to slow onboarding, missed dependency mismatches, and delayed test planning. 
The **AUTOSAR HLD Document Analysis Assistant** is a local-first, AI-assisted engineering platform that automates document ingestion, semantic chunking, embedding generation, vector indexing, and evidence-based Retrieval-Augmented Generation (RAG). It provides systems architects, AUTOSAR developers, and testers with cited answers, architecture reports, and preliminary mismatch checks while ensuring engineering decisions remain under strict human review.
---
## 2. Problem Statement
- **Information Overload:** HLD documents span 100–500+ pages of complex technical jargon, tables, and nested interface definitions.
- **Manual Traceability Gaps:** Tracing a signal (e.g., `VehicleSpeed`) from a sensor port across multiple component interfaces to a consumer (e.g., `EngineControl`) requires tedious manual search.
- **Inconsistency Risks:** Mismatched port data types, missing dependencies, and outdated revisions often go undetected until integration testing or vehicle sign-off.
- **Compliance & Privacy Constraints:** Cloud-based commercial LLMs cannot be used due to strict intellectual property and confidentiality policies governing core vehicle architectures.
---
## 3. Business Objectives
- Reduce manual HLD document review and navigation effort by at least 50%.
- Establish a searchable, structured repository of internal architecture knowledge.
- Improve component, interface, signal, and dependency traceability.
- Accelerate engineer onboarding and impact analysis during design changes.
---
## 4. Goals and Non-Goals
### Goals
- Ingest local PDF HLD files and extract text, tables, headers, and metadata.
- Generate dense vector embeddings using `BAAI/bge-small-en-v1.5` and store them in ChromaDB.
- Support natural language queries with strict page/section citations using Ollama (`llama3.2:latest`).
- Provide preliminary revision comparison and consistency checking under human governance.
### Non-Goals
- Automatic approval or sign-off of architecture decisions.
- Direct modification of source PDF HLD files without explicit engineering review.
- Replacement of formal AUTOSAR authoring tools (e.g., DaVinci Configurator, ARCCORE).
- Certified AUTOSAR compliance verification.
---
## 5. Stakeholders and Personas
1. **System / AUTOSAR Architects:** Define component interfaces and ports; require high-level dependency verification and impact analysis.
2. **Software Developers:** Implement component behavior; require quick lookup of signal definitions and data types.
3. **Integration Engineers:** Connect software components; require port-to-interface mapping and dependency chain validation.
4. **Test Engineers:** Plan test cases; require traceability from functional flows to signals and consumers.
5. **Engineering Managers:** Oversee project delivery and review timelines.
---
## 6. Functional Requirements (FR)
| ID | Description | Priority | Status | Acceptance Criteria |
|---|---|---|---|---|
| **FR-001** | **PDF Ingestion & Parsing:** Upload HLD PDF files via Streamlit and parse content using PyMuPDF. | Must | Implemented | Successful upload and text/table extraction without crashing. |
| **FR-002** | **OCR Integration:** Extract text from scanned PDF pages using Tesseract. | Should | Partially Implemented | Scanned pages are detected and passed through OCR. |
| **FR-003** | **Contextual Chunking:** Split document text by section headings and architecture context. | Must | Implemented | Chunks maintain section metadata and appropriate token length. |
| **FR-004** | **Embedding & Vector Storage:** Generate 384-dim embeddings via `bge-small-en-v1.5` and store in ChromaDB. | Must | Implemented | Vectors successfully indexed and retrievable by semantic search. |
| **FR-005** | **RAG Question Answering:** Query the local Ollama LLM (`llama3.2`) with retrieved context and receive cited answers. | Must | Implemented | Answers include valid page/section references or state insufficient evidence. |
| **FR-006** | **Entity Extraction:** Extract components, ports, interfaces, and signals into SQLite. | Must | Partially Implemented | Structured entities saved with document foreign keys. |
| **FR-007** | **Revision Comparison:** Compare two HLD versions to identify added, modified, or removed entities. | Should | Partially Implemented | Diff report generated for selected document versions. |
| **FR-008** | **Validation & Inconsistency Checks:** Run heuristic checks for unassigned ports or dangling signals. | Could | Partially Implemented | Potential mismatch warnings displayed in UI. |
| **FR-009** | **Project Isolation:** Isolate documents and vector collections by project ID. | Should | Planned | API and database queries strictly filter by project context. |
| **FR-010** | **Role-Based Access Control:** Restrict administrative actions to authorized roles. | Could | Planned | User authentication and authorization enforced across endpoints. |
---
## 7. Non-Functional Requirements (NFR)
- **NFR-001 (Privacy & Security):** All processing must execute locally or within a private enterprise network (no external cloud LLM API calls).
- **NFR-002 (Performance):** Semantic query retrieval and initial RAG generation must complete within 5 seconds on standard developer hardware.
- **NFR-003 (Reliability):** Backend FastAPI services must handle malformed PDFs gracefully with HTTP 400/500 error responses.
- **NFR-004 (Maintainability):** Codebase must maintain modular separation between ingestion, embedding, vector storage, and UI layers.
---
## 8. Success Metrics
- **Review Effort Reduction:** Measured by estimated time saved on signal tracing queries.
- **Retrieval Accuracy:** Evaluated against baseline test sets (e.g., 10/10 vehicle speed test queries).
- **Grounding Rate:** 100% of generated answers must cite source sections or explicitly report insufficient evidence.