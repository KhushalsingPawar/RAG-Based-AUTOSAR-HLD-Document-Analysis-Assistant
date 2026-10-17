
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from frontend.components.api_client import APIClient, BACKEND_URL
from frontend.components.ui_helpers import inject_custom_css, render_citation
from frontend.components.auth_page import render_auth_page, render_user_sidebar_widget
st.set_page_config(
    page_title="AUTOSAR HLD Document Analysis Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

# ── Authentication Gate ──────────────────────────────────────────────────────
# If not logged in, render the login/register page and stop.
if not render_auth_page():
    st.stop()

# Build a token-aware API client from session state
client = APIClient(
    base_url=BACKEND_URL,
    token=st.session_state.get("auth_token"),
)

# Header (only shown after login)
st.markdown('<div class="main-header">🚗 AUTOSAR HLD Document Analysis Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Local-first AI Platform for Automotive Architecture Ingestion, Grounded RAG Tracing, and Verification</div>',
    unsafe_allow_html=True,
)

# Sidebar: System Context & Project Selector
st.sidebar.title("Configuration & Context")

health_status = client.get_health()
if health_status.get("status") == "Healthy":
    st.sidebar.success(f"🟢 Backend: Online (v{health_status.get('version', '1.0')})")
    ollama_info = health_status.get("ollama_service", "Unknown")
    if "Ready" in ollama_info:
        st.sidebar.info(f"🤖 LLM: {health_status.get('ollama_model')} ({ollama_info})")
    else:
        st.sidebar.warning(f"🤖 LLM: {ollama_info}")
    st.sidebar.caption(f"💾 Vector Store: {health_status.get('vector_store')}")
else:
    st.sidebar.error("🔴 Backend Service Offline. Ensure FastAPI is running on port 8000.")

st.sidebar.divider()

# Logged-in user info + logout
render_user_sidebar_widget()

# Project Selection
projects = client.get_projects()
if not projects:
    project_options = {1: "Default Workspace"}
    selected_project_id = 1
else:
    project_options = {p["id"]: f"{p['name']} ({p.get('vehicle_program', 'General')})" for p in projects}
    selected_project_id = st.sidebar.selectbox(
        "Active Project Context",
        options=list(project_options.keys()),
        format_func=lambda x: project_options[x],
    )

with st.sidebar.expander("➕ Create New Project"):
    new_proj_name = st.text_input("Project Name", placeholder="e.g. Battery Management", key="sidebar_new_proj_name")
    new_proj_prog = st.text_input("Vehicle Program", placeholder="e.g. Tata Curvv EV", key="sidebar_new_proj_prog")
    new_proj_desc = st.text_area("Description", placeholder="Architecture tracing for BMS", key="sidebar_new_proj_desc")
    if st.button("Create Project", use_container_width=True, key="sidebar_create_proj_btn"):
        if not new_proj_name.strip():
            st.error("Please enter a project name.")
        else:
            p_res = client.create_project(
                name=new_proj_name.strip(),
                vehicle_program=new_proj_prog.strip() or "General Automotive",
                description=new_proj_desc.strip(),
            )
            if "id" in p_res:
                st.sidebar.success(f"Project '{new_proj_name}' created!")
                st.rerun()
            else:
                st.sidebar.error(f"Error: {p_res.get('detail', 'Failed to create project')}")

documents = client.get_documents(project_id=selected_project_id)

st.sidebar.divider()
st.sidebar.markdown("### Quick Demo Setup")
st.sidebar.caption("Load synthetic AUTOSAR HLD documents into the active project:")
col_demo1, col_demo2 = st.sidebar.columns(2)
with col_demo1:
    if st.button("Load v2.0 (Base)", use_container_width=True):
        with st.spinner("Ingesting v2.0..."):
            res = client.load_sample_hld("Brake_System_HLD_v2.0.pdf", selected_project_id, "v2.0.0")
            st.sidebar.success("v2.0 Indexed!")
            st.rerun()
with col_demo2:
    if st.button("Load v2.1 (Target)", use_container_width=True):
        with st.spinner("Ingesting v2.1..."):
            res = client.load_sample_hld("Brake_System_HLD_v2.1.pdf", selected_project_id, "v2.1.0")
            st.sidebar.success("v2.1 Indexed!")
            st.rerun()

# Tabs
tab_dash, tab_ingest, tab_rag, tab_entities, tab_diff, tab_validate = st.tabs(
    [
        "📊 Dashboard",
        "📥 HLD Ingestion",
        "💬 Semantic RAG Assistant",
        "🧩 Entity Explorer",
        "🔄 Revision Diff",
        "⚠️ Architecture Validation",
    ]
)

# ----------------- TAB 1: DASHBOARD -----------------
with tab_dash:
    st.subheader("Architectural Knowledge Base Overview")
    
    total_docs = len(documents)
    all_entities = client.get_entities(project_id=selected_project_id)
    swc_count = sum(1 for e in all_entities if e["entity_type"] == "Component")
    port_count = sum(1 for e in all_entities if e["entity_type"] == "Port")
    signal_count = sum(1 for e in all_entities if e["entity_type"] == "Signal")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Indexed HLDs", total_docs)
    m2.metric("Software Components (SWC)", swc_count)
    m3.metric("AUTOSAR Ports", port_count)
    m4.metric("Traced Signals", signal_count)
    m5.metric("Total Cataloged Entities", len(all_entities))

    st.markdown("#### Document Specifications")
    if documents:
        doc_df = pd.DataFrame(
            [
                {
                    "ID": d["id"],
                    "Filename": d["filename"],
                    "Version": d["version"],
                    "Total Pages": d["total_pages"],
                    "File Size (KB)": d["file_size_kb"],
                    "Status": d["status"],
                    "Ingested Date": d["uploaded_at"][:10],
                }
                for d in documents
            ]
        )
        st.dataframe(doc_df, use_container_width=True)
    else:
        st.info("👋 Welcome! You don't have any HLD specifications in this project yet. Use the 'HLD Ingestion' tab to upload your files, or click 'Load v2.0' in the sidebar.")

# ----------------- TAB 2: INGESTION -----------------
with tab_ingest:
    st.subheader("Ingest New High-Level Design (HLD) Specification")

    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Upload AUTOSAR HLD Specification (PDF)", type=["pdf"])
    with col_up2:
        doc_version = st.text_input("Specification Version Tag", value="v1.0.0")

    if uploaded_file and st.button("Ingest & Index PDF", type="primary"):
        with st.spinner("Extracting text, chunking, extracting AUTOSAR entities, and generating vector embeddings..."):
            file_bytes = uploaded_file.read()
            res = client.upload_pdf(file_bytes, uploaded_file.name, selected_project_id, doc_version)
            if "document_id" in res:
                st.success(f"Successfully processed {uploaded_file.name} (Document ID: {res['document_id']})")
                st.rerun()
            else:
                st.error(f"Ingestion failed: {res.get('detail', 'Unknown error')}")

    # --- DELETE & MANAGE DOCUMENTS SECTION ---
    st.divider()
    st.subheader("🗑️ Delete & Manage Ingested Documents")
    st.caption("Permanently delete unneeded HLD specifications, their extracted entities, and vector embeddings from your workspace.")
    if documents:
        col_del_select, col_del_btn = st.columns([3, 1])
        with col_del_select:
            doc_to_delete = st.selectbox(
                "Select Document to Delete",
                options=documents,
                format_func=lambda d: f"{d['filename']} ({d['version']}) — ID: {d['id']} | {d['total_pages']} pages",
                key="doc_delete_selector",
            )
        with col_del_btn:
            st.write("")
            st.write("")
            confirm_del = st.checkbox("Confirm Deletion", key="confirm_doc_delete")

        if doc_to_delete:
            st.caption(f"⚠️ Selected for removal: **{doc_to_delete['filename']}** (ID: {doc_to_delete['id']}, Version: {doc_to_delete['version']})")
            if st.button("🗑️ Delete Selected Document", type="secondary", disabled=not confirm_del):
                with st.spinner(f"Deleting '{doc_to_delete['filename']}'..."):
                    del_res = client.delete_document(doc_to_delete["id"])
                    if "deleted_id" in del_res:
                        st.success(f"✅ {del_res.get('message', 'Document deleted successfully.')}")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete document: {del_res.get('detail', 'Unknown error')}")
    else:
        st.info("No documents are currently ingested in this project.")

    st.divider()
    st.subheader("Chunk Inspector")
    if documents:
        doc_to_inspect = st.selectbox(
            "Select Document to Inspect Chunks",
            options=documents,
            format_func=lambda d: f"{d['filename']} ({d['version']})",
        )
        if doc_to_inspect:
            chunks = client.get_document_chunks(doc_to_inspect["id"])
            st.caption(f"Total contextual chunks: {len(chunks)}")
            for c in chunks[:10]:
                with st.expander(f"Chunk #{c['chunk_index']} | Page {c['page_number']} | {c['section_title']}"):
                    st.text(c["content"])
    else:
        st.info("No documents available to inspect chunks.")

# ----------------- TAB 3: SEMANTIC RAG -----------------
with tab_rag:
    st.subheader("Grounded Architecture Question Answering (RAG)")
    st.caption("Ask natural language questions regarding signal flow, ports, interfaces, and component mappings.")

    if not documents:
        st.info("ℹ️ No documents ingested in this project yet. Ingest an HLD specification in the 'HLD Ingestion' tab or load sample documents in the sidebar to ask architectural questions.")

    # Preset Suggestions
    st.markdown("**Suggested Engineering Inquiries:**")
    preset_cols = st.columns(3)
    preset_q = None
    with preset_cols[0]:
        if st.button("Identify port receiving VehicleSpeed"):
            preset_q = "Identify the port receiving VehicleSpeed and the component it belongs to."
    with preset_cols[1]:
        if st.button("Which SWC calculates brake pressure?"):
            preset_q = "Which software component calculates target brake pressure and what are its interfaces?"
    with preset_cols[2]:
        if st.button("Diagnostic trigger at 1.4g deceleration"):
            preset_q = "What diagnostic action occurs if deceleration exceeds 1.4g without pressure build-up?"

    default_q = preset_q or "Identify the port receiving VehicleSpeed."
    user_query = st.text_input("Engineering Query:", value=default_q)

    col_q1, col_q2 = st.columns([1, 4])
    with col_q1:
        top_k_val = st.slider("Context Chunks (top_k)", 1, 8, 4)

    if st.button("Execute Tracing Query", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Retrieving semantic context from ChromaDB and reasoning via Ollama (llama3.2)..."):
                rag_res = client.query_rag(
                    question=user_query,
                    project_id=selected_project_id,
                    document_id=None,
                    top_k=top_k_val,
                )

                st.markdown("### Grounded Response")
                st.markdown(rag_res.get("answer", "No response generated."))

                # Metadata bar
                c_meta1, c_meta2, c_meta3 = st.columns(3)
                c_meta1.caption(f"⏱️ **Latency:** {rag_res.get('latency_seconds', 0.0)}s")
                c_meta2.caption(f"🧠 **Model:** {rag_res.get('model_used', 'Ollama')}")
                confidence = rag_res.get("grounding_confidence", "High")
                c_meta3.caption(f"🎯 **Grounding Confidence:** {confidence}")

                # Citations
                st.markdown("#### Evidence & Source Citations")
                citations = rag_res.get("citations", [])
                if citations:
                    for cit in citations:
                        render_citation(cit)
                else:
                    st.info("No citations retrieved.")

# ----------------- TAB 4: ENTITY EXPLORER -----------------
with tab_entities:
    st.subheader("Cataloged AUTOSAR Architecture Entities")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        type_filter = st.selectbox(
            "Filter Entity Type",
            options=["All", "Component", "Port", "Interface", "Signal"],
        )
    with col_f2:
        search_query = st.text_input("Search Entity Name", placeholder="e.g. SpeedProcessingSWC")
    with col_f3:
        doc_filter = st.selectbox(
            "Filter Document",
            options=[None] + documents,
            format_func=lambda d: "All Documents" if d is None else f"{d['filename']} ({d['version']})",
        )

    filt_type = None if type_filter == "All" else type_filter
    filt_doc_id = doc_filter["id"] if doc_filter else None

    entities_data = client.get_entities(
        document_id=filt_doc_id,
        project_id=selected_project_id,
        entity_type=filt_type,
        search=search_query if search_query.strip() else None,
    )

    if entities_data:
        ent_df = pd.DataFrame(
            [
                {
                    "Type": e["entity_type"],
                    "Name": e["name"],
                    "Parent Component": e["parent_component"] or "N/A",
                    "Port Direction": e["port_type"] or "N/A",
                    "Interface": e["interface_name"] or "N/A",
                    "Data Type": e["data_type"] or "N/A",
                    "Source Page": e["source_page"],
                    "Section": e["section_title"],
                }
                for e in entities_data
            ]
        )
        st.dataframe(ent_df, use_container_width=True)

        csv = ent_df.to_csv(index=False).encode("utf-8")
        st.download_button("Export Entities to CSV", csv, "autosar_entities.csv", "text/csv")
    else:
        st.info("No matching AUTOSAR entities found.")

# ----------------- TAB 5: REVISION DIFF -----------------
with tab_diff:
    st.subheader("Architectural Revision Comparison (HLD Diff Engine)")
    st.caption("Compare two HLD revisions to identify added, modified, and removed components, ports, and signals.")

    if len(documents) < 2:
        st.warning("At least two document revisions are required for comparison. Ingest or load v2.0 and v2.1 from the sidebar.")
    else:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            doc_a = st.selectbox("Baseline Revision (Version A)", options=documents, index=0, format_func=lambda d: f"{d['filename']} ({d['version']})")
        with col_d2:
            doc_b = st.selectbox("Target Revision (Version B)", options=documents, index=1 if len(documents) > 1 else 0, format_func=lambda d: f"{d['filename']} ({d['version']})")

        if doc_a["id"] == doc_b["id"]:
            st.info("Select two distinct document versions to compute the architectural delta.")
        else:
            if st.button("Run Revision Diff", type="primary"):
                with st.spinner("Computing delta across architectural entities..."):
                    diff_res = client.compare_revisions(doc_a["id"], doc_b["id"])

                    summary = diff_res.get("summary", {})
                    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                    c_s1.metric("Added Entities", summary.get("added", 0))
                    c_s2.metric("Modified Entities", summary.get("modified", 0))
                    c_s3.metric("Removed Entities", summary.get("removed", 0))
                    c_s4.metric("Unchanged Entities", summary.get("unchanged", 0))

                    st.markdown("#### Architectural Delta Log")
                    for note in diff_res.get("architectural_notes", []):
                        st.markdown(f"- {note}")

                    st.markdown("#### Detailed Entity Comparison")
                    diff_items = diff_res.get("diff_items", [])
                    if diff_items:
                        diff_df = pd.DataFrame(
                            [
                                {
                                    "Status": item["status"],
                                    "Type": item["entity_type"],
                                    "Name": item["name"],
                                    "Details": str(item["details"]),
                                }
                                for item in diff_items
                            ]
                        )
                        st.dataframe(diff_df, use_container_width=True)

# ----------------- TAB 6: VALIDATION -----------------
with tab_validate:
    st.subheader("Architectural Consistency & Inconsistency Checks")
    st.caption("Heuristic static verification for unassigned ports, dangling signals, and data type mismatches.")

    if not documents:
        st.info("Ingest an HLD specification first to run verification.")
    else:
        target_doc = st.selectbox("Select Specification to Validate", options=documents, format_func=lambda d: f"{d['filename']} ({d['version']})")

        if st.button("Execute Architectural Validation", type="primary"):
            with st.spinner("Analyzing component interfaces and port bindings..."):
                val_res = client.validate_document(target_doc["id"])

                passed = val_res.get("passed_audit", False)
                if passed:
                    st.success("✅ Specification Passed Architecture Audit: No critical unassigned ports or type conflicts detected.")
                else:
                    st.error(f"❌ Verification Warnings Detected ({val_res.get('critical_count', 0)} Critical, {val_res.get('warning_count', 0)} Warnings)")

                v1, v2, v3, v4 = st.columns(4)
                v1.metric("Total Issues", val_res.get("total_issues", 0))
                v2.metric("Critical", val_res.get("critical_count", 0))
                v3.metric("Warnings", val_res.get("warning_count", 0))
                v4.metric("Advisories (Info)", val_res.get("info_count", 0))

                issues = val_res.get("issues", [])
                if issues:
                    st.markdown("#### Identified Inconsistencies")
                    for issue in issues:
                        severity = issue["severity"]
                        badge = "badge-critical" if severity == "CRITICAL" else ("badge-warning" if severity == "WARNING" else "badge-component")
                        st.markdown(
                            f"""
                            <div class="card-container">
                                <span class="{badge}">{severity}</span> &nbsp;
                                <b>{issue['category']}:</b> <code>{issue['entity_name']}</code> 
                                (Component: <b>{issue.get('component_name', 'N/A')}</b> | Page: <b>{issue['page']}</b>)
                                <p style="margin-top: 6px; margin-bottom: 4px;">{issue['description']}</p>
                                <p style="color: #1E40AF; font-size: 0.9rem; margin-bottom: 0;"><b>Remediation:</b> {issue['recommendation']}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No architectural warnings found in this document revision.")
