import os
import pickle
from typing import Optional, Union

from app.models.bow_intent_classifier import BowIntentClassifier
from app.models.multiclass_intent_classifier import MulticlassIntentClassifier
from app.models.sentence_pair_intent_classifier import SentencePairIntentClassifier

IntentClassifier = Union[
    BowIntentClassifier,
    MulticlassIntentClassifier,
    SentencePairIntentClassifier,
]

STRATEGY_ALIASES = {
    "bow": "bow",
    "multiclass": "multiclass",
    "sentence_pair": "sentence_pair",
    "sentence-pair": "sentence_pair",
    "pair": "sentence_pair",
    "modernbert": "sentence_pair",
    "bert": "sentence_pair",
    "distilbert": "multiclass",
}


def resolve_model_path(model_path: Optional[str] = None) -> str:
    if model_path:
        return model_path
    if env_path := os.getenv("INTENT_MODEL_PATH"):
        return env_path

    backend = os.getenv("INTENT_BACKEND", "bow").lower()
    if backend in {"modernbert", "sentence_pair", "sentence-pair", "pair", "bert"}:
        return "intent_model"
    if backend in {"multiclass", "distilbert"}:
        return "intent_model"
    return "data.pth"


def detect_strategy(model_path: str, meta: Optional[dict] = None) -> str:
    if model_path.endswith(".pth"):
        return BowIntentClassifier.STRATEGY

    if meta is None:
        with open(f"{model_path}/meta.pkl", "rb") as f:
            meta = pickle.load(f)

    if strategy := meta.get("strategy"):
        normalized = STRATEGY_ALIASES.get(strategy.lower(), strategy.lower())
        if normalized not in {
            BowIntentClassifier.STRATEGY,
            MulticlassIntentClassifier.STRATEGY,
            SentencePairIntentClassifier.STRATEGY,
        }:
            raise ValueError(f"Unsupported intent strategy: {strategy}")
        return normalized

    if "intent_descriptions" in meta:
        return SentencePairIntentClassifier.STRATEGY
    if "id2tag" in meta:
        return MulticlassIntentClassifier.STRATEGY

    raise ValueError(
        f"Could not detect intent strategy for model path: {model_path}. "
        "Expected meta.pkl to include 'strategy' or known classifier metadata."
    )


def load_intent_classifier(
    model_path: Optional[str] = None,
    strategy: Optional[str] = None,
    threshold: Optional[float] = None,
) -> IntentClassifier:
    resolved_path = resolve_model_path(model_path)
    resolved_strategy = strategy or os.getenv("INTENT_STRATEGY")

    if resolved_strategy:
        resolved_strategy = STRATEGY_ALIASES.get(
            resolved_strategy.lower(), resolved_strategy.lower()
        )
    elif resolved_path.endswith(".pth"):
        resolved_strategy = BowIntentClassifier.STRATEGY
    else:
        resolved_strategy = detect_strategy(resolved_path)

    if threshold is None and os.getenv("INTENT_THRESHOLD"):
        threshold = float(os.getenv("INTENT_THRESHOLD"))

    if resolved_strategy == BowIntentClassifier.STRATEGY:
        return BowIntentClassifier(resolved_path, threshold=threshold)
    if resolved_strategy == MulticlassIntentClassifier.STRATEGY:
        return MulticlassIntentClassifier(resolved_path, threshold=threshold)
    if resolved_strategy == SentencePairIntentClassifier.STRATEGY:
        return SentencePairIntentClassifier(resolved_path, threshold=threshold)

    raise ValueError(f"Unsupported intent strategy: {resolved_strategy}")
