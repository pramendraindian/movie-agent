import os
from dataclasses import dataclass


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class RagConfig:
    enabled: bool
    fallback_enabled: bool
    movie_augmentation_enabled: bool
    fallback_movie_queries_only: bool
    retrieval_backend: str
    retrieval_top_k: int
    retrieval_timeout_sec: float
    retrieval_similarity_cutoff: float
    llm_provider: str
    llm_model: str
    llm_timeout_sec: float


def get_rag_config() -> RagConfig:
    return RagConfig(
        enabled=_to_bool(os.getenv("RAG_ENABLED"), default=False),
        fallback_enabled=_to_bool(os.getenv("RAG_FALLBACK_ENABLED"), default=False),
        movie_augmentation_enabled=_to_bool(
            os.getenv("RAG_MOVIE_AUGMENTATION_ENABLED"),
            default=False,
        ),
        fallback_movie_queries_only=_to_bool(
            os.getenv("RAG_FALLBACK_MOVIE_ONLY"),
            default=False,
        ),
        retrieval_backend=os.getenv("RAG_RETRIEVAL_BACKEND", "chroma").strip().lower(),
        retrieval_top_k=_to_int(os.getenv("RAG_RETRIEVAL_TOP_K"), default=5),
        retrieval_timeout_sec=_to_float(
            os.getenv("RAG_RETRIEVAL_TIMEOUT_SEC"),
            default=1.2,
        ),
        retrieval_similarity_cutoff=_to_float(
            os.getenv("RAG_RETRIEVAL_SIMILARITY_CUTOFF"),
            default=0.2,
        ),
        llm_provider=os.getenv("RAG_LLM_PROVIDER", "ollama").strip().lower(),
        llm_model=os.getenv("RAG_LLM_MODEL", "phi3:mini").strip(),
        llm_timeout_sec=_to_float(os.getenv("RAG_LLM_TIMEOUT_SEC"), default=2.5),
    )
