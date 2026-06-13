import json
import os
import random
from dotenv import load_dotenv

from app.models.intent_classifier_factory import load_intent_classifier, resolve_model_path
from app.services.context_manager import get_context_manager
from app.services.entity_extractor import extract_entities
from app.services.llm_service import llm_fallback
from app.services.recommendation_service import recommend, text_response

load_dotenv()
INTENT_MODEL_PATH = os.getenv("INTENT_MODEL_PATH", "")
resolve_model_path()
classifier = load_intent_classifier(INTENT_MODEL_PATH)
CONF_THRESHOLD = float(os.getenv("INTENT_THRESHOLD", classifier.threshold))

with open("app/data/intents.json") as f:
    intents = json.load(f)


def is_movie_query(msg: str) -> bool:
    msg_lower = msg.lower()
    movie_keywords = [
        "movie", "movies", "film", "films", "watch", "trending", "popular",
        "relaxing", "feel good", "poster", "recommend", "similar", "genre",
        "suggest", "something to watch", "bored", "entertain",
    ]
    mood_keywords = [
        "sad", "down", "lonely", "happy", "depressed", "heartbroken", "uplifting",
    ]
    has_duration = any(
        unit in msg_lower for unit in [" min", " mins", " minute", " minutes"]
    )
    return (
        has_duration
        or any(keyword in msg_lower for keyword in movie_keywords)
        or any(keyword in msg_lower for keyword in mood_keywords)
    )


def has_movie_entities(msg: str) -> bool:
    entities = extract_entities(msg)
    return bool(
        entities.get("mood")
        or entities.get("genre")
        or entities.get("similar_to")
        or entities.get("follow_up")
        or entities.get("language")
        or entities.get("year")
        or entities.get("sort")
        or entities.get("runtime")
    )


def should_route_to_movies(msg: str) -> bool:
    return is_movie_query(msg) or has_movie_entities(msg)


def classify(msg):
    return classifier.predict(msg)


def get_intent_response(
    msg: str,
    *,
    session_id: str | None = None,
    image_base64: str | None = None,
) -> dict:
    ctx = get_context_manager().get_or_create(session_id)
    tag, conf = classify(msg)
    print(
        f"[{classifier.strategy}:{INTENT_MODEL_PATH}] intent={tag} conf={conf:.2f} session={ctx.session_id}"
    )

    if image_base64:
        result = recommend("movie", msg, session_id=ctx.session_id, image_base64=image_base64)
        result.setdefault("intent", "movie_recommendation")
        return result

    if tag.startswith("movie") or tag == "movie_recommendation" or should_route_to_movies(msg):
        result = recommend("movie", msg, session_id=ctx.session_id)
        result.setdefault("intent", tag if tag.startswith("movie") else "movie_recommendation")
        return result

    if conf < CONF_THRESHOLD or tag == "fallback":
        reply = text_response(llm_fallback(msg), ctx.session_id)
        ctx.add_turn("user", msg)
        ctx.add_turn("assistant", reply["response"])
        reply["intent"] = "fallback"
        return reply

    if tag.startswith("learning") or tag == "learning_recommendation":
        result = recommend("learning", msg, session_id=ctx.session_id)
        result["intent"] = tag
        return result

    for intent in intents["intents"]:
        if intent["tag"] == tag:
            reply = text_response(random.choice(intent.get("responses", ["Okay."])), ctx.session_id)
            ctx.add_turn("user", msg)
            ctx.add_turn("assistant", reply["response"])
            reply["intent"] = tag
            return reply

    reply = text_response("Sorry, I didn't understand.", ctx.session_id)
    reply["intent"] = "unknown"
    return reply
