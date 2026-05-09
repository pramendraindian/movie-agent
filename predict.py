import torch
import pickle
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

# Load model
# model = BertForSequenceClassification.from_pretrained("intent_model")
# tokenizer = BertTokenizer.from_pretrained("intent_model")
model = DistilBertForSequenceClassification.from_pretrained("intent_model")
tokenizer = DistilBertTokenizer.from_pretrained("intent_model")

with open("intent_model/meta.pkl", "rb") as f:
    meta = pickle.load(f)

id2tag = meta["id2tag"]

def predict_intent(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=1)
    top_probs, top_ids = torch.topk(probs, k=len(id2tag))

    print("\nPredictions:")

    for score, idx in zip(top_probs[0], top_ids[0]):
        print(f"{id2tag[idx.item()]}: {score.item():.4f}")

    pred_id = top_ids[0][0].item()
    confidence = top_probs[0][0].item()

    return id2tag[pred_id], confidence

# test
while True:
    text = input("You: ")
    intent, conf = predict_intent(text)
    print(f"Intent: {intent} (confidence: {conf:.2f})")