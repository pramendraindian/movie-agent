import pickle

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class SentencePairIntentClassifier:
    STRATEGY = "sentence_pair"
    DEFAULT_THRESHOLD = 0.65

    def __init__(self, model_path="intent_model", threshold=None):
        with open(f"{model_path}/meta.pkl", "rb") as f:
            meta = pickle.load(f)

        self.model_path = model_path
        self.strategy = meta.get("strategy", self.STRATEGY)
        self.model_name = meta.get("model_name")
        self.intent_descriptions = meta["intent_descriptions"]
        self.max_length = meta.get("max_length", 128)
        self.threshold = threshold if threshold is not None else meta.get(
            "threshold", self.DEFAULT_THRESHOLD
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def predict(self, text):
        scores = {}

        with torch.no_grad():
            for intent, description in self.intent_descriptions.items():
                inputs = self.tokenizer(
                    text,
                    description,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.max_length,
                )
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=1)
                scores[intent] = probs[0][1].item()

        best_intent, confidence = max(scores.items(), key=lambda item: item[1])
        if confidence < self.threshold:
            return "fallback", confidence
        return best_intent, confidence
