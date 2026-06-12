import os
from typing import List, Optional

import requests

from app.services.rag_config import get_rag_config
from app.services.retrieval_service import RetrievedMovie, get_retrieval_service

def llm_fallback(msg):
    return "I'm not fully sure, but you can try refining your question: " + msg


def _build_prompt(user_query: str, retrieved: List[RetrievedMovie]) -> str:
    context_lines = []
    for i, movie in enumerate(retrieved, start=1):
        context_lines.append(
            (
                f"{i}. {movie.title} | genres={movie.genres} | rating={movie.rating:.1f} "
                f"| runtime={movie.runtime or 'unknown'} | year={movie.release_year or 'unknown'} "
                f"| overview={movie.overview}"
            )
        )

    context_blob = "\n".join(context_lines) if context_lines else "No retrieved context"
    return (
        "You are a movie assistant. Use only provided context when recommending movies. "
        "Keep response concise (<= 4 lines), do not invent unknown fields, and avoid JSON.\n\n"
        f"User query: {user_query}\n"
        f"Context:\n{context_blob}\n\n"
        "Answer:"
    )


def _call_ollama(prompt: str, model: str, timeout_sec: float) -> Optional[str]:
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=timeout_sec)
    response.raise_for_status()
    data = response.json()
    text = str(data.get("response", "")).strip()
    return text or None


def rag_generate_fallback_response(msg: str) -> Optional[str]:
    config = get_rag_config()
    if not (config.enabled and config.fallback_enabled):
        return None

    try:
        retrieved = get_retrieval_service().retrieve(msg, top_k=config.retrieval_top_k)
        if not retrieved:
            return None

        if config.llm_provider == "ollama":
            prompt = _build_prompt(msg, retrieved)
            return _call_ollama(prompt, model=config.llm_model, timeout_sec=config.llm_timeout_sec)

        print(f"[RAG:llm] unsupported provider: {config.llm_provider}")
        return None
    except Exception as exc:
        print(f"[RAG:llm] fallback due to error: {exc}")
        return None
