import torch

from app.models.intent_model import NeuralNet
from app.utils.nlp_utils import bag_of_words, tokenize


class BowIntentClassifier:
    STRATEGY = "bow"
    DEFAULT_THRESHOLD = 0.7

    def __init__(self, model_path="data.pth", threshold=None):
        data = torch.load(model_path, map_location="cpu")

        self.model_path = model_path
        self.strategy = data.get("strategy", self.STRATEGY)
        self.threshold = threshold if threshold is not None else data.get(
            "threshold", self.DEFAULT_THRESHOLD
        )

        model = NeuralNet(data["input_size"], data["hidden_size"], data["output_size"])
        model.load_state_dict(data["model_state"])
        model.eval()

        self._model = model
        self._all_words = data["all_words"]
        self._tags = data["tags"]

    def predict(self, text):
        X = bag_of_words(tokenize(text), self._all_words)
        X = torch.from_numpy(X).float()
        output = self._model(X)
        probs = torch.softmax(output, dim=0)
        conf, pred = torch.max(probs, dim=0)
        return self._tags[pred.item()], conf.item()
