import pickle

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class MulticlassIntentClassifier:
    STRATEGY = "multiclass"
    DEFAULT_THRESHOLD = 0.5

    def __init__(self, model_path="intent_model", threshold=None):
        with open(f"{model_path}/meta.pkl", "rb") as f:
            meta = pickle.load(f)

        self.model_path = model_path
        self.strategy = meta.get("strategy", self.STRATEGY)
        self.model_name = meta.get("model_name")
        self.threshold = threshold if threshold is not None else meta.get(
            "threshold", self.DEFAULT_THRESHOLD
        )
        self.id2tag = meta["id2tag"]
        if isinstance(self.id2tag, dict) and self.id2tag and isinstance(
            next(iter(self.id2tag.keys())), str
        ):
            self.id2tag = {int(k): v for k, v in self.id2tag.items()}

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def predict(self, text):
        inputs = self.tokenizer(
            text, return_tensors="pt", truncation=True, padding=True
        )
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        pred_id = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_id].item()
        return self.id2tag[pred_id], confidence
