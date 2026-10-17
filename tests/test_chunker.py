from backend.app.services.chunker import chunker


def test_chunker_basic():
    fake_parsed_data = {
        "filename": "Test_HLD.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": "1. Overview\n\nThis is an introductory section.\n\n2. Architecture Details\n\nSpeedProcessingSWC connects to BrakeControlSWC.",
                "active_section": "1. Overview",
            }
        ],
    }

    chunks = chunker.chunk_document(fake_parsed_data)
    assert len(chunks) >= 1
    first_chunk = chunks[0]

    assert first_chunk["page_number"] == 1
    assert "Test_HLD.pdf" in first_chunk["content"]
    assert first_chunk["token_count"] > 0
