import re


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_content(text: str) -> str:
    """
    Clean unnecessary whitespace from chunk content.
    """

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CHUNK ID
# ============================================================

def generate_chunk_id(
    document_id: str,
    page_number: int,
    chunk_number: int
):
    """
    Generate a unique ID for every chunk.
    """

    return (
        f"{document_id}_"
        f"page_{page_number}_"
        f"chunk_{chunk_number}"
    )


# ============================================================
# SECTION CHUNKS
# ============================================================

def create_section_chunks(
    document_id: str,
    filename: str,
    structured_pages
):
    """
    Convert structured document sections
    into RAG-ready chunks.
    """

    chunks = []

    chunk_counter = 1

    for page in structured_pages:

        page_number = page["page_number"]

        sections = page.get(
            "sections",
            []
        )

        for section in sections:

            heading = section.get(
                "heading"
            )

            content = section.get(
                "content",
                ""
            )

            content = clean_content(
                content
            )

            if not content:
                continue

            chunk_id = generate_chunk_id(
                document_id,
                page_number,
                chunk_counter
            )

            chunks.append({

                "chunk_id": chunk_id,

                "document_id": document_id,

                "filename": filename,

                "page_number": page_number,

                "section": heading,

                "heading": heading,

                "entity_type": None,

                "entity_name": None,

                "content": content,

                "source": (
                    f"{filename} - "
                    f"Page {page_number}"
                )
            })

            chunk_counter += 1

    return chunks


# ============================================================
# ENTITY CHUNKS
# ============================================================

def create_entity_chunks(
    document_id: str,
    filename: str,
    entities
):
    """
    Convert extracted AUTOSAR entities
    into entity-specific chunks.
    """

    chunks = []

    chunk_counter = 1

    entity_groups = [

        (
            "SoftwareComponent",
            entities.get(
                "software_components",
                []
            )
        ),

        (
            "Interface",
            entities.get(
                "interfaces",
                []
            )
        ),

        (
            "Port",
            entities.get(
                "ports",
                []
            )
        ),

        (
            "Signal",
            entities.get(
                "signals",
                []
            )
        ),

        (
            "Dependency",
            entities.get(
                "dependencies",
                []
            )
        ),

        (
            "FunctionalFlow",
            entities.get(
                "functional_flows",
                []
            )
        )
    ]

    for entity_type, entity_list in entity_groups:

        for entity in entity_list:

            page_number = entity.get(
                "page_number",
                0
            )

            # --------------------------------
            # Software Component
            # --------------------------------

            if entity_type == "SoftwareComponent":

                entity_name = entity.get(
                    "name"
                )

                description = entity.get(
                    "description",
                    ""
                )

                content = (
                    f"Software Component: "
                    f"{entity_name}. "
                    f"{description}"
                )

            # --------------------------------
            # Interface
            # --------------------------------

            elif entity_type == "Interface":

                entity_name = entity.get(
                    "name"
                )

                interface_type = entity.get(
                    "interface_type"
                )

                description = entity.get(
                    "description",
                    ""
                )

                content = (
                    f"Interface: "
                    f"{entity_name}. "
                    f"Interface Type: "
                    f"{interface_type or 'Not specified'}. "
                    f"{description}"
                )

            # --------------------------------
            # Port
            # --------------------------------

            elif entity_type == "Port":

                entity_name = entity.get(
                    "name"
                )

                port_type = entity.get(
                    "port_type"
                )

                interface_name = entity.get(
                    "interface_name"
                )

                content = (
                    f"Port: {entity_name}. "
                    f"Port Type: "
                    f"{port_type or 'Not specified'}. "
                    f"Interface: "
                    f"{interface_name or 'Not specified'}."
                )

            # --------------------------------
            # Signal
            # --------------------------------

            elif entity_type == "Signal":

                entity_name = entity.get(
                    "name"
                )

                data_type = entity.get(
                    "data_type"
                )

                description = entity.get(
                    "description",
                    ""
                )

                content = (
                    f"Signal: "
                    f"{entity_name}. "
                    f"Data Type: "
                    f"{data_type or 'Not specified'}. "
                    f"{description}"
                )

            # --------------------------------
            # Dependency
            # --------------------------------

            elif entity_type == "Dependency":

                source = entity.get(
                    "source"
                )

                target = entity.get(
                    "target"
                )

                relationship = entity.get(
                    "relationship",
                    "depends_on"
                )

                entity_name = (
                    f"{source} -> {target}"
                )

                content = (
                    f"{source} "
                    f"{relationship} "
                    f"{target}."
                )

            # --------------------------------
            # Functional Flow
            # --------------------------------

            else:

                entity_name = entity.get(
                    "name"
                )

                description = entity.get(
                    "description",
                    ""
                )

                content = (
                    f"Functional Flow: "
                    f"{entity_name}. "
                    f"{description}"
                )

            content = clean_content(
                content
            )

            chunk_id = (
                f"{document_id}_"
                f"entity_{chunk_counter}"
            )

            chunks.append({

                "chunk_id": chunk_id,

                "document_id": document_id,

                "filename": filename,

                "page_number": page_number,

                "section": entity_type,

                "heading": entity_type,

                "entity_type": entity_type,

                "entity_name": entity_name,

                "content": content,

                "source": (
                    f"{filename} - "
                    f"Page {page_number}"
                )
            })

            chunk_counter += 1

    return chunks


# ============================================================
# COMBINED CHUNK CREATION
# ============================================================

def create_document_chunks(
    document_id: str,
    filename: str,
    structured_pages,
    entities
):
    """
    Create both section-level and
    entity-level chunks.
    """
    
    section_chunks = create_section_chunks(
        document_id,
        filename,
        structured_pages
    )

    entity_chunks = create_entity_chunks(
        document_id,
        filename,
        entities
    )

    return {
        "section_chunks": section_chunks,
        "entity_chunks": entity_chunks,
        "total_chunks": (
            len(section_chunks)
            + len(entity_chunks)
        )
    }