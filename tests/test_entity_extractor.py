from backend.app.services.entity_extractor import entity_extractor


def test_entity_extraction():
    fake_pages = [
        {
            "page_number": 2,
            "text": """
            Component: SpeedProcessingSWC
            - Provide-Port: P_SpeedReceiver
              Interface: VehicleSpeed_IF
              Transmitted Signal: VehicleSpeed
              Data Type: uint16
            """,
            "active_section": "4. Component Specification",
        }
    ]

    entities = entity_extractor.extract_from_pages(fake_pages, document_id=1)
    entity_names = {e["name"] for e in entities}
    entity_types = {e["entity_type"] for e in entities}

    assert "SpeedProcessingSWC" in entity_names
    assert "P_SpeedReceiver" in entity_names
    assert "VehicleSpeed_IF" in entity_names
    assert "VehicleSpeed" in entity_names

    assert "Component" in entity_types
    assert "Port" in entity_types
    assert "Interface" in entity_types
    assert "Signal" in entity_types

    # Check port attributes
    port = next(e for e in entities if e["name"] == "P_SpeedReceiver")
    assert port["port_type"] == "Provide-Port"
    assert port["parent_component"] == "SpeedProcessingSWC"

    # Check signal data type
    signal = next(e for e in entities if e["name"] == "VehicleSpeed")
    assert signal["data_type"] == "uint16"
