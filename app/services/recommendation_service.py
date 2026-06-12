import re

from app.services.entity_extractor import extract_entities
from app.services.rag_config import get_rag_config
from app.services.retrieval_service import get_retrieval_service
from app.utils.movie_utils import get_recommendation_engine


TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"


def text_response(text: str) -> dict:
    return {"response": text, "movies": []}


def recommend(domain, msg):
    """
    Provide recommendations based on domain and user message.

    Args:
        domain: "movie" or "learning"
        msg: user's message/query

    Returns:
        Recommendation response dictionary
    """
    if domain == "movie":
        return get_movie_recommendations(msg)
    if domain == "learning":
        return get_learning_recommendations(msg)
    return text_response("I can help with movie or learning recommendations. What would you like?")


def get_movie_recommendations(msg: str) -> dict:
    """Get movie recommendations based on user message and extracted entities."""
    try:
        engine = get_recommendation_engine()
        entities = extract_entities(msg)
        msg_lower = msg.lower()

        duration_match = re.search(
            r"\b(\d{2,3})\s*(?:min|mins|minute|minutes)\b",
            msg_lower,
        )

        if duration_match:
            target_minutes = int(duration_match.group(1))
            recommendations = engine.get_runtime_recommendations(
                target_minutes,
                n_recommendations=5,
            )
        elif (
            "relaxing" in msg_lower
            or "feel good" in msg_lower
            or "light" in msg_lower
            or entities.get("mood") == "feel_good"
        ):
            recommendations = engine.get_genre_recommendations(
                "comedy",
                n_recommendations=5,
            )
        elif "genre" in entities:
            recommendations = engine.get_genre_recommendations(
                entities["genre"],
                n_recommendations=5,
            )
        elif "year" in entities:
            recommendations = engine.get_movies_by_year(entities["year"])
        elif entities.get("sort") == "rating":
            recommendations = engine.get_top_rated_recommendations(5)
        elif entities.get("sort") == "trending":
            recommendations = engine.get_trending_recommendations(5)
        else:
            recommendations = engine.get_trending_recommendations(5)

        recommendations = _augment_with_retrieved_movies(msg, recommendations)

        if recommendations:
            return {
                "response": "I recommend these movies:",
                "movies": [format_movie_card(movie) for movie in recommendations],
            }

        return text_response(
            "Sorry, I couldn't find movie recommendations. Try asking about a specific genre!"
        )

    except Exception as e:
        print(f"Error in get_movie_recommendations: {e}")
        return text_response("I had trouble fetching recommendations. Please try again!")


def _augment_with_retrieved_movies(msg: str, base_recommendations: list) -> list:
    config = get_rag_config()
    if not (config.enabled and config.movie_augmentation_enabled):
        return base_recommendations

    try:
        retrieved = get_retrieval_service().retrieve(msg, top_k=config.retrieval_top_k)
        if not retrieved:
            return base_recommendations

        merged = list(base_recommendations)
        seen_titles = {str(movie.get("title", "")).strip().lower() for movie in merged}

        for item in retrieved:
            title_key = item.title.strip().lower()
            if not title_key or title_key in seen_titles:
                continue
            merged.append(
                {
                    "title": item.title,
                    "rating": item.rating,
                    "runtime": item.runtime,
                    "release_year": item.release_year,
                    "genres": item.genres,
                    "overview": item.overview,
                    "poster_path": item.poster_path,
                }
            )
            seen_titles.add(title_key)
            if len(merged) >= 5:
                break

        print("[RAG:movie-augmentation] merged retrieval with TF-IDF results")
        return merged[:5]
    except Exception as exc:
        print(f"[RAG:movie-augmentation] fallback due to error: {exc}")
        return base_recommendations


def format_movie_summary(movie: dict) -> str:
    """Format one movie for compact pipe-delimited UI rendering."""
    runtime = f" - {movie['runtime']}" if movie.get("runtime") else ""
    return f"{movie['title']} - {movie['rating']:.1f}/10{runtime}"


def format_movie_card(movie: dict) -> dict:
    """Format one movie for structured API/UI rendering."""
    poster_path = str(movie.get("poster_path", "") or "").strip()
    if poster_path.lower() in {"", "nan", "none"}:
        poster_path = ""
    if poster_path and not poster_path.startswith("/"):
        poster_path = f"/{poster_path}"
    poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else ""
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


def get_learning_recommendations(msg: str) -> dict:
    """Get learning resource recommendations."""
    recommendations = {
        "programming": [
            "freeCodeCamp - Free coding courses",
            "Codecademy - Interactive coding lessons",
            "LeetCode - Programming problem practice",
        ],
        "data science": [
            "Fast.ai - Practical deep learning",
            "Coursera - Data science specializations",
            "Kaggle - Real-world data projects",
        ],
        "web development": [
            "MDN Web Docs - Web standards documentation",
            "The Odin Project - Full stack curriculum",
            "Frontend Masters - Advanced web skills",
        ],
        "general": [
            "Coursera - University-level courses",
            "edX - Quality online education",
            "YouTube Learning - Video tutorials",
            "Khan Academy - Free educational content",
        ],
    }

    msg_lower = msg.lower()

    for topic in recommendations.keys():
        if topic in msg_lower:
            return text_response("You might like: " + ", ".join(recommendations[topic][:2]))

    return text_response("You might like: " + ", ".join(recommendations["general"][:3]))
