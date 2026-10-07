from pydantic import BaseModel
from typing import List


class PageContent(BaseModel):
    page_number: int
    text: str


class DocumentResponse(BaseModel):
    filename: str
    total_pages: int
    pages: List[PageContent]