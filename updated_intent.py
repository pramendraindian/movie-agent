from updated_predict import predict_intent

while True:

    text = input("You: ")

    intent, conf = predict_intent(text)

    print(f"\nIntent: {intent}")
    print(f"Confidence: {conf:.4f}")


# from predict import predict_intent

# test_queries = [

#     "i want a funny movie",
#     "movies with mind blowing twists",
#     "suggest good sci fi films",

#     "how do i learn machine learning",
#     "best coding tutorials",
#     "good resources for backend engineering",

#     "hello there",
#     "goodbye friend",

#     "book me flight tickets",
#     "what is the stock market today",

#     # unseen conversational examples

#     "i need something entertaining tonight",
#     "teach me artificial intelligence",
#     "movies for date night",
#     "can you order pizza"
# ]

# for query in test_queries:

#     print("\n===================================")

#     print(f"Query: {query}")

#     intent, confidence = predict_intent(query)

#     print(f"\nFinal Intent: {intent}")

#     print(f"Confidence: {confidence:.4f}")