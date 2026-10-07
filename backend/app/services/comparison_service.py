def entity_key(entity):
    """
    Creates a unique key for an entity.
    The entity name is used as the primary identifier.
    """

    if "name" in entity:
        return entity.get("name")

    if "source" in entity and "target" in entity:
        return (
            f"{entity.get('source')}"
            f" -> "
            f"{entity.get('target')}"
        )

    return None


def normalize_value(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def compare_entity_lists(
    old_entities,
    new_entities
):
    old_map = {}
    new_map = {}

    for entity in old_entities:
        key = entity_key(entity)

        if key:
            old_map[key] = entity

    for entity in new_entities:
        key = entity_key(entity)

        if key:
            new_map[key] = entity

    added = []
    removed = []
    changed = []
    unchanged = []

    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    common_keys = old_keys & new_keys

    for key in sorted(added_keys):
        added.append(new_map[key])

    for key in sorted(removed_keys):
        removed.append(old_map[key])

    for key in sorted(common_keys):

        old_entity = old_map[key]
        new_entity = new_map[key]

        differences = {}

        all_fields = (
            set(old_entity.keys())
            | set(new_entity.keys())
        )

        for field in all_fields:

            old_value = old_entity.get(field)
            new_value = new_entity.get(field)

            if normalize_value(old_value) != normalize_value(
                new_value
            ):
                differences[field] = {
                    "old": old_value,
                    "new": new_value
                }

        if differences:
            changed.append({
                "key": key,
                "old": old_entity,
                "new": new_entity,
                "changes": differences
            })
        else:
            unchanged.append(new_entity)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(unchanged)
        }
    }


def compare_documents(
    old_document,
    new_document
):
    old_entities = old_document.get(
        "entities",
        {}
    )

    new_entities = new_document.get(
        "entities",
        {}
    )

    entity_types = [
        "software_components",
        "interfaces",
        "ports",
        "signals",
        "dependencies",
        "functional_flows"
    ]

    comparison = {}

    for entity_type in entity_types:

        old_list = old_entities.get(
            entity_type,
            []
        )

        new_list = new_entities.get(
            entity_type,
            []
        )

        comparison[entity_type] = compare_entity_lists(
            old_list,
            new_list
        )

    return {
        "old_document": {
            "document_id": old_document.get(
                "document_id"
            ),
            "filename": old_document.get(
                "filename"
            ),
            "total_pages": old_document.get(
                "total_pages"
            )
        },
        "new_document": {
            "document_id": new_document.get(
                "document_id"
            ),
            "filename": new_document.get(
                "filename"
            ),
            "total_pages": new_document.get(
                "total_pages"
            )
        },
        "comparison": comparison
    }