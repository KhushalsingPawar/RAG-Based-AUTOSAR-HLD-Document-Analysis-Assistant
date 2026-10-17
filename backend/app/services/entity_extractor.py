import re
from typing import List, Dict, Any
from backend.app.models.schema import AutosarEntity


class AutosarEntityExtractor:
    """
    Extracts AUTOSAR software components (SWCs), ports, interfaces, signals,
    and associated data types from parsed HLD document text.
    """

    # AUTOSAR naming pattern conventions
    SWC_PATTERN = re.compile(
        r"(?:Component:\s*|Software\s+Component:\s*|\b)([A-Z][a-zA-Z0-9_]+SWC|[A-Z][a-zA-Z0-9_]+Component)\b"
    )
    PORT_PATTERN = re.compile(
        r"(?:(Provide-Port|Require-Port|PPort|RPort):\s*|\b)([PR]_[a-zA-Z0-9_]+)\b"
    )
    INTERFACE_PATTERN = re.compile(
        r"(?:Interface:\s*|\b)([A-Z][a-zA-Z0-9_]+(?:_IF|Interface))\b"
    )
    SIGNAL_PATTERN = re.compile(
        r"(?:Signal:\s*|Transmitted Signal:\s*|Received Signal:\s*)([A-Z][a-zA-Z0-9_]+)\b"
    )
    DATATYPE_PATTERN = re.compile(
        r"(?:Data Type:\s*|\b)(uint8|uint16|uint32|sint8|sint16|sint32|float32|float64|boolean)\b",
        re.IGNORECASE,
    )

    def extract_from_pages(self, pages_data: List[Dict[str, Any]], document_id: int) -> List[Dict[str, Any]]:
        extracted_entities: List[Dict[str, Any]] = []
        seen_keys = set()

        current_component = "GeneralEBCS"

        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]
            section = page.get("active_section", "General Architecture")

            lines = text.splitlines()
            current_port_type = None
            current_port_name = None
            current_interface = None
            current_signal = None
            current_data_type = None

            for line in lines:
                cleaned = line.strip()

                # Detect active SWC
                if swc_match := self.SWC_PATTERN.search(cleaned):
                    detected_swc = swc_match.group(1)
                    current_component = detected_swc
                    key = ("Component", detected_swc, page_num)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        extracted_entities.append(
                            {
                                "document_id": document_id,
                                "entity_type": "Component",
                                "name": detected_swc,
                                "parent_component": None,
                                "port_type": None,
                                "interface_name": None,
                                "data_type": None,
                                "source_page": page_num,
                                "section_title": section,
                                "description": f"Software Component declared in {section}.",
                            }
                        )

                # Detect Ports
                if port_match := self.PORT_PATTERN.search(cleaned):
                    kind_raw = port_match.group(1)
                    port_name = port_match.group(2)
                    if port_name.startswith("P_") or (kind_raw and "Provide" in kind_raw):
                        current_port_type = "Provide-Port"
                    elif port_name.startswith("R_") or (kind_raw and "Require" in kind_raw):
                        current_port_type = "Require-Port"
                    else:
                        current_port_type = "Port"

                    current_port_name = port_name
                    key = ("Port", port_name, page_num)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        extracted_entities.append(
                            {
                                "document_id": document_id,
                                "entity_type": "Port",
                                "name": port_name,
                                "port_type": current_port_type,
                                "parent_component": current_component,
                                "interface_name": current_interface,
                                "data_type": current_data_type,
                                "source_page": page_num,
                                "section_title": section,
                                "description": f"{current_port_type} belonging to {current_component}.",
                            }
                        )

                # Detect Interfaces
                if if_match := self.INTERFACE_PATTERN.search(cleaned):
                    if_name = if_match.group(1)
                    current_interface = if_name
                    key = ("Interface", if_name, page_num)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        extracted_entities.append(
                            {
                                "document_id": document_id,
                                "entity_type": "Interface",
                                "name": if_name,
                                "port_type": None,
                                "parent_component": current_component,
                                "interface_name": if_name,
                                "data_type": None,
                                "source_page": page_num,
                                "section_title": section,
                                "description": f"AUTOSAR Interface definition referenced in {section}.",
                            }
                        )

                # Detect Signals
                if sig_match := self.SIGNAL_PATTERN.search(cleaned):
                    sig_name = sig_match.group(1)
                    current_signal = sig_name

                    # Look ahead or check same line for data type
                    dt_match = self.DATATYPE_PATTERN.search(cleaned)
                    dt = dt_match.group(1).lower() if dt_match else None

                    key = ("Signal", sig_name, page_num)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        extracted_entities.append(
                            {
                                "document_id": document_id,
                                "entity_type": "Signal",
                                "name": sig_name,
                                "port_type": current_port_type,
                                "parent_component": current_component,
                                "interface_name": current_interface,
                                "data_type": dt,
                                "source_page": page_num,
                                "section_title": section,
                                "description": f"Architectural Signal mapped in {current_component}.",
                            }
                        )

                # Catch Standalone Data Type line
                if dt_match := self.DATATYPE_PATTERN.search(cleaned):
                    current_data_type = dt_match.group(1).lower()
                    # Backpropagate to last added signal if missing
                    if extracted_entities and extracted_entities[-1]["entity_type"] == "Signal":
                        if not extracted_entities[-1]["data_type"]:
                            extracted_entities[-1]["data_type"] = current_data_type

        return extracted_entities


entity_extractor = AutosarEntityExtractor()
