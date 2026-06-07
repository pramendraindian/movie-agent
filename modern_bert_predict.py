import pickle
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)

# ==================================================
# Load metadata
# ==================================================

with open("intent_model/meta.pkl", "rb") as f:
    meta = pickle.load(f)

INTENT_DESCRIPTIONS = meta["intent_descriptions"]

MODEL_NAME = meta["model_name"]

MAX_LENGTH = meta["max_length"]

# ==================================================
# Load tokenizer + model
# ==================================================

tokenizer = AutoTokenizer.from_pretrained(
    "intent_model"
)

model = AutoModelForSequenceClassification.from_pretrained(
    "intent_model"
)

model.eval()

# ==================================================
# Predict
# ==================================================

def predict_intent(text, threshold=0.65):

    scores = {}

    with torch.no_grad():

        for intent, description in INTENT_DESCRIPTIONS.items():

            inputs = tokenizer(

                text,
                description,

                return_tensors="pt",

                truncation=True,

                max_length=MAX_LENGTH
            )

            outputs = model(**inputs)

            probs = torch.nn.functional.softmax(
                outputs.logits,
                dim=1
            )

            match_probability = probs[0][1].item()

            scores[intent] = match_probability

    # ==================================================
    # Sort scores
    # ==================================================

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    print("\nPredictions:\n")

    for intent, score in sorted_scores:
        print(f"{intent}: {score:.4f}")

    best_intent = sorted_scores[0][0]

    confidence = sorted_scores[0][1]

    if confidence < threshold:
        return "fallback", confidence

    return best_intent, confidence

# ==================================================
# Interactive loop
# ==================================================

while True:

    text = input("\nYou: ")

    if text.lower() in ["quit", "exit"]:
        break

    intent, confidence = predict_intent(text)

    print(f"\nPredicted Intent: {intent}")

    print(f"Confidence: {confidence:.4f}")