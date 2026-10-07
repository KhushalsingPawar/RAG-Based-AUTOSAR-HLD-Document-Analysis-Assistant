import streamlit as st
import requests
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8000"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AUTOSAR HLD Assistant",
    page_icon="🚗",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "document_id" not in st.session_state:
    st.session_state.document_id = None

if "filename" not in st.session_state:
    st.session_state.filename = None

if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []


# ============================================================
# HEADER
# ============================================================

st.title("🚗 AUTOSAR HLD Document Analysis Assistant")

st.markdown(
    """
AI-assisted analysis of AUTOSAR High-Level Design documents.

**Upload → Extract → Search → Analyze → Validate → Compare**
"""
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "📄 Upload HLD",
        "📊 Document Summary",
        "🧩 AUTOSAR Entities",
        "🔍 RAG Question Answering",
        "⚖️ Compare HLD Versions",
        "⚠️ Validation"
    ]
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def upload_document(uploaded_file):

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf"
        )
    }

    try:

        response = requests.post(
            f"{BACKEND_URL}/api/documents/upload",
            files=files,
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "Backend is not running. "
            "Start FastAPI using: "
            "`uvicorn app.main:app --reload`"
        )

        return None

    except requests.exceptions.RequestException as error:

        st.error(
            f"Upload failed: {error}"
        )

        return None


def get_document_report(document_id):

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/documents/report",
            params={
                "document_id": document_id
            },
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException:

        return None


def ask_question(
    question,
    top_k=5,
    document_id=None
):

    payload = {
        "question": question,
        "top_k": top_k
    }

    if document_id:

        payload["document_id"] = document_id

    try:

        response = requests.post(
            f"{BACKEND_URL}/api/documents/ask",
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        st.error(
            f"Question answering failed: {error}"
        )

        return None


def compare_documents(
    old_document_id,
    new_document_id
):

    payload = {
        "old_document_id": old_document_id,
        "new_document_id": new_document_id
    }

    try:

        response = requests.post(
            f"{BACKEND_URL}/api/documents/compare",
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        st.error(
            f"Comparison failed: {error}"
        )

        return None


def validate_document(document_id):

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/documents/validate/{document_id}",
            timeout=60
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        st.error(
            f"Validation failed: {error}"
        )

        return None


# ============================================================
# PAGE 1 — UPLOAD
# ============================================================

if page == "📄 Upload HLD":

    st.header("📄 Upload AUTOSAR HLD")

    uploaded_file = st.file_uploader(
        "Upload an HLD PDF",
        type=["pdf"]
    )

    if uploaded_file:

        st.info(
            f"Selected file: {uploaded_file.name}"
        )

        if st.button(
            "🚀 Analyze HLD",
            type="primary"
        ):

            with st.spinner(
                "Processing HLD document..."
            ):

                result = upload_document(
                    uploaded_file
                )

            if result:

                document_id = result.get(
                    "document_id"
                )

                st.session_state.document_id = (
                    document_id
                )

                st.session_state.filename = (
                    uploaded_file.name
                )

                document_record = {
                    "document_id": document_id,
                    "filename": uploaded_file.name
                }

                if document_record not in st.session_state.uploaded_documents:

                    st.session_state.uploaded_documents.append(
                        document_record
                    )

                st.success(
                    "HLD uploaded and analyzed successfully!"
                )

                st.subheader("Processing Result")

                # Get nested processing information
                chunks_info = result.get("chunks", {})
                embeddings_info = result.get("embeddings", {})

                total_chunks = chunks_info.get(
                    "total_chunks",
                    embeddings_info.get("total_chunks", 0)
                )

                embedding_dimension = embeddings_info.get(
                    "embedding_dimension",
                    0
                )

                embedding_model = embeddings_info.get(
                    "embedding_model",
                    "Unknown"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Pages",
                        result.get(
                            "total_pages",
                            0
                        )
                    )

                with col2:

                    st.metric(
                        "Chunks",
                        total_chunks
                    )

                with col3:

                    st.metric(
                        "Embedding Dimension",
                        embedding_dimension
                    )

                with col4:

                    st.metric(
                        "Entities",
                        sum(
                            len(value)
                            for value in result.get(
                                "entities",
                                {}
                            ).values()
                            if isinstance(value, list)
                        )
                    )

                st.caption(
                    f"Embedding Model: `{embedding_model}`"
                )

                st.success(
                    "HLD processing pipeline completed successfully."
                )

                st.code(
                    document_id
                )

                st.info(
                    "Save this Document ID for comparison and debugging."
                )

# ============================================================
# PAGE 2 — DOCUMENT SUMMARY
# ============================================================

elif page == "📊 Document Summary":

    st.header("📊 Document Summary")

    if not st.session_state.document_id:

        st.warning(
            "Upload an HLD document first."
        )

    else:

        report = get_document_report(
            st.session_state.document_id
        )

        if report:

            st.subheader(
                report.get(
                    "filename",
                    "Unknown document"
                )
            )

            summary = report.get(
                "summary",
                {}
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Pages",
                    report.get(
                        "total_pages",
                        0
                    )
                )

                st.metric(
                    "Components",
                    summary.get(
                        "software_components",
                        0
                    )
                )

            with col2:

                st.metric(
                    "Interfaces",
                    summary.get(
                        "interfaces",
                        0
                    )
                )

                st.metric(
                    "Ports",
                    summary.get(
                        "ports",
                        0
                    )
                )

            with col3:

                st.metric(
                    "Signals",
                    summary.get(
                        "signals",
                        0
                    )
                )

                st.metric(
                    "Dependencies",
                    summary.get(
                        "dependencies",
                        0
                    )
                )

            st.metric(
                "Functional Flows",
                summary.get(
                    "functional_flows",
                    0
                )
            )


# ============================================================
# PAGE 3 — AUTOSAR ENTITIES
# ============================================================

elif page == "🧩 AUTOSAR Entities":

    st.header("🧩 AUTOSAR Entities")

    if not st.session_state.document_id:

        st.warning(
            "Upload an HLD document first."
        )

    else:

        report = get_document_report(
            st.session_state.document_id
        )

        if report:

            entities = report.get(
                "entities",
                {}
            )

            entity_type = st.selectbox(
                "Select entity type",
                [
                    "software_components",
                    "interfaces",
                    "ports",
                    "signals",
                    "dependencies",
                    "functional_flows"
                ]
            )

            entity_data = entities.get(
                entity_type,
                []
            )

            st.write(
                f"Found **{len(entity_data)}** "
                f"{entity_type.replace('_', ' ')}."
            )

            if entity_data:

                dataframe = pd.DataFrame(
                    entity_data
                )

                st.dataframe(
                    dataframe,
                    use_container_width=True
                )

            else:

                st.info(
                    "No entities found."
                )


# ============================================================
# PAGE 4 — RAG QUESTION ANSWERING
# ============================================================

elif page == "🔍 RAG Question Answering":

    st.header("🔍 Ask Questions About HLD")

    if not st.session_state.document_id:

        st.warning(
            "Upload an HLD document first."
        )

    else:

        question = st.text_area(
            "Enter your AUTOSAR architecture question",
            placeholder=(
                "Example: Which component depends "
                "on SpeedSensor?"
            )
        )

        top_k = st.slider(
            "Number of retrieved sources",
            min_value=1,
            max_value=10,
            value=5
        )

        if st.button(
            "🔍 Ask Question",
            type="primary"
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                with st.spinner(
                    "Searching HLD and generating answer..."
                ):

                    result = ask_question(
                        question=question,
                        top_k=top_k,
                        document_id=(
                            st.session_state.document_id
                        )
                    )

                if result:

                    st.subheader(
                        "Answer"
                    )

                    st.success(
                        result.get(
                            "answer",
                            "No answer returned."
                        )
                    )

                    st.subheader(
                        "📚 Citations"
                    )

                    citations = result.get(
                        "citations",
                        []
                    )

                    if citations:

                        for citation in citations:

                            st.markdown(
                                f"- {citation}"
                            )

                    else:

                        st.info(
                            "No citations available."
                        )

                    with st.expander(
                        "View Retrieved Sources"
                    ):

                        sources = result.get(
                            "sources",
                            []
                        )

                        for source in sources:

                            st.markdown(
                                f"""
**Source {source.get('source_id')}**

- File: `{source.get('filename')}`
- Page: `{source.get('page_number')}`
- Section: `{source.get('section')}`
- Entity: `{source.get('entity_name')}`
- Distance: `{source.get('distance')}`
"""
                            )

                            st.code(
                                source.get(
                                    "content",
                                    ""
                                )
                            )


# ============================================================
# PAGE 5 — COMPARE HLD
# ============================================================

elif page == "⚖️ Compare HLD Versions":

    st.header("⚖️ Compare HLD Versions")

    documents = (
        st.session_state.uploaded_documents
    )

    if len(documents) < 2:

        st.warning(
            "Upload at least two HLD versions "
            "to compare them."
        )

    else:

        document_options = {
            document["filename"]:
            document["document_id"]
            for document in documents
        }

        old_filename = st.selectbox(
            "Old HLD Version",
            list(document_options.keys()),
            key="old_document"
        )

        new_filename = st.selectbox(
            "New HLD Version",
            list(document_options.keys()),
            key="new_document"
        )

        if st.button(
            "⚖️ Compare Versions",
            type="primary"
        ):

            if old_filename == new_filename:

                st.error(
                    "Old and new HLD must be different."
                )

            else:

                with st.spinner(
                    "Comparing HLD versions..."
                ):

                    result = compare_documents(
                        document_options[
                            old_filename
                        ],
                        document_options[
                            new_filename
                        ]
                    )

                if result:

                    comparison = result.get(
                        "comparison",
                        {}
                    )

                    for entity_type, data in comparison.items():

                        st.subheader(
                            entity_type.replace(
                                "_",
                                " "
                            ).title()
                        )

                        summary = data.get(
                            "summary",
                            {}
                        )

                        col1, col2, col3, col4 = (
                            st.columns(4)
                        )

                        with col1:

                            st.metric(
                                "Added",
                                summary.get(
                                    "added",
                                    0
                                )
                            )

                        with col2:

                            st.metric(
                                "Removed",
                                summary.get(
                                    "removed",
                                    0
                                )
                            )

                        with col3:

                            st.metric(
                                "Changed",
                                summary.get(
                                    "changed",
                                    0
                                )
                            )

                        with col4:

                            st.metric(
                                "Unchanged",
                                summary.get(
                                    "unchanged",
                                    0
                                )
                            )

                        if data.get("added"):

                            with st.expander(
                                "➕ Added"
                            ):

                                st.json(
                                    data["added"]
                                )

                        if data.get("removed"):

                            with st.expander(
                                "➖ Removed"
                            ):

                                st.json(
                                    data["removed"]
                                )

                        if data.get("changed"):

                            with st.expander(
                                "🔄 Changed"
                            ):

                                st.json(
                                    data["changed"]
                                )


# ============================================================
# PAGE 6 — VALIDATION
# ============================================================

elif page == "⚠️ Validation":

    st.header(
        "⚠️ HLD Validation & Inconsistency Detection"
    )

    if not st.session_state.document_id:

        st.warning(
            "Upload an HLD document first."
        )

    else:

        if st.button(
            "🔎 Run Validation",
            type="primary"
        ):

            with st.spinner(
                "Checking HLD for inconsistencies..."
            ):

                result = validate_document(
                    st.session_state.document_id
                )

            if result:

                validation = result.get(
                    "validation",
                    {}
                )

                total_issues = validation.get(
                    "total_issues",
                    0
                )

                severity_summary = validation.get(
                    "severity_summary",
                    {}
                )

                st.subheader(
                    "Validation Summary"
                )

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "Total Issues",
                        total_issues
                    )

                with col2:

                    st.metric(
                        "🔴 High",
                        severity_summary.get(
                            "HIGH",
                            0
                        )
                    )

                with col3:

                    st.metric(
                        "🟠 Medium",
                        severity_summary.get(
                            "MEDIUM",
                            0
                        )
                    )

                with col4:

                    st.metric(
                        "🟢 Low",
                        severity_summary.get(
                            "LOW",
                            0
                        )
                    )

                st.divider()

                issues = validation.get(
                    "issues",
                    []
                )

                if not issues:

                    st.success(
                        "No inconsistencies detected."
                    )

                else:

                    st.subheader(
                        "Detected Issues"
                    )

                    for index, issue in enumerate(
                        issues,
                        start=1
                    ):

                        severity = issue.get(
                            "severity",
                            "UNKNOWN"
                        )

                        issue_type = issue.get(
                            "type",
                            "UNKNOWN"
                        )

                        with st.expander(
                            f"{index}. "
                            f"{severity} — "
                            f"{issue_type}"
                        ):

                            st.write(
                                issue.get(
                                    "message",
                                    ""
                                )
                            )

                            st.json(issue)