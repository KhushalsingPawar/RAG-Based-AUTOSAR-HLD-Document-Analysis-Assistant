from app.services.entity_service import (
    extract_autosar_entities
)


def flatten_structured_pages(structured_pages):
    sections = []

    for page in structured_pages:
        page_sections = page.get("sections", [])
        sections.extend(page_sections)

    return sections


def generate_entity_report(structured_pages):
    entities = extract_autosar_entities(
        structured_pages
    )
    

    return {
        "software_components": entities.get(
            "software_components", []
        ),
        "interfaces": entities.get(
            "interfaces", []
        ),
        "ports": entities.get(
            "ports", []
        ),
        "signals": entities.get(
            "signals", []
        ),
        "dependencies": entities.get(
            "dependencies", []
        ),
        "functional_flows": entities.get(
            "functional_flows", []
        )
    }


def generate_summary_report(
    filename,
    total_pages,
    structured_pages
):
    entities = generate_entity_report(
        structured_pages
    )

    return {
        "filename": filename,
        "total_pages": total_pages,
        "summary": {
            "software_components": len(
                entities["software_components"]
            ),
            "interfaces": len(
                entities["interfaces"]
            ),
            "ports": len(
                entities["ports"]
            ),
            "signals": len(
                entities["signals"]
            ),
            "dependencies": len(
                entities["dependencies"]
            ),
            "functional_flows": len(
                entities["functional_flows"]
            )
        },
        "entities": entities
    }