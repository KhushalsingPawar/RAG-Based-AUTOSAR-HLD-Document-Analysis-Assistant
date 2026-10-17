import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Project Models ---
class ProjectCreate(BaseModel):
    name: str = Field(..., description="EBCS Advanced Braking")
    vehicle_program: Optional[str] = Field("Tata EV Gen-3", description="Tata EV Gen-3")
    description: Optional[str] = Field(None, description="Electronic Brake Control Architecture Analysis")


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    vehicle_program: Optional[str]
    description: Optional[str]
    created_at: datetime.datetime


# --- Document Models ---
class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    version: str
    total_pages: int
    file_size_kb: float
    status: str
    uploaded_at: datetime.datetime


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    page_number: int
    section_title: str
    content: str
    token_count: int


# --- Autosar Entity Models ---
class AutosarEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    entity_type: str
    name: str
    port_type: Optional[str] = None
    interface_name: Optional[str] = None
    data_type: Optional[str] = None
    parent_component: Optional[str] = None
    source_page: int
    section_title: str
    description: Optional[str] = None


# --- RAG Query Models ---
class QueryRequest(BaseModel):
    question: str = Field(..., description="Identify the port receiving VehicleSpeed.")
    project_id: Optional[int] = Field(None, description="Project ID filter")
    document_id: Optional[int] = Field(None, description="Document ID filter")
    top_k: int = Field(4, ge=1, le=10)


class CitationSource(BaseModel):
    chunk_id: str
    document_id: int
    document_name: str
    version: str
    page_number: int
    section_title: str
    content: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: List[CitationSource]
    model_used: str
    grounding_confidence: str  # High, Medium, Low, Insufficient Evidence
    latency_seconds: float


# --- Revision Comparison Models ---
class CompareRequest(BaseModel):
    doc_a_id: int = Field(..., description="Baseline Document ID (e.g. v2.0)")
    doc_b_id: int = Field(..., description="Target Document ID (e.g. v2.1)")


class EntityDiffItem(BaseModel):
    entity_type: str
    name: str
    status: str  # Added, Removed, Modified, Unchanged
    details: Dict[str, Any]


class CompareResponse(BaseModel):
    doc_a_name: str
    doc_a_version: str
    doc_b_name: str
    doc_b_version: str
    summary: Dict[str, int]
    diff_items: List[EntityDiffItem]
    architectural_notes: List[str]


# --- Architectural Validation Models ---
class ValidationIssue(BaseModel):
    severity: str  # CRITICAL, WARNING, INFO
    category: str  # Unassigned Port, Dangling Signal, Data Type Mismatch
    entity_name: str
    component_name: Optional[str] = None
    page: int
    description: str
    recommendation: str


class ValidationResponse(BaseModel):
    document_id: int
    document_name: str
    document_version: str
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue]
    passed_audit: bool


# --- System Health ---
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_store: str
    ollama_service: str
    ollama_model: str
