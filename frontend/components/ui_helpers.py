import streamlit as st
from typing import Any


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Modern Automotive Engineering Theme */
        .main-header {
            font-size: 2.1rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #4B5563;
            margin-bottom: 1.5rem;
        }
        .card-container {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
        }
        .badge-component {
            background-color: #DBEAFE;
            color: #1E40AF;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-port-p {
            background-color: #D1FAE5;
            color: #065F46;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-port-r {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-signal {
            background-color: #EDE9FE;
            color: #5B21B6;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-critical {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .badge-warning {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .citation-box {
            border-left: 4px solid #3B82F6;
            background-color: #F0F9FF;
            padding: 10px 14px;
            margin-top: 8px;
            border-radius: 0 6px 6px 0;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: Any, delta: str = None, help_text: str = None):
    st.metric(label=title, value=value, delta=delta, help=help_text)


def render_citation(cit: dict):
    doc_name = cit.get("document_name", "HLD Document")
    ver = cit.get("version", "1.0")
    sec = cit.get("section_title", "General")
    page = cit.get("page_number", 1)
    score = int(cit.get("score", 0.0) * 100)
    content = cit.get("content", "")

    st.markdown(
        f"""
        <div class="citation-box">
            <b>Source Citation:</b> {doc_name} (v{ver}) &nbsp;|&nbsp; 
            <b>Section:</b> {sec} &nbsp;|&nbsp; 
            <b>Page:</b> <span class="badge-component">Page {page}</span> &nbsp;|&nbsp; 
            <b>Relevance:</b> {score}%
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(f"View Retrieved Excerpt (Page {page})"):
        st.code(content, language="markdown")
