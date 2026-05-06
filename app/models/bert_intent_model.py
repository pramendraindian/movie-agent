from transformers import BertTokenizer, BertForSequenceClassification
import torch
import pickle

class BertIntentClassifier:
    def __init__(self, model_path="intent_model"):
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)

        with open(f"{model_path}/meta.pkl", "rb") as f:
            meta = pickle.load(f)

        self.id2tag = meta["id2tag"]

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        outputs = self.model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=1)
        pred_id = torch.argmax(probs).item()
        confidence = probs[0][pred_id].item()

        return self.id2tag[pred_id], confidence