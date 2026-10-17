from backend.app.services.validation_engine import validation_engine
from backend.app.services.diff_engine import diff_engine
from backend.app.models.schema import Document, AutosarEntity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base


def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_validation_engine_detects_unassigned_port():
    db = setup_in_memory_db()

    doc = Document(id=1, project_id=1, filename="Test.pdf", file_path="fake/path", version="v1.0")
    db.add(doc)
    db.commit()

    # Add an unassigned port
    port = AutosarEntity(
        document_id=1,
        entity_type="Port",
        name="R_ExternalInertiaSensor",
        port_type="Require-Port",
        parent_component="DiagnosticMonitorSWC",
        description="Unassigned port without matching provider",
        source_page=4,
    )
    db.add(port)
    db.commit()

    report = validation_engine.validate_document(1, db)
    assert report["total_issues"] >= 1
    assert any(i["category"] == "Unassigned Port" for i in report["issues"])
    assert report["passed_audit"] is False


def test_diff_engine_detects_added_component():
    db = setup_in_memory_db()

    doc_a = Document(id=1, project_id=1, filename="Doc_v1.pdf", file_path="fake/v1", version="v1.0")
    doc_b = Document(id=2, project_id=1, filename="Doc_v2.pdf", file_path="fake/v2", version="v2.0")
    db.add_all([doc_a, doc_b])
    db.commit()

    # Baseline has SpeedProcessingSWC
    e_a = AutosarEntity(document_id=1, entity_type="Component", name="SpeedProcessingSWC", source_page=2)
    # Target has SpeedProcessingSWC + RegenBrakeCoordinatorSWC
    e_b1 = AutosarEntity(document_id=2, entity_type="Component", name="SpeedProcessingSWC", source_page=2)
    e_b2 = AutosarEntity(document_id=2, entity_type="Component", name="RegenBrakeCoordinatorSWC", source_page=2)
    db.add_all([e_a, e_b1, e_b2])
    db.commit()

    diff = diff_engine.compare_revisions(1, 2, db)
    assert diff["summary"]["added"] == 1
    assert diff["summary"]["unchanged"] == 1
    assert any(item["name"] == "RegenBrakeCoordinatorSWC" and item["status"] == "Added" for item in diff["diff_items"])
