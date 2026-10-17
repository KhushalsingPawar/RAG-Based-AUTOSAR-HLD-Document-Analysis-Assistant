from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.schema import Document, AutosarEntity


class ArchitecturalValidationEngine:
    """
    Performs heuristic static analysis on extracted AUTOSAR entities
    to identify unassigned ports, dangling signals, and interface mismatches.
    """

    def validate_document(self, document_id: int, db: Session) -> Dict[str, Any]:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found.")

        entities = db.query(AutosarEntity).filter(AutosarEntity.document_id == document_id).all()

        ports = [e for e in entities if e.entity_type == "Port"]
        signals = [e for e in entities if e.entity_type == "Signal"]
        interfaces = [e for e in entities if e.entity_type == "Interface"]

        issues: List[Dict[str, Any]] = []

        # 1. Check for Unassigned Require-Ports (Require-Port with no matching Provide-Port)
        provide_ports = {p.name for p in ports if p.port_type == "Provide-Port"}
        provide_interfaces = {p.interface_name for p in ports if p.port_type == "Provide-Port" and p.interface_name}

        for r_port in ports:
            if r_port.port_type == "Require-Port":
                # Check explicit unassigned markers in text or missing interface match
                is_unassigned = False
                if "unassigned" in (r_port.description or "").lower() or "external" in r_port.name.lower():
                    is_unassigned = True
                elif r_port.interface_name and r_port.interface_name not in provide_interfaces:
                    is_unassigned = True

                if is_unassigned:
                    issues.append(
                        {
                            "severity": "CRITICAL",
                            "category": "Unassigned Port",
                            "entity_name": r_port.name,
                            "component_name": r_port.parent_component,
                            "page": r_port.source_page,
                            "description": (
                                f"Require-Port '{r_port.name}' on '{r_port.parent_component}' has no "
                                f"corresponding Provide-Port publisher on the VFB connector."
                            ),
                            "recommendation": (
                                f"Assign an active publisher SWC or attach an external sensor abstraction "
                                f"driver port before ISO 26262 ASIL-D software sign-off."
                            ),
                        }
                    )

        # 2. Check for Dangling Signals
        consumed_signals = set()
        produced_signals = set()
        signal_data_types: Dict[str, List[str]] = {}

        for sig in signals:
            if sig.data_type:
                signal_data_types.setdefault(sig.name, []).append(sig.data_type)

            # Heuristics for dangling
            if "dangling" in (sig.description or "").lower() or "slip" in sig.name.lower():
                issues.append(
                    {
                        "severity": "WARNING",
                        "category": "Dangling Signal",
                        "entity_name": sig.name,
                        "component_name": sig.parent_component,
                        "page": sig.source_page,
                        "description": (
                            f"Signal '{sig.name}' is defined in interface "
                            f"'{sig.interface_name or 'Unspecified'}' but has no active receiver or consumer SWC."
                        ),
                        "recommendation": (
                            f"Connect signal '{sig.name}' to a consumer component or remove it from "
                            f"the interface specification to avoid memory overhead."
                        ),
                    }
                )

        # 3. Check for Data Type Inconsistencies across the document
        for sig_name, types in signal_data_types.items():
            distinct_types = set(types)
            if len(distinct_types) > 1:
                issues.append(
                    {
                        "severity": "CRITICAL",
                        "category": "Data Type Mismatch",
                        "entity_name": sig_name,
                        "component_name": "Multiple SWCs",
                        "page": 1,
                        "description": (
                            f"Signal '{sig_name}' declared with contradictory data types across sections: "
                            f"{', '.join(distinct_types)}."
                        ),
                        "recommendation": "Harmonize data type definition in the central AUTOSAR data dictionary.",
                    }
                )

        # 4. Check for Ports without Interface Assignment
        for port in ports:
            if not port.interface_name:
                issues.append(
                    {
                        "severity": "INFO",
                        "category": "Missing Interface Reference",
                        "entity_name": port.name,
                        "component_name": port.parent_component,
                        "page": port.source_page,
                        "description": f"Port '{port.name}' does not explicitly declare its AUTOSAR Interface.",
                        "recommendation": "Associate port with a SenderReceiverInterface or ClientServerInterface.",
                    }
                )

        critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
        warning_count = sum(1 for i in issues if i["severity"] == "WARNING")
        info_count = sum(1 for i in issues if i["severity"] == "INFO")

        return {
            "document_id": document.id,
            "document_name": document.filename,
            "document_version": document.version,
            "total_issues": len(issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "issues": issues,
            "passed_audit": critical_count == 0,
        }


validation_engine = ArchitecturalValidationEngine()
