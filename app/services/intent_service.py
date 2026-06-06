import json
import random

import torch

from app.models.intent_model import NeuralNet
from app.services.llm_service import llm_fallback
from app.services.recommendation_service import recommend
from app.utils.nlp_utils import bag_of_words, tokenize


with open("app/data/intents.json") as f:
    intents = json.load(f)

data = torch.load("data.pth")

model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"])
model.load_state_dict(data["model_state"])
model.eval()

all_words = data["all_words"]
tags = data["tags"]


def text_response(text: str) -> dict:
    return {"response": text, "movies": []}


def is_movie_query(msg: str) -> bool:
    msg_lower = msg.lower()
    movie_keywords = [
        "movie",
        "movies",
        "film",
        "films",
        "watch",
        "trending",
        "popular",
        "relaxing",
        "feel good",
    ]
    has_duration = any(unit in msg_lower for unit in [" min", " mins", " minute", " minutes"])
    return has_duration or any(keyword in msg_lower for keyword in movie_keywords)


def classify(msg):
    X = bag_of_words(tokenize(msg), all_words)
    X = torch.from_numpy(X).float()
    output = model(X)
    probs = torch.softmax(output, dim=0)
    conf, pred = torch.max(probs, dim=0)
    return tags[pred.item()], conf.item()


def get_intent_response(msg):
    tag, conf = classify(msg)
    print(f"Predicted intent: {tag} with confidence {conf:.2f}")

    if is_movie_query(msg):
        return recommend("movie", msg)

    if conf < 0.7:
        return text_response(llm_fallback(msg))

    if tag.startswith("movie"):
        return recommend("movie", msg)

    if tag.startswith("learning"):
        return recommend("learning", msg)

    for intent in intents["intents"]:
        if intent["tag"] == tag:
            return text_response(random.choice(intent["responses"]))

    return text_response("Sorry, I didn't understand.")
