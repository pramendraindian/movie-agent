"""Build recommendation plans from intent, entities, and session context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecommendationPlan:
    tool: str
    params: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


def build_plan(
    message: str,
    entities: dict[str, Any],
    *,
    is_follow_up: bool = False,
    last_movies: list[dict] | None = None,
) -> RecommendationPlan:
    msg = message.lower()
    last_movies = last_movies or []

    if is_follow_up and last_movies:
        anchor = last_movies[0].get("title", "")
        if anchor:
            return RecommendationPlan(
                tool="similar_movies",
                params={"title": anchor, "n": 5},
                reason=f"Follow-up to previous picks; finding movies like {anchor}.",
            )

    if entities.get("similar_to"):
        return RecommendationPlan(
            tool="similar_movies",
            params={"title": entities["similar_to"], "n": 5},
            reason=f"User asked for movies similar to {entities['similar_to']}.",
        )

    if entities.get("runtime"):
        return RecommendationPlan(
            tool="runtime",
            params={"minutes": entities["runtime"], "n": 5},
            reason=f"Runtime constraint ~{entities['runtime']} minutes.",
        )

    if entities.get("mood") == "feel_good" or any(
        k in msg for k in ("relaxing", "feel good", "uplifting", "light")
    ):
        return RecommendationPlan(
            tool="genre",
            params={"genre": "comedy", "n": 5},
            reason="Feel-good / relaxing mood maps to comedy picks.",
        )

    if entities.get("mood") == "sad":
        return RecommendationPlan(
            tool="rag_search",
            params={"query": "comforting uplifting feel good heartwarming movie", "n": 5},
            reason="Sad mood — retrieving comforting feel-good titles via RAG.",
        )

    if entities.get("genre"):
        return RecommendationPlan(
            tool="genre",
            params={"genre": entities["genre"], "n": 5},
            reason=f"Genre filter: {entities['genre']}.",
        )

    if "sci-fi" in msg or "science fiction" in msg or "space" in msg:
        return RecommendationPlan(
            tool="genre",
            params={"genre": "sci-fi", "n": 5},
            reason="Sci-fi request.",
        )

    if entities.get("year"):
        return RecommendationPlan(
            tool="year",
            params={"year": entities["year"], "n": 5},
            reason=f"Release year filter: {entities['year']}.",
        )

    if entities.get("language"):
        return RecommendationPlan(
            tool="rag_search",
            params={
                "query": f"{entities['language']} language movies {message}",
                "n": 5,
            },
            reason=f"Language preference: {entities['language']}.",
        )

    if entities.get("sort") == "rating":
        return RecommendationPlan(
            tool="top_rated",
            params={"n": 5},
            reason="User asked for top-rated movies.",
        )

    if entities.get("sort") == "trending" or "trending" in msg or "popular" in msg:
        return RecommendationPlan(
            tool="trending",
            params={"n": 5},
            reason="Trending / popular request.",
        )

    if any(k in msg for k in ("like", "similar", "same as", "more like")):
        return RecommendationPlan(
            tool="rag_search",
            params={"query": message, "n": 5},
            reason="Similarity-style query handled by semantic RAG search.",
        )

    return RecommendationPlan(
        tool="rag_search",
        params={"query": message, "n": 5},
        reason="Default semantic retrieval over movie catalog.",
    )
