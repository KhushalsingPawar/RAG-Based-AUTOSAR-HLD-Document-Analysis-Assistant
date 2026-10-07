import chromadb


VECTOR_DB_PATH = "vector_db"

COLLECTION_NAME = "autosar_hld_chunks"


# Create persistent ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)


# Create or get collection
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)


def store_embeddings(
    embedded_chunks
):
    """
    Store document chunk embeddings
    inside ChromaDB.

    Each chunk contains:

    - chunk_id
    - document_id
    - filename
    - page_number
    - section
    - heading
    - entity_type
    - entity_name
    - content
    - source
    - embedding
    """

    if not embedded_chunks:
        return {
            "stored": 0,
            "collection": COLLECTION_NAME
        }

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in embedded_chunks:

        embedding = chunk.get(
            "embedding",
            []
        )

        if not embedding:
            continue

        chunk_id = chunk.get(
            "chunk_id"
        )

        ids.append(
            chunk_id
        )

        embeddings.append(
            embedding
        )

        documents.append(
            chunk.get(
                "content",
                ""
            )
        )

        metadata = {
            "document_id": chunk.get(
                "document_id",
                ""
            ),
            "filename": chunk.get(
                "filename",
                ""
            ),
            "page_number": chunk.get(
                "page_number",
                0
            ),
            "section": chunk.get(
                "section",
                ""
            ) or "",
            "heading": chunk.get(
                "heading",
                ""
            ) or "",
            "entity_type": chunk.get(
                "entity_type",
                ""
            ) or "",
            "entity_name": chunk.get(
                "entity_name",
                ""
            ) or "",
            "source": chunk.get(
                "source",
                ""
            )
        }

        metadatas.append(
            metadata
        )

    if not ids:
        return {
            "stored": 0,
            "collection": COLLECTION_NAME
        }

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    return {
        "stored": len(ids),
        "collection": COLLECTION_NAME
    }


def get_collection_count():
    """
    Return total number of vectors
    stored in ChromaDB.
    """

    return collection.count()


def get_collection_info():
    """
    Return basic vector database information.
    """

    return {
        "collection": COLLECTION_NAME,
        "count": collection.count()
    }

def search_similar_chunks(
    query_embedding,
    top_k=5,
    document_id=None
):
    """
    Search ChromaDB for the most relevant
    chunks using vector similarity.

    Args:
        query_embedding: Embedding of user question
        top_k: Number of results to retrieve
        document_id: Optional document filter

    Returns:
        List of relevant chunks with metadata.
    """

    if not query_embedding:
        return []

    query_arguments = {
        "query_embeddings": [query_embedding],
        "n_results": top_k
    }

    if document_id:
        query_arguments["where"] = {
            "document_id": document_id
        }

    results = collection.query(
        **query_arguments
    )

    retrieved_chunks = []

    result_ids = results.get(
        "ids",
        [[]]
    )[0]

    result_documents = results.get(
        "documents",
        [[]]
    )[0]

    result_metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    result_distances = results.get(
        "distances",
        [[]]
    )[0]

    for index in range(
        len(result_ids)
    ):

        metadata = (
            result_metadatas[index]
            if index < len(result_metadatas)
            else {}
        )

        document = (
            result_documents[index]
            if index < len(result_documents)
            else ""
        )

        distance = (
            result_distances[index]
            if index < len(result_distances)
            else None
        )

        retrieved_chunks.append({
            "chunk_id": result_ids[index],
            "content": document,
            "distance": distance,

            "document_id": metadata.get(
                "document_id"
            ),

            "filename": metadata.get(
                "filename"
            ),

            "page_number": metadata.get(
                "page_number"
            ),

            "section": metadata.get(
                "section"
            ),

            "heading": metadata.get(
                "heading"
            ),

            "entity_type": metadata.get(
                "entity_type"
            ),

            "entity_name": metadata.get(
                "entity_name"
            ),

            "source": metadata.get(
                "source"
            )
        })

    return retrieved_chunks