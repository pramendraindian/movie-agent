"""Movie recommendation service — delegates to the agentic RAG pipeline."""

from __future__ import annotations

from app.services.context_manager import SessionContext, get_context_manager
from app.utils.movie_format import format_movie_card

# Re-export for backwards compatibility
__all__ = ["recommend", "get_movie_recommendations", "format_movie_card", "text_response"]


def text_response(text: str, session_id: str = "") -> dict:
    payload = {"response": text, "movies": []}
    if session_id:
        payload["session_id"] = session_id
    return payload


def recommend(
    domain: str,
    msg: str,
    *,
    session_id: str | None = None,
    image_base64: str | None = None,
) -> dict:
    ctx = get_context_manager().get_or_create(session_id)

    if domain == "movie" or image_base64:
        return get_movie_recommendations(msg, ctx, image_base64=image_base64)

    if domain == "learning":
        return get_learning_recommendations(msg, ctx.session_id)

    return text_response(
        "I can help with movie or learning recommendations. What would you like?",
        ctx.session_id,
    )


def get_movie_recommendations(
    msg: str,
    ctx: SessionContext,
    *,
    image_base64: str | None = None,
) -> dict:
    try:
        from app.services.agent_service import run_agent

        return run_agent(msg, ctx, image_base64=image_base64)
    except Exception as e:
        print(f"Error in get_movie_recommendations: {e}")
        return text_response(
            "I had trouble fetching recommendations. Please try again!",
            ctx.session_id,
        )


def format_movie_summary(movie: dict) -> str:
    runtime = f" - {movie['runtime']}" if movie.get("runtime") else ""
    return f"{movie['title']} - {movie['rating']:.1f}/10{runtime}"


def get_learning_recommendations(msg: str, session_id: str = "") -> dict:
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

    for topic in recommendations:
        if topic in msg_lower:
            return text_response(
                "You might like: " + ", ".join(recommendations[topic][:2]),
                session_id,
            )

    return text_response(
        "You might like: " + ", ".join(recommendations["general"][:3]),
        session_id,
    )
