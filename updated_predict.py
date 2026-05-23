import torch
import pickle

from transformers import (
    BertTokenizer,
    BertForSequenceClassification
)

# ==================================================
# Load model
# ==================================================

model = BertForSequenceClassification.from_pretrained(
    "intent_model"
)

tokenizer = BertTokenizer.from_pretrained(
    "intent_model"
)

with open("intent_model/meta.pkl", "rb") as f:
    meta = pickle.load(f)

INTENT_DESCRIPTIONS = meta["intent_descriptions"]

# ==================================================
# Predict
# ==================================================

def predict_intent(text):

    scores = {}

    for intent, description in INTENT_DESCRIPTIONS.items():

        inputs = tokenizer(
            text,
            description,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=64
        )

        outputs = model(**inputs)

        probs = torch.nn.functional.softmax(
            outputs.logits,
            dim=1
        )

        match_probability = probs[0][1].item()

        scores[intent] = match_probability

    # -----------------------------------------
    # Print all scores
    # -----------------------------------------

    print("\nPredictions:\n")

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for intent, score in sorted_scores:
        print(f"{intent}: {score:.4f}")

    best_intent = sorted_scores[0][0]
    confidence = sorted_scores[0][1]

    # confidence threshold
    if confidence < 0.65:
        return "fallback", confidence

    return best_intent, confidence

# ==================================================
# Interactive test
# ==================================================

while True:

    text = input("\nYou: ")

    intent, confidence = predict_intent(text)

    print(
        f"\nPredicted Intent: {intent}"
    )

    print(
        f"Confidence: {confidence:.4f}"
    )