import pickle
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class ModernBertIntentClassifier:
    def __init__(self, model_path="intent_model", threshold=0.65):
        with open(f"{model_path}/meta.pkl", "rb") as f:
            meta = pickle.load(f)
        self.intent_descriptions = meta["intent_descriptions"]
        self.max_length = meta["max_length"]
        self.threshold = threshold
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def predict(self, text):
        scores = {}
        with torch.no_grad():
            for intent, description in self.intent_descriptions.items():
                inputs = self.tokenizer(
                    text, description,
                    return_tensors="pt", truncation=True, max_length=self.max_length
                )
                probs = torch.nn.functional.softmax(self.model(**inputs).logits, dim=1)
                scores[intent] = probs[0][1].item()
        best_intent, confidence = max(scores.items(), key=lambda x: x[1])
        if confidence < self.threshold:
            return "fallback", confidence
        return best_intent, confidence