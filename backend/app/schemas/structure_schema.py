from pydantic import BaseModel
from typing import List


class TableData(BaseModel):
    page_number: int
    rows: List[List[str]]


class SectionData(BaseModel):
    page_number: int
    heading: str
    content: str


class StructuredPage(BaseModel):
    page_number: int
    headings: List[str]
    sections: List[SectionData]
    tables: List[TableData]


class StructuredDocument(BaseModel):
    filename: str
    total_pages: int
    document_type: str
    pages: List[StructuredPage]