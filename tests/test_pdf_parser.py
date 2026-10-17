import os
import pytest
from backend.app.services.pdf_parser import pdf_parser

SAMPLE_PDF = "data/sample_hlds/Brake_System_HLD_v2.0.pdf"


def test_pdf_parsing():
    assert os.path.exists(SAMPLE_PDF), "Sample PDF should exist before running test"
    result = pdf_parser.parse_pdf(SAMPLE_PDF)

    assert result["total_pages"] == 9
    assert result["filename"] == "Brake_System_HLD_v2.0.pdf"
    assert len(result["pages"]) == 9
    assert result["file_size_kb"] > 0

    # Verify that first page has introductory text
    first_page = result["pages"][0]
    assert first_page["page_number"] == 1   
    assert "AUTOSAR" in first_page["text"]
    assert first_page["character_count"] > 100
