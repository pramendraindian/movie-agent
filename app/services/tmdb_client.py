"""TMDB REST API client for live movie search and metadata."""

from __future__ import annotations

import os
from typing import Any

import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"


class TMDBClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("TMDB_API_KEY", "")
        self.enabled = bool(self.api_key)

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        if not self.enabled:
            return None
        params = dict(params or {})
        params["api_key"] = self.api_key
        try:
            resp = requests.get(f"{TMDB_BASE}{path}", params=params, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            print(f"TMDB API error ({path}): {exc}")
            return None

    def search_movies(self, query: str, n: int = 5) -> list[dict[str, Any]]:
        data = self._get("/search/movie", {"query": query, "page": 1})
        if not data or "results" not in data:
            return []
        return [self._normalize_movie(m) for m in data["results"][:n]]

    def trending(self, n: int = 5) -> list[dict[str, Any]]:
        data = self._get("/trending/movie/week")
        if not data or "results" not in data:
            return []
        return [self._normalize_movie(m) for m in data["results"][:n]]

    def movie_details(self, movie_id: int) -> dict[str, Any] | None:
        data = self._get(f"/movie/{movie_id}")
        if not data:
            return None
        return self._normalize_movie(data)

    def find_by_poster_path(self, poster_path: str) -> list[dict[str, Any]]:
        """Best-effort lookup when poster path is known from vision match."""
        if not poster_path:
            return []
        data = self._get("/search/movie", {"query": poster_path.split("/")[-1]})
        if not data or "results" not in data:
            return []
        matches = [
            self._normalize_movie(m)
            for m in data["results"]
            if m.get("poster_path") == poster_path
        ]
        return matches[:3]

    def _normalize_movie(self, raw: dict) -> dict[str, Any]:
        poster = raw.get("poster_path") or ""
        if poster and not str(poster).startswith("/"):
            poster = f"/{poster}"
        release = raw.get("release_date") or ""
        year = release[:4] if release else ""
        genres = ", ".join(g.get("name", "") for g in raw.get("genres", []) if g.get("name"))
        if not genres and raw.get("genre_ids"):
            genres = ", ".join(str(g) for g in raw["genre_ids"])
        runtime = raw.get("runtime")
        runtime_str = f"{int(runtime)} min" if runtime else ""
        return {
            "id": raw.get("id", 0),
            "title": raw.get("title") or raw.get("original_title") or "Unknown",
            "rating": float(raw.get("vote_average") or 0),
            "genres": genres or "Unknown",
            "overview": (raw.get("overview") or "")[:200],
            "popularity": float(raw.get("popularity") or 0),
            "vote_count": int(raw.get("vote_count") or 0),
            "release_date": release,
            "release_year": year,
            "runtime": runtime_str,
            "poster_path": poster,
            "poster_url": f"{TMDB_IMAGE_BASE}{poster}" if poster else "",
            "source": "tmdb_api",
        }


_tmdb_client: TMDBClient | None = None


def get_tmdb_client() -> TMDBClient:
    global _tmdb_client
    if _tmdb_client is None:
        _tmdb_client = TMDBClient()
    return _tmdb_client
