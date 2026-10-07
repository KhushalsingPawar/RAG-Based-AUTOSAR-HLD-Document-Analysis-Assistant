from collections import defaultdict


def normalize_name(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def validate_duplicate_ports(ports):
    """
    Detect duplicate port names on the same page.
    """

    grouped_ports = defaultdict(list)

    for port in ports:
        name = normalize_name(port.get("name"))
        page_number = port.get("page_number")

        if not name:
            continue

        key = (name, page_number)
        grouped_ports[key].append(port)

    issues = []

    for (name, page_number), matching_ports in grouped_ports.items():

        if len(matching_ports) > 1:

            issues.append({
                "type": "DUPLICATE_PORT",
                "severity": "HIGH",
                "message": (
                    f"Duplicate port '{name}' found "
                    f"on page {page_number}."
                ),
                "page_number": page_number,
                "entity_name": name,
                "count": len(matching_ports)
            })

    return issues


def validate_dependency_targets(
    software_components,
    dependencies
):
    """
    Check whether dependency targets are defined
    as software components.
    """

    component_names = {
        normalize_name(component.get("name"))
        for component in software_components
        if component.get("name")
    }

    issues = []

    for dependency in dependencies:

        source = dependency.get("source")
        target = dependency.get("target")
        page_number = dependency.get("page_number")

        normalized_target = normalize_name(target)

        if (
            normalized_target
            and normalized_target not in component_names
        ):

            issues.append({
                "type": "MISSING_DEPENDENCY_TARGET",
                "severity": "HIGH",
                "message": (
                    f"Dependency target '{target}' "
                    f"is not defined as a software component."
                ),
                "page_number": page_number,
                "source": source,
                "target": target
            })

    return issues


def validate_dependency_sources(
    software_components,
    dependencies
):
    """
    Check whether dependency sources are defined.
    """

    component_names = {
        normalize_name(component.get("name"))
        for component in software_components
        if component.get("name")
    }

    issues = []

    for dependency in dependencies:

        source = dependency.get("source")
        target = dependency.get("target")
        page_number = dependency.get("page_number")

        normalized_source = normalize_name(source)

        if (
            normalized_source
            and normalized_source not in component_names
        ):

            issues.append({
                "type": "UNDEFINED_COMPONENT_REFERENCE",
                "severity": "HIGH",
                "message": (
                    f"Dependency source '{source}' "
                    f"is not defined as a software component."
                ),
                "page_number": page_number,
                "source": source,
                "target": target
            })

    return issues


def validate_ports_without_interface(ports):
    """
    Detect ports where interface information is missing.
    """

    issues = []

    for port in ports:

        interface_name = port.get("interface_name")
        port_name = port.get("name")
        page_number = port.get("page_number")

        if not interface_name:

            issues.append({
                "type": "PORT_WITHOUT_INTERFACE",
                "severity": "MEDIUM",
                "message": (
                    f"Port '{port_name}' has no "
                    f"associated interface."
                ),
                "page_number": page_number,
                "entity_name": port_name
            })

    return issues


def validate_interfaces_without_component(
    interfaces,
    software_components,
    ports
):
    """
    Detect interfaces that do not appear to be connected
    to any component.

    Since the current extraction model does not yet store
    explicit component-interface relationships, this rule
    uses available port/interface references.
    """

    interface_names = {
        normalize_name(interface.get("name"))
        for interface in interfaces
        if interface.get("name")
    }

    connected_interfaces = {
        normalize_name(port.get("interface_name"))
        for port in ports
        if port.get("interface_name")
    }

    issues = []

    for interface in interfaces:

        name = interface.get("name")
        page_number = interface.get("page_number")

        if (
            normalize_name(name) not in connected_interfaces
        ):

            issues.append({
                "type": "INTERFACE_WITHOUT_CONNECTION",
                "severity": "MEDIUM",
                "message": (
                    f"Interface '{name}' does not have "
                    f"a connected port."
                ),
                "page_number": page_number,
                "entity_name": name
            })

    return issues


def validate_signal_data_types(signals):
    """
    Detect the same signal having conflicting data types.
    """

    signal_types = defaultdict(set)

    signal_pages = defaultdict(list)

    for signal in signals:

        name = normalize_name(signal.get("name"))
        data_type = signal.get("data_type")
        page_number = signal.get("page_number")

        if not name:
            continue

        if data_type:
            signal_types[name].add(
                normalize_name(data_type)
            )

        signal_pages[name].append(page_number)

    issues = []

    for signal_name, data_types in signal_types.items():

        if len(data_types) > 1:

            issues.append({
                "type": "CONFLICTING_SIGNAL_DATA_TYPE",
                "severity": "HIGH",
                "message": (
                    f"Signal '{signal_name}' has "
                    f"conflicting data types."
                ),
                "entity_name": signal_name,
                "data_types": sorted(data_types),
                "pages": signal_pages[signal_name]
            })

    return issues


def validate_document(entities):
    """
    Run all validation rules.
    """

    software_components = entities.get(
        "software_components",
        []
    )

    interfaces = entities.get(
        "interfaces",
        []
    )

    ports = entities.get(
        "ports",
        []
    )

    signals = entities.get(
        "signals",
        []
    )

    dependencies = entities.get(
        "dependencies",
        []
    )

    all_issues = []

    all_issues.extend(
        validate_duplicate_ports(ports)
    )

    all_issues.extend(
        validate_dependency_sources(
            software_components,
            dependencies
        )
    )

    all_issues.extend(
        validate_dependency_targets(
            software_components,
            dependencies
        )
    )

    all_issues.extend(
        validate_ports_without_interface(
            ports
        )
    )

    all_issues.extend(
        validate_interfaces_without_component(
            interfaces,
            software_components,
            ports
        )
    )

    all_issues.extend(
        validate_signal_data_types(
            signals
        )
    )

    severity_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for issue in all_issues:

        severity = issue.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "total_issues": len(all_issues),
        "severity_summary": severity_counts,
        "issues": all_issues
    }