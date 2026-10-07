import re
import fitz


# ---------------------------------------------------------
# 1. HEADING DETECTION
# ---------------------------------------------------------

def is_heading(line: str) -> bool:

    line = line.strip()

    if not line:
        return False

    
    numbered_heading = re.match(
        r"^\d+(\.\d+)*\.?\s+.+",
        line
    )

    if numbered_heading:
        return True

    # Common AUTOSAR-related keywords
    keywords = [
        "architecture",
        "software components",
        "software component",
        "interfaces",
        "interface",
        "signals",
        "signal",
        "dependencies",
        "dependency",
        "functional flow",
        "functional flows",
        "system design",
        "system architecture",
        "component design",
        "communication",
        "ports",
        "requirements"
    ]

    lower_line = line.lower()

    for keyword in keywords:
        if keyword in lower_line:
            return True

    return False


# ---------------------------------------------------------
# 2. SECTION EXTRACTION
# ---------------------------------------------------------

def extract_sections(text: str, page_number: int):
    """
    Convert page text into structured sections.
    """

    lines = text.splitlines()

    sections = []

    current_heading = None
    current_content = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if is_heading(line):

            # Save previous section
            if current_heading is not None:

                sections.append({
                    "page_number": page_number,
                    "heading": current_heading,
                    "content": " ".join(current_content).strip()
                })

            # Start new section
            current_heading = line
            current_content = []

        else:

            current_content.append(line)

    # Save last section
    if current_heading is not None:

        sections.append({
            "page_number": page_number,
            "heading": current_heading,
            "content": " ".join(current_content).strip()
        })

    return sections


# ---------------------------------------------------------
# 3. TABLE EXTRACTION
# ---------------------------------------------------------

def extract_tables_from_pdf(file_path: str):
    """
    Extract digital tables from the PDF.

    Returns:
        [
            {
                "page_number": 1,
                "rows": [...]
            }
        ]
    """

    all_tables = []

    document = fitz.open(file_path)

    try:

        for page_number, page in enumerate(document, start=1):

            try:

                table_finder = page.find_tables()

                for table in table_finder.tables:

                    rows = table.extract()

                    if rows:

                        cleaned_rows = []

                        for row in rows:

                            cleaned_row = [
                                str(cell).strip() if cell is not None else ""
                                for cell in row
                            ]

                            cleaned_rows.append(cleaned_row)

                        all_tables.append({
                            "page_number": page_number,
                            "rows": cleaned_rows
                        })

            except Exception as error:

                print(
                    f"Table extraction failed on page "
                    f"{page_number}: {error}"
                )

    finally:
        document.close()

    return all_tables


# ---------------------------------------------------------
# 4. STRUCTURED PAGE PROCESSING
# ---------------------------------------------------------

def process_document_pages(pages, tables):
    """
    Combine extracted text, sections and tables.
    """

    structured_pages = []

    for page in pages:

        page_number = page["page_number"]
        text = page["text"]

        # Extract sections
        sections = extract_sections(
            text,
            page_number
        )

        # Extract heading list
        headings = [
            section["heading"]
            for section in sections
        ]

        # Find tables belonging to this page
        page_tables = [
            table
            for table in tables
            if table["page_number"] == page_number
        ]

        structured_pages.append({
            "page_number": page_number,
            "headings": headings,
            "sections": sections,
            "tables": page_tables
        })

    return structured_pages