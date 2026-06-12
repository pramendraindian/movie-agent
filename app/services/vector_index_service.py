from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from app.services.embedding_service import embed_texts
from app.utils.movie_utils import get_data_loader


@dataclass(frozen=True)
class IndexStats:
    total_movies: int
    indexed_movies: int


class VectorIndexService:
    def __init__(self) -> None:
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        import chromadb

        client = chromadb.PersistentClient(path=".chroma")
        self._collection = client.get_or_create_collection(
            name="movies",
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    def _movie_to_document(self, movie: Dict) -> str:
        return (
            f"Title: {movie.get('title', '')}\n"
            f"Genres: {movie.get('genres', '')}\n"
            f"Overview: {movie.get('overview', '')}\n"
            f"Keywords: {movie.get('keywords', '')}\n"
            f"Tagline: {movie.get('tagline', '')}"
        )

    def _movie_id(self, movie: Dict) -> str:
        base = f"{movie.get('id', '')}|{movie.get('title', '')}|{movie.get('release_date', '')}"
        digest = hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]
        return f"movie_{digest}"

    def build_index(self, rebuild: bool = False, limit: int | None = None) -> IndexStats:
        collection = self._get_collection()
        loader = get_data_loader()
        movies_df = loader.get_all_movies()

        if movies_df is None or movies_df.empty:
            return IndexStats(total_movies=0, indexed_movies=0)

        records: List[Dict] = movies_df.to_dict(orient="records")
        if limit and limit > 0:
            records = records[:limit]

        if rebuild:
            all_items = collection.get(include=[])
            existing_ids = all_items.get("ids", [])
            if existing_ids:
                collection.delete(ids=existing_ids)

        ids = [self._movie_id(movie) for movie in records]
        docs = [self._movie_to_document(movie) for movie in records]
        embeddings = embed_texts(docs)
        metadatas = [
            {
                "title": str(movie.get("title", "")),
                "genres": str(movie.get("genres", "")),
                "overview": str(movie.get("overview", "")),
                "poster_path": str(movie.get("poster_path", "")),
                "rating": float(movie.get("rating", 0.0) or 0.0),
                "runtime": float(movie.get("runtime", 0.0) or 0.0),
                "release_year": str(self._extract_release_year(movie)),
            }
            for movie in records
        ]

        collection.upsert(
            ids=ids,
            documents=docs,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return IndexStats(total_movies=len(records), indexed_movies=len(ids))

    def _extract_release_year(self, movie: Dict) -> str:
        release_date = movie.get("release_date")
        if release_date is None or release_date == "":
            return ""
        try:
            dt = pd.to_datetime(release_date, errors="coerce")
            return str(int(dt.year)) if pd.notna(dt) else ""
        except Exception:
            return ""


_vector_index_service = None


def get_vector_index_service() -> VectorIndexService:
    global _vector_index_service
    if _vector_index_service is None:
        _vector_index_service = VectorIndexService()
    return _vector_index_service
