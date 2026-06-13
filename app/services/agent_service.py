"""Agentic orchestrator: intent → plan → tool execution → RAG → LLM synthesis."""

from __future__ import annotations

import os
import re
from typing import Any

from app.services.context_manager import SessionContext
from app.services.entity_extractor import extract_entities
from app.services.llm_service import plan_with_llm, synthesize_response
from app.services.query_builder import RecommendationPlan, build_plan
from app.utils.movie_format import format_movie_card
from app.services.tmdb_client import get_tmdb_client
from app.services.vector_store import get_vector_store
from app.services.vision_service import get_vision_service
from app.utils.movie_utils import get_recommendation_engine

AGENT_MODE = os.getenv("AGENT_MODE", "hybrid")  # hybrid | rule | llm
USE_TMDB_API = os.getenv("USE_TMDB_API", "true").lower() in {"1", "true", "yes"}


TOOL_SCHEMA = [
    {"name": "rag_search", "description": "Semantic search over movie overviews/genres", "params": ["query", "n"]},
    {"name": "similar_movies", "description": "Content-based similar titles", "params": ["title", "n"]},
    {"name": "genre", "description": "Filter by genre", "params": ["genre", "n"]},
    {"name": "trending", "description": "Popular/trending movies", "params": ["n"]},
    {"name": "top_rated", "description": "Highest rated movies", "params": ["n"]},
    {"name": "runtime", "description": "Movies near target runtime", "params": ["minutes", "n"]},
    {"name": "year", "description": "Movies from a release year", "params": ["year", "n"]},
    {"name": "search_title", "description": "Exact title search", "params": ["query", "n"]},
]


def _is_follow_up(message: str, ctx: SessionContext) -> bool:
    msg = message.lower().strip()
    follow_up_phrases = (
        "more like this",
        "similar to that",
        "another one",
        "more of those",
        "show me more",
        "anything else",
    )
    return any(p in msg for p in follow_up_phrases) and bool(ctx.last_movies)


def execute_tool(tool: str, params: dict[str, Any]) -> list[dict]:
    engine = get_recommendation_engine()
    n = int(params.get("n", 5))
    vector_store = get_vector_store()
    tmdb = get_tmdb_client()

    if tool == "rag_search":
        movies = vector_store.retrieve(params.get("query", ""), top_k=n)
        if not movies:
            movies = engine.search_movies(params.get("query", ""), n)
        return movies

    if tool == "similar_movies":
        title = params.get("title", "")
        movies = engine.get_content_based_recommendations(title, n)
        if not movies:
            movies = vector_store.retrieve_similar_to_title(title, top_k=n)
        return movies

    if tool == "genre":
        return engine.get_genre_recommendations(params.get("genre", "drama"), n)

    if tool == "trending":
        if USE_TMDB_API and tmdb.enabled:
            live = tmdb.trending(n)
            if live:
                return live
        return engine.get_trending_recommendations(n)

    if tool == "top_rated":
        return engine.get_top_rated_recommendations(n)

    if tool == "runtime":
        return engine.get_runtime_recommendations(int(params.get("minutes", 90)), n)

    if tool == "year":
        return engine.get_movies_by_year(int(params.get("year", 2020)), n)

    if tool == "search_title":
        query = params.get("query", "")
        if USE_TMDB_API and tmdb.enabled:
            live = tmdb.search_movies(query, n)
            if live:
                return live
        return engine.search_movies(query, n)

    return engine.get_trending_recommendations(n)


def _merge_tmdb_boost(movies: list[dict], query: str) -> list[dict]:
    if not USE_TMDB_API:
        return movies
    tmdb = get_tmdb_client()
    if not tmdb.enabled or not query:
        return movies
    live = tmdb.search_movies(query, 2)
    if not live:
        return movies
    seen = {m.get("title", "").lower() for m in movies}
    merged = list(movies)
    for item in live:
        if item.get("title", "").lower() not in seen:
            merged.insert(0, item)
            seen.add(item.get("title", "").lower())
    return merged[: max(len(movies), 5)]


def run_agent(
    message: str,
    ctx: SessionContext,
    *,
    image_base64: str | None = None,
    forced_intent: str | None = None,
) -> dict[str, Any]:
    tools_used: list[str] = []
    vision_result: dict | None = None
    entities = extract_entities(message)

    duration_match = re.search(r"\b(\d{2,3})\s*(?:min|mins|minute|minutes)\b", message.lower())
    if duration_match:
        entities["runtime"] = int(duration_match.group(1))

    if image_base64:
        vision = get_vision_service()
        vision_result = vision.analyze_poster(image_base64)
        tools_used.append("vision_analyze_poster")
        if vision_result.get("matched_title"):
            entities["similar_to"] = vision_result["matched_title"]
        elif vision_result.get("inferred_genre"):
            entities.setdefault("genre", vision_result["inferred_genre"])

    is_follow_up = _is_follow_up(message, ctx)
    plan: RecommendationPlan | None = None

    if AGENT_MODE in {"llm", "hybrid"} and not image_base64:
        llm_plan = plan_with_llm(message, ctx.history_text(), TOOL_SCHEMA)
        if llm_plan and llm_plan.get("tool"):
            plan = RecommendationPlan(
                tool=llm_plan["tool"],
                params=llm_plan.get("params", {}),
                reason=llm_plan.get("reason", "LLM planner"),
            )
            tools_used.append(f"llm_plan:{plan.tool}")

    if plan is None:
        plan = build_plan(
            message,
            entities,
            is_follow_up=is_follow_up,
            last_movies=ctx.last_movies,
        )
        tools_used.append(f"rule_plan:{plan.tool}")

    movies = execute_tool(plan.tool, plan.params)
    tools_used.append(plan.tool)

    if not movies and plan.tool != "rag_search":
        movies = execute_tool("rag_search", {"query": message, "n": 5})
        tools_used.append("rag_search_fallback")

    if vision_result and vision_result.get("similar_movies"):
        seen = {m.get("title") for m in movies}
        for vm in vision_result["similar_movies"]:
            if vm.get("title") not in seen:
                movies.append(vm)
                seen.add(vm.get("title"))

    movies = _merge_tmdb_boost(movies, message)
    movies = movies[:5]

    rag_snippets = [
        f"{m.get('title')}: {m.get('overview', '')[:100]}"
        for m in movies[:3]
    ]
    rag_context = "\n".join(rag_snippets)

    response_text = synthesize_response(
        user_message=message,
        movies=movies,
        rag_context=rag_context,
        system_hint=plan.reason,
        history=ctx.history_text(),
    )

    if vision_result and image_base64:
        response_text = f"{vision_result.get('message', '')} {response_text}".strip()

    ctx.last_movies = movies
    ctx.last_entities = entities
    ctx.last_query = message
    ctx.last_intent = forced_intent or "movie_recommendation"
    ctx.add_turn("user", message)
    ctx.add_turn("assistant", response_text)

    return {
        "response": response_text,
        "movies": [format_movie_card(m) for m in movies],
        "session_id": ctx.session_id,
        "intent": ctx.last_intent,
        "tools_used": tools_used,
        "plan": {"tool": plan.tool, "params": plan.params, "reason": plan.reason},
    }
