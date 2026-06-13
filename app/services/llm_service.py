"""LLM integration with optional RAG context for response synthesis."""

from __future__ import annotations

import json
import os
from typing import Any

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _openai_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def llm_fallback(msg: str) -> str:
    if not _openai_available():
        return (
            "I'm not fully sure how to help with that. "
            "Try asking for movie recommendations by genre, mood, runtime, or upload a poster image."
        )
    return synthesize_response(
        user_message=msg,
        movies=[],
        rag_context="",
        system_hint="The user message was unclear. Ask a clarifying question about movies.",
    )


def synthesize_response(
    *,
    user_message: str,
    movies: list[dict],
    rag_context: str = "",
    system_hint: str = "",
    history: str = "",
) -> str:
    """Generate a natural-language reply grounded in retrieved movies."""
    if not _openai_available():
        return _template_response(user_message, movies, system_hint)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        movie_summaries = [
            f"- {m.get('title')} ({m.get('rating', 0):.1f}/10): {m.get('overview', '')[:120]}"
            for m in movies[:5]
        ]
        prompt = f"""You are CineGenie, an expert movie recommendation agent using TMDB data.

Conversation history:
{history or 'None'}

User: {user_message}

Retrieved movies (ground truth — only recommend from this list):
{chr(10).join(movie_summaries) if movie_summaries else 'None found'}

RAG context:
{rag_context or 'N/A'}

Task: {system_hint or 'Explain why these picks fit the user request. Be concise (2-4 sentences).'}
"""
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful movie assistant. Never invent movie titles."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"LLM synthesis error: {exc}")
        return _template_response(user_message, movies, system_hint)


def plan_with_llm(
    user_message: str,
    history: str,
    tools_schema: list[dict],
) -> dict[str, Any] | None:
    """Optional LLM tool planner for agentic routing."""
    if not _openai_available():
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a movie agent planner. Choose one tool to satisfy the user. "
                        "Respond ONLY with JSON: {\"tool\": \"...\", \"params\": {...}, \"reason\": \"...\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"History:\n{history}\n\nUser: {user_message}\n\nTools:\n{json.dumps(tools_schema)}",
                },
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:
        print(f"LLM planner error: {exc}")
        return None


def _template_response(user_message: str, movies: list[dict], hint: str) -> str:
    if not movies:
        return hint or "I couldn't find matching movies. Try a genre, mood, or movie title."
    titles = ", ".join(m.get("title", "?") for m in movies[:3])
    extra = f" and {len(movies) - 3} more" if len(movies) > 3 else ""
    return f"Based on your request, I recommend: {titles}{extra}."
