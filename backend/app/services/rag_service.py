from app.services.retrieval_service import (
    retrieve_relevant_chunks
)

from app.services.llm_service import (
    generate_llm_response
)


def build_context(chunks):
    context_parts = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):
        context_parts.append(
            f"""
SOURCE {index}

Filename:
{chunk.get("filename", "")}

Page:
{chunk.get("page_number", "")}

Section:
{chunk.get("section", "")}

Entity Type:
{chunk.get("entity_type", "")}

Entity Name:
{chunk.get("entity_name", "")}

Content:
{chunk.get("content", "")}

Source:
{chunk.get("source", "")}
""".strip()
        )

    return "\n\n".join(context_parts)


def build_rag_prompt(question: str, context: str):
    return f"""
You are an AUTOSAR High-Level Design analysis assistant.

Answer the user's question using ONLY the provided HLD context.

RULES:

1. Use only information present in the context.
2. Give a clear explanatory answer, not just a keyword or entity name.
3. Answer in 2-4 complete sentences when the question requires explanation.
4. Include the relevant relationship between components, ports, interfaces,
   signals, dependencies, or functional flows.
5. If the context contains a sequence or relationship, explain that sequence.
6. Do not invent information.
7. If the answer cannot be found in the context, say:

"The information is not available in the provided HLD context."

8. Do not create citations yourself.
9. Do not mention information that is not supported by the context.

HLD CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
""".strip()


def build_sources(chunks):
    sources = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):
        sources.append({
            "source_id": index,
            "chunk_id": chunk.get("chunk_id"),
            "filename": chunk.get("filename"),
            "page_number": chunk.get("page_number"),
            "section": chunk.get("section"),
            "heading": chunk.get("heading"),
            "entity_type": chunk.get("entity_type"),
            "entity_name": chunk.get("entity_name"),
            "source": chunk.get("source"),
            "distance": chunk.get("distance")
        })

    return sources


def build_citation(source):
    filename = source.get("filename") or "Unknown document"
    page_number = source.get("page_number") or "Unknown page"

    section = (
        source.get("section")
        or source.get("heading")
        or "Unknown section"
    )

    return (
        f"[{source.get('source_id')}] "
        f"{filename} — "
        f"Page {page_number} — "
        f"Section: {section}"
    )


def build_citations(sources):
    citations = []

    seen = set()

    for source in sources:
        citation = build_citation(source)

        if citation in seen:
            continue

        seen.add(citation)

        citations.append(citation)

    return citations


def ask_rag_question(
    question: str,
    top_k: int = 5,
    document_id: str = None
):
    chunks = retrieve_relevant_chunks(
        query=question,
        top_k=top_k,
        document_id=document_id
    )

    if not chunks:
        return {
            "answer": (
                "The information is not available "
                "in the provided HLD context."
            ),
            "sources": [],
            "citations": []
        }

    context = build_context(chunks)

    prompt = build_rag_prompt(
        question=question,
        context=context
    )

    answer = generate_llm_response(
        prompt
    )

    sources = build_sources(chunks)

    citations = build_citations(
        sources
    )

    return {
        "answer": answer,
        "sources": sources,
        "citations": citations
    }