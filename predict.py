import torch
import pickle
from transformers import BertTokenizer, BertForSequenceClassification

# Load model
model = BertForSequenceClassification.from_pretrained("intent_model")
tokenizer = BertTokenizer.from_pretrained("intent_model")

with open("intent_model/meta.pkl", "rb") as f:
    meta = pickle.load(f)

id2tag = meta["id2tag"]

def predict_intent(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=1)
    pred_id = torch.argmax(probs).item()
    confidence = probs[0][pred_id].item()
    
    return id2tag[pred_id], confidence

# test
while True:
    text = input("You: ")
    intent, conf = predict_intent(text)
    print(f"Intent: {intent} (confidence: {conf:.2f})")