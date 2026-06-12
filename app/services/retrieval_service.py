from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from app.services.embedding_service import embed_texts
from app.services.rag_config import get_rag_config


class RetrieverBackend(str, Enum):
    CHROMA = "chroma"


@dataclass(frozen=True)
class RetrievedMovie:
    title: str
    genres: str
    overview: str
    rating: float
    runtime: str
    release_year: str
    poster_path: str
    similarity: float


def _to_runtime_string(runtime_value) -> str:
    try:
        runtime_int = int(float(runtime_value))
        return f"{runtime_int} min" if runtime_int > 0 else ""
    except (TypeError, ValueError):
        return ""


class ChromaRetriever:
    def __init__(self) -> None:
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        import chromadb

        persistent_client = chromadb.PersistentClient(path=".chroma")
        self._collection = persistent_client.get_or_create_collection(
            name="movies",
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def retrieve(self, query: str, top_k: int) -> List[RetrievedMovie]:
        collection = self._get_collection()
        query_embedding = embed_texts([query])[0]
        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            include=["metadatas", "distances"],
        )

        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]

        results: List[RetrievedMovie] = []
        for metadata, distance in zip(metadatas, distances):
            similarity = max(0.0, min(1.0, 1.0 - float(distance)))
            results.append(
                RetrievedMovie(
                    title=str(metadata.get("title", "Unknown")),
                    genres=str(metadata.get("genres", "")),
                    overview=str(metadata.get("overview", "")),
                    rating=float(metadata.get("rating", 0.0) or 0.0),
                    runtime=_to_runtime_string(metadata.get("runtime", "")),
                    release_year=str(metadata.get("release_year", "")),
                    poster_path=str(metadata.get("poster_path", "")),
                    similarity=similarity,
                )
            )
        return results


class RetrievalService:
    def __init__(self) -> None:
        self._retriever = None

    def _get_retriever(self):
        if self._retriever is not None:
            return self._retriever

        config = get_rag_config()
        if config.retrieval_backend != RetrieverBackend.CHROMA.value:
            raise ValueError(
                f"Unsupported retrieval backend: {config.retrieval_backend}"
            )
        self._retriever = ChromaRetriever()
        return self._retriever

    def retrieve(self, query: str, top_k: int | None = None) -> List[RetrievedMovie]:
        config = get_rag_config()
        if not query.strip():
            return []

        k = top_k if top_k is not None else config.retrieval_top_k

        try:
            retriever = self._get_retriever()
            retrieved = retriever.retrieve(query, k)
            return [
                item
                for item in retrieved
                if item.similarity >= config.retrieval_similarity_cutoff
            ]
        except Exception as exc:
            print(f"[RAG:retrieve] fallback due to error: {exc}")
            return []


_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
