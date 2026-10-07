from app.services.embedding_service import (
    generate_embedding
)

from app.services.vector_service import (
    search_similar_chunks
)


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    document_id: str = None
):
    """
    Convert the user query into an embedding
    and retrieve the most relevant chunks
    from ChromaDB.
    """

    if not query or not query.strip():
        return []

    query = query.strip()

    # Step 1: Generate embedding for question
    query_embedding = generate_embedding(
        query
    )

    if not query_embedding:
        return []

    # Step 2: Search vector database
    chunks = search_similar_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
        document_id=document_id
    )

    return chunks