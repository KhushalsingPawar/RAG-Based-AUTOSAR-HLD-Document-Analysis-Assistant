from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.schema import Document, AutosarEntity


class RevisionDiffEngine:
    """
    Compares two AUTOSAR HLD document revisions to identify added, modified,
    and removed components, ports, interfaces, and signals.
    """

    def compare_revisions(self, doc_a_id: int, doc_b_id: int, db: Session) -> Dict[str, Any]:
        doc_a = db.query(Document).filter(Document.id == doc_a_id).first()
        doc_b = db.query(Document).filter(Document.id == doc_b_id).first()

        if not doc_a or not doc_b:
            raise ValueError("One or both document revisions could not be found.")

        entities_a = db.query(AutosarEntity).filter(AutosarEntity.document_id == doc_a_id).all()
        entities_b = db.query(AutosarEntity).filter(AutosarEntity.document_id == doc_b_id).all()

        map_a = {(e.entity_type, e.name): e for e in entities_a}
        map_b = {(e.entity_type, e.name): e for e in entities_b}

        diff_items: List[Dict[str, Any]] = []
        notes: List[str] = []

        added_count = 0
        removed_count = 0
        modified_count = 0
        unchanged_count = 0

        # Check for Added and Modified/Unchanged in B
        for key, ent_b in map_b.items():
            ent_type, name = key
            if key not in map_a:
                added_count += 1
                diff_items.append(
                    {
                        "entity_type": ent_type,
                        "name": name,
                        "status": "Added",
                        "details": {
                            "component": ent_b.parent_component,
                            "port_type": ent_b.port_type,
                            "interface": ent_b.interface_name,
                            "data_type": ent_b.data_type,
                            "page": ent_b.source_page,
                            "section": ent_b.section_title,
                        },
                    }
                )
                notes.append(f"New {ent_type} '{name}' introduced in {doc_b.version} (Page {ent_b.source_page}).")
            else:
                ent_a = map_a[key]
                # Check for modifications
                changed_attrs = []
                if ent_a.data_type != ent_b.data_type:
                    changed_attrs.append(f"data_type changed: '{ent_a.data_type}' -> '{ent_b.data_type}'")
                if ent_a.port_type != ent_b.port_type:
                    changed_attrs.append(f"port_type changed: '{ent_a.port_type}' -> '{ent_b.port_type}'")
                if ent_a.parent_component != ent_b.parent_component:
                    changed_attrs.append(f"parent_component changed: '{ent_a.parent_component}' -> '{ent_b.parent_component}'")

                if changed_attrs:
                    modified_count += 1
                    diff_items.append(
                        {
                            "entity_type": ent_type,
                            "name": name,
                            "status": "Modified",
                            "details": {
                                "modifications": changed_attrs,
                                "previous": {"data_type": ent_a.data_type, "port_type": ent_a.port_type},
                                "current": {"data_type": ent_b.data_type, "port_type": ent_b.port_type},
                                "page": ent_b.source_page,
                            },
                        }
                    )
                    notes.append(f"{ent_type} '{name}' modified: {'; '.join(changed_attrs)}.")
                else:
                    unchanged_count += 1
                    diff_items.append(
                        {
                            "entity_type": ent_type,
                            "name": name,
                            "status": "Unchanged",
                            "details": {
                                "component": ent_b.parent_component,
                                "data_type": ent_b.data_type,
                                "page": ent_b.source_page,
                            },
                        }
                    )

        # Check for Removed from A
        for key, ent_a in map_a.items():
            ent_type, name = key
            if key not in map_b:
                removed_count += 1
                diff_items.append(
                    {
                        "entity_type": ent_type,
                        "name": name,
                        "status": "Removed",
                        "details": {
                            "component": ent_a.parent_component,
                            "port_type": ent_a.port_type,
                            "data_type": ent_a.data_type,
                            "last_seen_page": ent_a.source_page,
                        },
                    }
                )
                notes.append(f"{ent_type} '{name}' removed in revision {doc_b.version}.")

        return {
            "doc_a_name": doc_a.filename,
            "doc_a_version": doc_a.version,
            "doc_b_name": doc_b.filename,
            "doc_b_version": doc_b.version,
            "summary": {
                "added": added_count,
                "modified": modified_count,
                "removed": removed_count,
                "unchanged": unchanged_count,
                "total_delta": added_count + modified_count + removed_count,
            },
            "diff_items": diff_items,
            "architectural_notes": notes,
        }


diff_engine = RevisionDiffEngine()
