# import json
# import numpy as np

# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity


# class SemanticIntentClassifier:

#     def __init__(self, intents_path="app/data/intents.json"):

#         # Load lightweight semantic model
#         self.model = SentenceTransformer("all-MiniLM-L6-v2")

#         # Load intents
#         with open(intents_path) as f:
#             data = json.load(f)

#         self.intent_examples = []
#         self.intent_tags = []

#         # Store all training examples
#         for intent in data["intents"]:

#             tag = intent["tag"]

#             # IMPORTANT:
#             # skip fallback intent
#             if tag == "fallback":
#                 continue

#             for pattern in intent["patterns"]:
#                 self.intent_examples.append(pattern)
#                 self.intent_tags.append(tag)

#         # Precompute embeddings once
#         self.embeddings = self.model.encode(
#             self.intent_examples,
#             convert_to_numpy=True
#         )

#     def predict(self, text):

#         # Encode user input
#         query_embedding = self.model.encode(
#             [text],
#             convert_to_numpy=True
#         )

#         # Cosine similarity
#         similarities = cosine_similarity(
#             query_embedding,
#             self.embeddings
#         )[0]

#         # Best match
#         best_idx = np.argmax(similarities)

#         intent = self.intent_tags[best_idx]
#         confidence = float(similarities[best_idx])

#         return intent, confidence

import json
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticIntentClassifier:

    def __init__(self, intents_path="app/data/new_intents.json"):

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        with open(intents_path) as f:
            data = json.load(f)

        self.intent_embeddings = {}
        self.intent_patterns = {}

        for intent in data["intents"]:

            tag = intent["tag"]

            patterns = intent["patterns"]

            embeddings = self.model.encode(
                patterns,
                convert_to_numpy=True
            )

            # centroid embedding
            centroid = np.mean(embeddings, axis=0)

            self.intent_embeddings[tag] = centroid
            self.intent_patterns[tag] = patterns

    def predict(self, text):

        query_embedding = self.model.encode(
            [text],
            convert_to_numpy=True
        )[0]

        scores = {}

        for tag, centroid in self.intent_embeddings.items():

            similarity = cosine_similarity(
                [query_embedding],
                [centroid]
            )[0][0]

            scores[tag] = similarity

        best_tag = max(scores, key=scores.get)

        return best_tag, float(scores[best_tag])