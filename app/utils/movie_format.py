"""Shared movie card formatting for API responses."""

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"


def format_movie_card(movie: dict) -> dict:
    poster_path = str(movie.get("poster_path", "") or "").strip()
    if poster_path.lower() in {"", "nan", "none"}:
        poster_path = ""
    if poster_path and not poster_path.startswith("/"):
        poster_path = f"/{poster_path}"
    poster_url = movie.get("poster_url") or (
        f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else ""
    )
    return {
        "title": movie.get("title", "Unknown"),
        "rating": movie.get("rating", 0),
        "runtime": movie.get("runtime", ""),
        "release_year": movie.get("release_year", ""),
        "genres": movie.get("genres", ""),
        "overview": movie.get("overview", ""),
        "poster_path": poster_path,
        "poster_url": poster_url,
    }
