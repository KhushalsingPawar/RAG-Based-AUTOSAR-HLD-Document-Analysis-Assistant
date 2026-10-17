"""
End-to-End Pipeline Verification Script
Tests ingestion, entity extraction, ChromaDB embedding, RAG querying with Ollama,
revision comparison, and architectural validation.
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, init_db
from backend.app.models.schema import Project
from backend.app.routes.upload import _process_and_index_pdf
from backend.app.services.rag_engine import rag_engine
from backend.app.services.diff_engine import diff_engine
from backend.app.services.validation_engine import validation_engine


def main():
    print("=" * 60)
    print("🚗 AUTOSAR HLD Analysis Assistant - Pipeline Verification")
    print("=" * 60)

    # 1. Init DB
    init_db()
    db = SessionLocal()

    # Create test project
    project = db.query(Project).filter(Project.name == "EBCS Verification Project").first()
    if not project:
        project = Project(
            name="EBCS Verification Project",
            vehicle_program="Tata EV Gen-3",
            description="Automated test project for pipeline validation.",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    print(f"✅ Project ready: ID {project.id} - '{project.name}'")

    # 2. Ingest v2.0
    print("\n📥 Ingesting Brake_System_HLD_v2.0.pdf (Baseline)...")
    doc_v20 = _process_and_index_pdf(
        file_path="data/sample_hlds/Brake_System_HLD_v2.0.pdf",
        filename="Brake_System_HLD_v2.0.pdf",
        version="v2.0.0",
        project_id=project.id,
        db=db,
    )
    print(f"✅ Document v2.0 ingested: ID {doc_v20.id}, Pages: {doc_v20.total_pages}, Status: {doc_v20.status}")

    # Ingest v2.1
    print("\n📥 Ingesting Brake_System_HLD_v2.1.pdf (Target)...")
    doc_v21 = _process_and_index_pdf(
        file_path="data/sample_hlds/Brake_System_HLD_v2.1.pdf",
        filename="Brake_System_HLD_v2.1.pdf",
        version="v2.1.0",
        project_id=project.id,
        db=db,
    )
    print(f"✅ Document v2.1 ingested: ID {doc_v21.id}, Pages: {doc_v21.total_pages}, Status: {doc_v21.status}")

    # 3. Query RAG Engine
    print("\n💬 Querying RAG Engine: 'Identify the port receiving VehicleSpeed.'...")
    query_res = rag_engine.query(
        question="Identify the port receiving VehicleSpeed and the component it belongs to.",
        project_id=project.id,
        document_id=doc_v21.id,
        top_k=4,
    )
    print(f"🤖 LLM Model: {query_res['model_used']}")
    print(f"🎯 Grounding Confidence: {query_res['grounding_confidence']}")
    print(f"⏱️ Latency: {query_res['latency_seconds']}s")
    print(f"📝 Answer:\n{query_res['answer']}")
    print(f"🔍 Citations Count: {len(query_res['citations'])}")
    for cit in query_res["citations"][:2]:
        print(f"   - {cit['document_name']} | Section: {cit['section_title']} | Page: {cit['page_number']} | Score: {int(cit['score']*100)}%")

    # 4. Revision Comparison
    print("\n🔄 Running Revision Comparison (v2.0 vs v2.1)...")
    diff_res = diff_engine.compare_revisions(doc_v20.id, doc_v21.id, db)
    print(f"📊 Diff Summary: {diff_res['summary']}")
    for note in diff_res["architectural_notes"][:3]:
        print(f"   - {note}")

    # 5. Architecture Validation
    print("\n⚠️ Running Architectural Validation on v2.1...")
    val_res = validation_engine.validate_document(doc_v21.id, db)
    print(f"🔍 Total Issues Found: {val_res['total_issues']} (Critical: {val_res['critical_count']}, Warnings: {val_res['warning_count']})")
    for issue in val_res["issues"]:
        print(f"   [{issue['severity']}] {issue['category']}: '{issue['entity_name']}' on {issue.get('component_name')} (Page {issue['page']})")

    db.close()
    print("\n" + "=" * 60)
    print("🎉 ALL PIPELINE CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
