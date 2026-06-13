"""Dense retrieval (RAG) over TMDB movie catalog using sentence embeddings."""

from __future__ import annotations

import os
from typing import Any

import numpy as np

_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_INDEX_PATH = os.getenv("RAG_INDEX_PATH", "app/data/rag_index.npz")


class MovieVectorStore:
    """Semantic movie index for RAG retrieval."""

    def __init__(self) -> None:
        self._model = None
        self._embeddings: np.ndarray | None = None
        self._movies: list[dict[str, Any]] = []
        self._ready = False

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(_EMBEDDING_MODEL)
        return self._model

    def _movie_document(self, movie: dict) -> str:
        parts = [
            movie.get("title", ""),
            movie.get("genres", ""),
            movie.get("overview", ""),
            movie.get("keywords", ""),
            movie.get("tagline", ""),
        ]
        return " ".join(str(p) for p in parts if p)

    def build_index(self, movies: list[dict]) -> None:
        if not movies:
            return

        self._movies = movies
        try:
            model = self._load_model()
            documents = [self._movie_document(m) for m in movies]
            embeddings = model.encode(documents, show_progress_bar=False, normalize_embeddings=True)
            self._embeddings = np.asarray(embeddings, dtype=np.float32)
            self._ready = True

            try:
                os.makedirs(os.path.dirname(_INDEX_PATH) or ".", exist_ok=True)
                np.savez_compressed(
                    _INDEX_PATH,
                    embeddings=self._embeddings,
                    titles=np.array([m.get("title", "") for m in movies]),
                )
            except OSError:
                pass
        except ImportError:
            print("sentence-transformers not installed — RAG will use keyword search fallback.")
            self._ready = True
            self._embeddings = None

    def _ensure_index(self) -> None:
        if self._ready:
            return

        from app.utils.movie_utils import get_recommendation_engine

        engine = get_recommendation_engine()
        if engine.movies_df is None or engine.movies_df.empty:
            return

        movies = engine._format_recommendations(engine.movies_df.index.tolist())
        self.build_index(movies)

    def retrieve(self, query: str, top_k: int = 8) -> list[dict]:
        self._ensure_index()
        if not self._ready:
            return []

        if self._embeddings is None:
            from app.utils.movie_utils import get_recommendation_engine

            return get_recommendation_engine().search_movies(query, top_k)

        model = self._load_model()
        query_vec = model.encode([query], normalize_embeddings=True)[0]
        scores = self._embeddings @ query_vec
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            movie = dict(self._movies[int(idx)])
            movie["rag_score"] = float(scores[int(idx)])
            results.append(movie)
        return results

    def retrieve_similar_to_title(self, title: str, top_k: int = 5) -> list[dict]:
        return self.retrieve(f"movies similar to {title} same genre mood style", top_k=top_k)


_vector_store: MovieVectorStore | None = None


def get_vector_store() -> MovieVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = MovieVectorStore()
    return _vector_store
