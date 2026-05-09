from app.models.bert_intent_model import BertIntentClassifier

clf = BertIntentClassifier()

while True:
    text = input("You: ")
    intent, conf = clf.predict(text)
    print(f"Intent: {intent}, Confidence: {conf:.2f}")


# from app.models.semantic_intent_model import SemanticIntentClassifier

# clf = SemanticIntentClassifier()

# while True:
#     text = input("You: ")

#     intent, conf = clf.predict(text)

#     print(f"Intent: {intent}")
#     print(f"Confidence: {conf:.2f}")