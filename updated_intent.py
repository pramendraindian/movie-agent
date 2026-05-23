from updated_predict import predict_intent

while True:

    text = input("You: ")

    intent, conf = predict_intent(text)

    print(f"\nIntent: {intent}")
    print(f"Confidence: {conf:.4f}")