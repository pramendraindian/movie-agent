import json
import os
import random

import torch

from app.models.intent_model import NeuralNet
from app.utils.nlp_utils import bag_of_words, tokenize
from app.services.llm_service import llm_fallback
from app.services.recommendation_service import recommend

INTENT_BACKEND = os.getenv("INTENT_BACKEND", "bow").lower()

with open("app/data/intents.json") as f:
    intents = json.load(f)

if INTENT_BACKEND == "modernbert":
    from app.models.modern_bert_intent_model import ModernBertIntentClassifier

    classifier = ModernBertIntentClassifier()
    CONF_THRESHOLD = 0.65

    def classify(msg):
        return classifier.predict(msg)
else:
    data = torch.load("data.pth")

    model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"])
    model.load_state_dict(data["model_state"])
    model.eval()

    all_words = data["all_words"]
    tags = data["tags"]
    CONF_THRESHOLD = 0.7

    def classify(msg):
        X = bag_of_words(tokenize(msg), all_words)
        X = torch.from_numpy(X).float()
        output = model(X)
        probs = torch.softmax(output, dim=0)
        conf, pred = torch.max(probs, dim=0)
        return tags[pred.item()], conf.item()


def get_intent_response(msg):
    tag, conf = classify(msg)
    print(f"[{INTENT_BACKEND}] intent={tag} conf={conf:.2f}")

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
