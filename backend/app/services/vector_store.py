import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from backend.app.config import settings


class VectorStoreService:
    """
    Manages vector embeddings and indexing using ChromaDB and SentenceTransformer (bge-small-en-v1.5).
    """

    def __init__(self):
        self._embedder = None
        self._client = None
        self._collection = None

    @property
    def embedder(self) -> SentenceTransformer:
        if self._embedder is None:
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return self._embedder

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        document_id: int,
        document_name: str,
        project_id: int,
        version: str,
        user_id: Optional[int] = None,
    ) -> int:
        if not chunks:
            return 0

        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedder.encode(texts, normalize_embeddings=True).tolist()

        ids = [f"doc_{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "project_id": project_id,
                "version": version,
                "user_id": user_id or 1,
                "page_number": chunk["page_number"],
                "section_title": chunk["section_title"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(ids)

    def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None,
        allowed_document_ids: Optional[List[int]] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        # If user has an allowed list of documents and it is empty, they have 0 documents
        if allowed_document_ids is not None and len(allowed_document_ids) == 0:
            return []

        # If a specific document is requested, ensure it is within allowed_document_ids
        if document_id is not None:
            if allowed_document_ids is not None and document_id not in allowed_document_ids:
                return []
            where_filter = {"document_id": document_id}
        elif allowed_document_ids is not None:
            if len(allowed_document_ids) == 1:
                where_filter = {"document_id": allowed_document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": allowed_document_ids}}
        elif project_id:
            where_filter = {"project_id": project_id}
        else:
            where_filter = None

        query_embedding = self.embedder.encode([query], normalize_embeddings=True).tolist()[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
        )

        retrieved: List[Dict[str, Any]] = []
        if results and results.get("ids") and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                text = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                # In cosine space in ChromaDB, distance = 1 - cosine_similarity
                distance = results["distances"][0][i] if "distances" in results else 0.5
                similarity = round(max(0.0, 1.0 - distance), 4)

                retrieved.append(
                    {
                        "chunk_id": doc_id,
                        "document_id": meta["document_id"],
                        "document_name": meta["document_name"],
                        "version": meta["version"],
                        "page_number": meta["page_number"],
                        "section_title": meta["section_title"],
                        "content": text,
                        "score": similarity,
                    }
                )

        return retrieved

    def delete_document_chunks(self, document_id: int):
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        count = self.collection.count()
        return {
            "total_indexed_chunks": count,
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
        }


vector_store = VectorStoreService()
