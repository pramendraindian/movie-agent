"""Vision understanding for movie poster images using CLIP embeddings."""

from __future__ import annotations

import base64
import io
import os
from typing import Any

import numpy as np
from PIL import Image

_CLIP_MODEL = os.getenv("VISION_MODEL", "clip-ViT-B-32")


class VisionService:
    """Identify movies from poster images and find visually similar titles."""

    def __init__(self) -> None:
        self._model = None
        self._poster_embeddings: np.ndarray | None = None
        self._poster_movies: list[dict] = []
        self._index_ready = False

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(_CLIP_MODEL)
        return self._model

    def _ensure_poster_index(self) -> None:
        if self._index_ready:
            return

        from app.utils.movie_utils import get_recommendation_engine

        engine = get_recommendation_engine()
        if engine.movies_df is None or engine.movies_df.empty:
            return

        movies_with_posters = []
        for idx in engine.movies_df.index:
            row = engine.movies_df.loc[idx]
            poster = str(row.get("poster_path", "") or "").strip()
            if not poster or poster.lower() in {"nan", "none"}:
                continue
            movies_with_posters.append(engine._format_recommendations([idx])[0])
            if len(movies_with_posters) >= 150:
                break

        if not movies_with_posters:
            return

        model = self._load_model()
        urls = [
            f"https://image.tmdb.org/t/p/w342{m['poster_path']}"
            for m in movies_with_posters
        ]
        embeddings = []
        valid_movies = []
        for movie, url in zip(movies_with_posters, urls):
            try:
                emb = model.encode(Image.open(io.BytesIO(self._fetch_image(url))))
                embeddings.append(emb)
                valid_movies.append(movie)
            except Exception:
                continue

        if embeddings:
            self._poster_embeddings = np.asarray(embeddings, dtype=np.float32)
            norms = np.linalg.norm(self._poster_embeddings, axis=1, keepdims=True)
            self._poster_embeddings = self._poster_embeddings / np.clip(norms, 1e-9, None)
            self._poster_movies = valid_movies
            self._index_ready = True

    def _fetch_image(self, url: str) -> bytes:
        import requests

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.content

    def _decode_image(self, image_base64: str) -> Image.Image:
        raw = image_base64
        if "," in raw:
            raw = raw.split(",", 1)[1]
        data = base64.b64decode(raw)
        return Image.open(io.BytesIO(data)).convert("RGB")

    def analyze_poster(self, image_base64: str, top_k: int = 5) -> dict[str, Any]:
        """Match uploaded poster to catalog and infer recommendation intent."""
        try:
            self._ensure_poster_index()
            model = self._load_model()
            image = self._decode_image(image_base64)
            query_emb = np.asarray(model.encode(image), dtype=np.float32)
            query_emb = query_emb / max(np.linalg.norm(query_emb), 1e-9)
        except ImportError:
            return {
                "intent": "movie_recommendation",
                "matched_title": "",
                "confidence": 0.0,
                "inferred_genre": "drama",
                "similar_movies": [],
                "message": "Vision model unavailable. Install sentence-transformers for poster understanding.",
            }
        except Exception as exc:
            return {
                "intent": "movie_recommendation",
                "matched_title": "",
                "confidence": 0.0,
                "inferred_genre": "drama",
                "similar_movies": [],
                "message": f"Could not analyze poster: {exc}",
            }

        intent = "movie_recommendation"
        matched_title = ""
        confidence = 0.0
        similar: list[dict] = []

        if self._poster_embeddings is not None and len(self._poster_movies) > 0:
            scores = self._poster_embeddings @ query_emb
            order = np.argsort(scores)[::-1][:top_k]
            similar = []
            for idx in order:
                movie = dict(self._poster_movies[int(idx)])
                score = float(scores[int(idx)])
                movie["visual_score"] = score
                similar.append(movie)
            if similar:
                matched_title = similar[0].get("title", "")
                confidence = similar[0].get("visual_score", 0.0)

        text_probe = model.encode(["action blockbuster poster", "romantic comedy poster", "horror thriller poster"])
        image_emb = query_emb
        mood_labels = ["action", "comedy", "horror"]
        mood_scores = text_probe @ image_emb
        dominant_mood_idx = int(np.argmax(mood_scores))
        inferred_genre = mood_labels[dominant_mood_idx]

        return {
            "intent": intent,
            "matched_title": matched_title,
            "confidence": confidence,
            "inferred_genre": inferred_genre,
            "similar_movies": similar,
            "message": (
                f"I analyzed the poster"
                + (f" — it looks like **{matched_title}**" if matched_title else "")
                + f" with a {inferred_genre} vibe."
            ),
        }


_vision_service: VisionService | None = None


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
