import re


# ============================================================
# Utility Functions
# ============================================================

def clean_text(text: str) -> str:
    """
    Clean unnecessary spaces from extracted text.
    """

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def unique_entities(entities):
    """
    Remove duplicate entities based on their dictionary content.
    """

    unique = []

    for entity in entities:

        if entity not in unique:
            unique.append(entity)

    return unique


# ============================================================
# SOFTWARE COMPONENT EXTRACTION
# ============================================================

def extract_software_components(sections):
    """
    Extract AUTOSAR Software Components.

    Example:
        SWC: EngineControl
        Software Component: BrakeControl
        Component: SensorManager
    """

    components = []

    patterns = [
        r"(?:SWC|Software Component)\s*[:\-]\s*([A-Za-z0-9_.\-]+)",
        r"(?:Component)\s*[:\-]\s*([A-Za-z0-9_.\-]+)"
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                components.append({
                    "name": match.strip(),
                    "page_number": page_number,
                    "description": content[:300]
                })

    return unique_entities(components)


# ============================================================
# INTERFACE EXTRACTION
# ============================================================

def extract_interfaces(sections):
    """
    Extract AUTOSAR interfaces.

    Example:
        Interface: ISpeedData
        SenderReceiverInterface: ISensorData
        ClientServerInterface: IEngineControl
    """

    interfaces = []

    patterns = [
        r"(?:Interface)\s*[:\-]\s*([A-Za-z0-9_.\-]+)",

        r"(?:SenderReceiverInterface)\s*[:\-]\s*"
        r"([A-Za-z0-9_.\-]+)",

        r"(?:ClientServerInterface)\s*[:\-]\s*"
        r"([A-Za-z0-9_.\-]+)"
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                interface_type = None

                if "SenderReceiver" in pattern:
                    interface_type = "Sender-Receiver"

                elif "ClientServer" in pattern:
                    interface_type = "Client-Server"

                interfaces.append({
                    "name": match.strip(),
                    "page_number": page_number,
                    "interface_type": interface_type,
                    "description": content[:300]
                })

    return unique_entities(interfaces)


# ============================================================
# PORT EXTRACTION
# ============================================================

def extract_ports(sections):
    """
    Extract AUTOSAR ports.

    Example:
        Port: SpeedDataPort
        P-Port: SpeedData
        R-Port: VehicleSpeed
    """

    ports = []

    patterns = [
        (
            r"(?:Port)\s*[:\-]\s*"
            r"([A-Za-z0-9_.\-]+)",
            None
        ),

        (
            r"(?:P-Port)\s*[:\-]\s*"
            r"([A-Za-z0-9_.\-]+)",
            "P-Port"
        ),

        (
            r"(?:R-Port)\s*[:\-]\s*"
            r"([A-Za-z0-9_.\-]+)",
            "R-Port"
        ),

        (
            r"(?:Provide Port)\s*[:\-]\s*"
            r"([A-Za-z0-9_.\-]+)",
            "P-Port"
        ),

        (
            r"(?:Require Port)\s*[:\-]\s*"
            r"([A-Za-z0-9_.\-]+)",
            "R-Port"
        )
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern, port_type in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                ports.append({
                    "name": match.strip(),
                    "page_number": page_number,
                    "port_type": port_type,
                    "interface_name": None
                })

    return unique_entities(ports)


# ============================================================
# SIGNAL EXTRACTION
# ============================================================

def extract_signals(sections):
    """
    Extract signals.

    Example:
        Signal: VehicleSpeed
        Signal: EngineRPM
        Data Element: BrakePressure
    """

    signals = []

    patterns = [
        r"(?:Signal)\s*[:\-]\s*([A-Za-z0-9_.\-]+)",

        r"(?:Data Element)\s*[:\-]\s*"
        r"([A-Za-z0-9_.\-]+)"
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                signals.append({
                    "name": match.strip(),
                    "page_number": page_number,
                    "data_type": None,
                    "description": content[:300]
                })

    return unique_entities(signals)


# ============================================================
# DEPENDENCY EXTRACTION
# ============================================================

def extract_dependencies(sections):
    """
    Extract explicit dependency relationships.

    Example:
        EngineControl depends on SpeedSensor
        BrakeControl -> VehicleSpeed
    """

    dependencies = []

    patterns = [

        (
            r"([A-Za-z0-9_.\-]+)"
            r"\s+depends\s+on\s+"
            r"([A-Za-z0-9_.\-]+)"
        ),

        (
            r"([A-Za-z0-9_.\-]+)"
            r"\s+depends\s+upon\s+"
            r"([A-Za-z0-9_.\-]+)"
        ),

        (
            r"([A-Za-z0-9_.\-]+)"
            r"\s*->\s*"
            r"([A-Za-z0-9_.\-]+)"
        )
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for source, target in matches:

                dependencies.append({
                    "source": source.strip(),
                    "target": target.strip(),
                    "page_number": page_number,
                    "relationship": "depends_on"
                })

    return unique_entities(dependencies)


# ============================================================
# FUNCTIONAL FLOW EXTRACTION
# ============================================================

def extract_functional_flows(sections):
    """
    Extract functional flows.

    Example:
        Functional Flow: Vehicle Speed Processing
        Flow: Brake Control Flow
    """

    flows = []

    patterns = [

        r"(?:Functional Flow)\s*[:\-]\s*(.+)",

        r"(?:Functional Process)\s*[:\-]\s*(.+)",

        r"(?:Flow)\s*[:\-]\s*(.+)"
    ]

    for section in sections:

        content = section["content"]
        page_number = section["page_number"]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            for match in matches:

                flow_name = clean_text(match)

                flows.append({
                    "name": flow_name,
                    "page_number": page_number,
                    "description": content[:500]
                })

    return unique_entities(flows)


# ============================================================
# MAIN ENTITY EXTRACTION
# ============================================================

def extract_autosar_entities(structured_pages):
    """
    Extract all AUTOSAR entities from structured pages.
    """

    all_sections = []

    for page in structured_pages:

        sections = page.get(
            "sections",
            []
        )

        all_sections.extend(sections)

    software_components = extract_software_components(
        all_sections
    )

    interfaces = extract_interfaces(
        all_sections
    )

    ports = extract_ports(
        all_sections
    )

    signals = extract_signals(
        all_sections
    )

    dependencies = extract_dependencies(
        all_sections
    )

    functional_flows = extract_functional_flows(
        all_sections
    )
    
    print("\n========== ENTITY EXTRACTION ==========")

    print(
        "Software Components:",
        software_components
    )

    print(
        "Interfaces:",
        interfaces
    )

    print(
        "Ports:",
        ports
    )

    print(
        "Signals:",
        signals
    )

    print(
        "Dependencies:",
        dependencies
    )

    print(
        "Functional Flows:",
        functional_flows
    )

    return {
        "software_components": software_components,
        "interfaces": interfaces,
        "ports": ports,
        "signals": signals,
        "dependencies": dependencies,
        "functional_flows": functional_flows
    }