import re
from typing import List, Dict, Any
from backend.app.config import settings


class ContextualChunker:
    """
    Contextual Chunking Service for AUTOSAR HLD documents.
    Preserves document structure, section headers, and page citations within each chunk.
    """

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        filename = parsed_data.get("filename", "Unknown_Document.pdf")
        pages = parsed_data.get("pages", [])
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            active_section = page.get("active_section", "General Architecture")

            if not page_text or len(page_text.strip()) == 0:
                continue

            # Split page into logical paragraphs
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", page_text) if p.strip()]

            current_chunk_text = ""
            current_section = active_section

            for para in paragraphs:
                # Check if paragraph contains a new section heading
                first_line = para.splitlines()[0].strip()
                if pdf_parser_heading := self._extract_heading(first_line):
                    current_section = pdf_parser_heading

                if len(current_chunk_text) + len(para) > self.chunk_size and len(current_chunk_text) > 0:
                    # Save current chunk
                    formatted_content = (
                        f"[Document: {filename} | Section: {current_section} | Page: {page_num}]\n"
                        f"{current_chunk_text.strip()}"
                    )
                    chunks.append(
                        {
                            "chunk_index": chunk_idx,
                            "page_number": page_num,
                            "section_title": current_section,
                            "content": formatted_content,
                            "raw_text": current_chunk_text.strip(),
                            "token_count": len(formatted_content.split()),
                        }
                    )
                    chunk_idx += 1

                    # Overlap handling: keep the trailing overlap text
                    overlap_words = current_chunk_text.split()[-int(self.chunk_overlap / 5) :]
                    current_chunk_text = " ".join(overlap_words) + "\n\n" + para
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para

            # Add remaining text on the page
            if current_chunk_text.strip():
                formatted_content = (
                    f"[Document: {filename} | Section: {current_section} | Page: {page_num}]\n"
                    f"{current_chunk_text.strip()}"
                )
                chunks.append(
                    {
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "section_title": current_section,
                        "content": formatted_content,
                        "raw_text": current_chunk_text.strip(),
                        "token_count": len(formatted_content.split()),
                    }
                )
                chunk_idx += 1

        return chunks

    def _extract_heading(self, line: str) -> str | None:
        if re.match(r"^(?:Section\s+\d+|[\d\.]+\s+[A-Z]|[A-Z\s]{4,30}$)", line):
            return line[:60]
        return None


chunker = ContextualChunker()
