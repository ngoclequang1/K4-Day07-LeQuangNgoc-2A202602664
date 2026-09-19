from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    An in-memory vector store for text chunks.

    Each Document is stored as one chunk; callers perform chunking beforehand.
    The embedding_fn parameter allows injection of mock or real embeddings.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._store: list[dict[str, Any]] = []

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = deepcopy(doc.metadata)
        # A chunk may already identify its original file through metadata.
        metadata.setdefault("doc_id", doc.id)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        ranked = [(_dot(query_embedding, record["embedding"]), record) for record in records]
        # Python's stable sort keeps insertion order when scores are equal.
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": deepcopy(record["metadata"]),
                "score": score,
            }
            for score, record in ranked[:top_k]
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed and append each document as one record without changing its metadata.
        """
        for doc in docs:
            self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        Scores are dot products (equivalent to cosine for normalized embeddings).
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)
        candidates = [
            record
            for record in self._store
            if all(
                key in record["metadata"] and record["metadata"][key] == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        previous_size = len(self._store)
        self._store = [record for record in self._store if record["metadata"]["doc_id"] != doc_id]
        return len(self._store) < previous_size
