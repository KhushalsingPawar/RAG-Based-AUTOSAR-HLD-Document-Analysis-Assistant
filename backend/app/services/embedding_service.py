from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# Embedding Model Configuration
# ---------------------------------------------------------

MODEL_NAME = "BAAI/bge-small-en-v1.5"


# Load model once when the application starts.
embedding_model = SentenceTransformer(
    MODEL_NAME
)


# ---------------------------------------------------------
# Generate embedding for one text
# ---------------------------------------------------------

def generate_embedding(text: str):
    """
    Convert text into a numerical embedding vector.

    Returns:
        list[float]
    """

    if not text or not text.strip():
        return []

    embedding = embedding_model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


# ---------------------------------------------------------
# Generate embeddings for multiple chunks
# ---------------------------------------------------------

def generate_chunk_embeddings(chunks):
    """
    Generate embeddings for all document chunks.

    Existing chunk metadata is preserved.

    Returns:
        List of chunks containing:
        - original metadata
        - embedding
        - embedding_dimension
    """

    embedded_chunks = []

    for chunk in chunks:

        content = chunk.get(
            "content",
            ""
        )

        embedding = generate_embedding(
            content
        )

        embedded_chunk = {
            **chunk,

            "embedding": embedding,

            "embedding_dimension": len(
                embedding
            )
        }

        embedded_chunks.append(
            embedded_chunk
        )

    return embedded_chunks


# ---------------------------------------------------------
# Generate embeddings for complete document
# ---------------------------------------------------------

def generate_document_embeddings(
    section_chunks,
    entity_chunks
):
    """
    Generate embeddings for both:

    1. Section chunks
    2. Entity chunks
    """

    embedded_section_chunks = (
        generate_chunk_embeddings(
            section_chunks
        )
    )

    embedded_entity_chunks = (
        generate_chunk_embeddings(
            entity_chunks
        )
    )

    all_chunks = (
        embedded_section_chunks
        + embedded_entity_chunks
    )

    return {
        "section_chunks": embedded_section_chunks,

        "entity_chunks": embedded_entity_chunks,

        "total_chunks": len(
            all_chunks
        ),

        "embedding_model": MODEL_NAME,

        "embedding_dimension": (
            len(all_chunks[0]["embedding"])
            if all_chunks
            else 0
        )
    }