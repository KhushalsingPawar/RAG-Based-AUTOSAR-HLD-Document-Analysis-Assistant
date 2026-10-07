import fitz


def extract_pdf_text(file_path: str):
    """
    Extract text from a PDF page by page.

    Returns:
        [
            {
                "page_number": 1,
                "text": "..."
            }
        ]
    """

    pages = []

    document = fitz.open(file_path)

    try:
        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text")

            pages.append({
                "page_number": page_number,
                "text": text.strip()
            })

    finally:
        document.close()

    return pages