# AUTOSAR HLD Document Analysis Assistant - Documentation Suite
This documentation suite has been prepared for the **AUTOSAR HLD Document Analysis Assistant** project, developed as part of the Tata Technologies interview selection process. 
## Overview of Deliverables
1. **`Project_Feature_guide.pdf`** *(Design & Content Spec)*: A stakeholder-facing feature manual detailing capabilities, end-to-end workflows, user interaction models, and example Q&A.
2. **`PRD.md` (Product Requirements Document):** A comprehensive product specification mapping business objectives to functional and non-functional requirements (`FR-001`, `NFR-001`, etc.), user personas, and release phases.
3. **`Architecture.md` (Software Architecture Document):** A technical deep-dive covering the FastAPI backend, Streamlit frontend, PyMuPDF extraction pipeline, Sentence Transformers, ChromaDB vector storage, Ollama local LLM integration, and Mermaid diagrams.
4. **`implementation_plan.md` (Phased Roadmap):** A rigorous 8-phase implementation plan moving from baseline discovery and ingestion hardening to advanced RAG, revision comparison, security, and testing.
## Consistency and Status Legend
All documents strictly reflect the current implementation state (`FastAPI`, `Streamlit`, `PyMuPDF`, `BAAI/bge-small-en-v1.5`, `ChromaDB`, `Ollama/llama3.2`, and `SQLite`), distinguishing verified features from planned enhancements.