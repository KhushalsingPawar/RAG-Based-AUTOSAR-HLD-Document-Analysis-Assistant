import os
import re
from typing import List, Dict, Any
import fitz  # PyMuPDF


class PDFParserService:
    """
    Parses AUTOSAR High-Level Design (HLD) PDF documents using PyMuPDF.
    Extracts text, structural section headings, and metadata.
    Includes heuristic detection for scanned pages (OCR fallback).
    """

    HEADING_REGEX = re.compile(
        r"^(?:(?:\d+\.|\d+\.\d+|\d+\.\d+\.\d+)\s+[A-Z][\w\s\-_/]+|Section\s+\d+[\.\d]*\s*.*|[A-Z][A-Z0-9\s\-_]{3,40}:?$)",
        re.MULTILINE,
    )

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_data: List[Dict[str, Any]] = []
        all_headings: List[str] = []

        current_active_section = "Document Overview"

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            raw_text = page.get_text("text").strip()

            # Check if page is likely scanned (very little text extracted from non-empty page)
            is_scanned = len(raw_text) < 30 and len(page.get_images()) > 0

            # Identify section headings on this page
            page_headings = []
            lines = raw_text.splitlines()
            for line in lines:
                cleaned_line = line.strip()
                if self.HEADING_REGEX.match(cleaned_line):
                    page_headings.append(cleaned_line)
                    all_headings.append(cleaned_line)
                    current_active_section = cleaned_line

            pages_data.append(
                {
                    "page_number": page_num,
                    "text": raw_text,
                    "active_section": current_active_section,
                    "detected_headings": page_headings,
                    "is_scanned": is_scanned,
                    "character_count": len(raw_text),
                }
            )

        doc.close()

        file_size_kb = round(os.path.getsize(file_path) / 1024, 2)

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "total_pages": total_pages,
            "file_size_kb": file_size_kb,
            "pages": pages_data,
            "headings": all_headings,
        }


pdf_parser = PDFParserService()
