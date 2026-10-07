from pydantic import BaseModel
from typing import Optional


class DocumentChunk(BaseModel):
    chunk_id: str

    document_id: str

    filename: str

    page_number: int

    section: Optional[str] = None

    heading: Optional[str] = None

    entity_type: Optional[str] = None

    entity_name: Optional[str] = None

    content: str

    source: str