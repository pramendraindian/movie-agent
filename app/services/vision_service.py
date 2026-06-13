"""Vision understanding for movie poster images using CLIP embeddings."""

from __future__ import annotations

import base64
import io
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import numpy as np
from PIL import Image

_CLIP_MODEL = os.getenv("VISION_MODEL", "clip-ViT-B-32")
_POSTER_INDEX_SIZE = int(os.getenv("VISION_POSTER_INDEX_SIZE", "40"))
_INDEX_PATH = os.getenv("VISION_INDEX_PATH", "app/data/vision_poster_index.npz")
_MOVIES_PATH = os.getenv("VISION_MOVIES_PATH", "app/data/vision_poster_movies.json")
_FETCH_WORKERS = int(os.getenv("VISION_FETCH_WORKERS", "8"))
_FETCH_TIMEOUT = int(os.getenv("VISION_FETCH_TIMEOUT", "5"))


class VisionService:
    """Identify movies from poster images and find visually similar titles."""

    def __init__(self) -> None:
        self._model = None
        self._poster_embeddings: np.ndarray | None = None
        self._poster_movies: list[dict] = []
        self._index_ready = False
        self._index_building = False
        self._lock = threading.Lock()

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            print(f"Loading vision model {_CLIP_MODEL}...")
            self._model = SentenceTransformer(_CLIP_MODEL)
        return self._model

    def _load_cached_index(self) -> bool:
        if not os.path.exists(_INDEX_PATH) or not os.path.exists(_MOVIES_PATH):
            return False
        try:
            data = np.load(_INDEX_PATH)
            embeddings = data["embeddings"]
            with open(_MOVIES_PATH, encoding="utf-8") as f:
                movies = json.load(f)
            if len(movies) == 0 or len(embeddings) == 0:
                return False
            self._poster_embeddings = np.asarray(embeddings, dtype=np.float32)
            self._poster_movies = movies
            self._index_ready = True
            print(f"✓ Loaded cached poster index ({len(movies)} movies)")
            return True
        except Exception as exc:
            print(f"Could not load cached poster index: {exc}")
            return False

    def _save_cached_index(self) -> None:
        if self._poster_embeddings is None or not self._poster_movies:
            return
        try:
            os.makedirs(os.path.dirname(_INDEX_PATH) or ".", exist_ok=True)
            np.savez_compressed(_INDEX_PATH, embeddings=self._poster_embeddings)
            with open(_MOVIES_PATH, "w", encoding="utf-8") as f:
                json.dump(self._poster_movies, f)
        except OSError as exc:
            print(f"Could not save poster index cache: {exc}")

    def _fetch_image(self, url: str) -> bytes | None:
        import requests

        try:
            resp = requests.get(url, timeout=_FETCH_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None

    def _download_posters(
        self, movies: list[dict]
    ) -> list[tuple[dict, Image.Image]]:
        tasks = {
            f"https://image.tmdb.org/t/p/w342{m['poster_path']}": m
            for m in movies
            if m.get("poster_path")
        }
        results: list[tuple[dict, Image.Image]] = []

        with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as pool:
            future_map = {
                pool.submit(self._fetch_image, url): (url, movie)
                for url, movie in tasks.items()
            }
            for future in as_completed(future_map):
                url, movie = future_map[future]
                raw = future.result()
                if not raw:
                    continue
                try:
                    image = Image.open(io.BytesIO(raw)).convert("RGB")
                    results.append((movie, image))
                except Exception:
                    continue
        return results

    def _build_poster_index(self) -> None:
        with self._lock:
            if self._index_ready or self._index_building:
                return
            self._index_building = True

        try:
            if self._load_cached_index():
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
                if len(movies_with_posters) >= _POSTER_INDEX_SIZE:
                    break

            if not movies_with_posters:
                return

            print(f"Building poster index ({len(movies_with_posters)} posters)...")
            model = self._load_model()
            downloaded = self._download_posters(movies_with_posters)
            if not downloaded:
                print("Poster index build failed: no posters downloaded.")
                return

            images = [img for _, img in downloaded]
            embeddings = model.encode(images, batch_size=16, show_progress_bar=False)
            embeddings = np.asarray(embeddings, dtype=np.float32)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, 1e-9, None)

            self._poster_embeddings = embeddings
            self._poster_movies = [movie for movie, _ in downloaded]
            self._index_ready = True
            self._save_cached_index()
            print(f"✓ Poster index ready ({len(self._poster_movies)} movies)")
        finally:
            self._index_building = False

    def _ensure_poster_index(self) -> None:
        if self._index_ready:
            return
        self._build_poster_index()

    def warm_up(self) -> None:
        """Pre-load CLIP model and poster index (call at server startup)."""
        try:
            self._load_model()
            self._build_poster_index()
        except ImportError:
            print("Vision warm-up skipped: sentence-transformers not installed.")
        except Exception as exc:
            print(f"Vision warm-up failed: {exc}")

    def _decode_image(self, image_base64: str) -> Image.Image:
        raw = image_base64
        if "," in raw:
            raw = raw.split(",", 1)[1]
        data = base64.b64decode(raw)
        return Image.open(io.BytesIO(data)).convert("RGB")

    def _infer_genre_from_image(self, model, query_emb: np.ndarray) -> str:
        text_probe = model.encode(
            ["action blockbuster poster", "romantic comedy poster", "horror thriller poster"]
        )
        mood_labels = ["action", "comedy", "horror"]
        mood_scores = text_probe @ query_emb
        return mood_labels[int(np.argmax(mood_scores))]

    def analyze_poster(self, image_base64: str, top_k: int = 5) -> dict[str, Any]:
        """Match uploaded poster to catalog and infer recommendation intent."""
        try:
            model = self._load_model()
            image = self._decode_image(image_base64)
            query_emb = np.asarray(model.encode(image), dtype=np.float32)
            query_emb = query_emb / max(np.linalg.norm(query_emb), 1e-9)
            inferred_genre = self._infer_genre_from_image(model, query_emb)
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

        self._ensure_poster_index()

        matched_title = ""
        confidence = 0.0
        similar: list[dict] = []

        if self._poster_embeddings is not None and len(self._poster_movies) > 0:
            scores = self._poster_embeddings @ query_emb
            order = np.argsort(scores)[::-1][:top_k]
            for idx in order:
                movie = dict(self._poster_movies[int(idx)])
                score = float(scores[int(idx)])
                movie["visual_score"] = score
                similar.append(movie)
            if similar:
                matched_title = similar[0].get("title", "")
                confidence = similar[0].get("visual_score", 0.0)

        catalog_note = ""
        if not similar and self._index_building:
            catalog_note = " Visual catalog is still loading — using genre-based recommendations."

        return {
            "intent": "movie_recommendation",
            "matched_title": matched_title,
            "confidence": confidence,
            "inferred_genre": inferred_genre,
            "similar_movies": similar,
            "message": (
                f"I analyzed the poster"
                + (f" — it looks like **{matched_title}**" if matched_title else "")
                + f" with a {inferred_genre} vibe.{catalog_note}"
            ),
        }


_vision_service: VisionService | None = None
_warm_up_started = False


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


def warm_up_vision() -> None:
    get_vision_service().warm_up()


def warm_up_vision_async() -> None:
    global _warm_up_started
    if _warm_up_started:
        return
    _warm_up_started = True

    def _run() -> None:
        warm_up_vision()

    threading.Thread(target=_run, daemon=True, name="vision-warmup").start()
