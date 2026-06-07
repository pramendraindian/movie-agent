import json
import os
import random

from app.models.intent_classifier_factory import load_intent_classifier, resolve_model_path
from app.services.llm_service import llm_fallback
from app.services.recommendation_service import recommend

INTENT_MODEL_PATH = resolve_model_path()
classifier = load_intent_classifier(INTENT_MODEL_PATH)
CONF_THRESHOLD = float(os.getenv("INTENT_THRESHOLD", classifier.threshold))

with open("app/data/intents.json") as f:
    intents = json.load(f)


def classify(msg):
    return classifier.predict(msg)


def get_intent_response(msg):
    tag, conf = classify(msg)
    print(
        f"[{classifier.strategy}:{INTENT_MODEL_PATH}] intent={tag} conf={conf:.2f}"
    )

    if conf < CONF_THRESHOLD or tag == "fallback":
        return llm_fallback(msg)

    if tag.startswith("movie") or tag == "movie_recommendation":
        return recommend("movie", msg)

    if tag.startswith("learning") or tag == "learning_recommendation":
        return recommend("learning", msg)

    for intent in intents["intents"]:
        if intent["tag"] == tag:
            return random.choice(intent.get("responses", ["Okay."]))

    return "Sorry, I didn't understand."
