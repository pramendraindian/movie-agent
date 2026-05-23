import json
import random
import pickle
import torch
import evaluate
import numpy as np

from sklearn.model_selection import train_test_split

from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments
)

from torch.utils.data import Dataset

# ==================================================
# Intent descriptions
# ==================================================

INTENT_DESCRIPTIONS = {

    "greeting":
    "user is greeting, saying hello, hi, hey, or starting a conversation",

    "goodbye":
    "user is ending the conversation, saying goodbye, bye, see you later, or farewell",

    "movie_recommendation":
    "user is asking for movie recommendations, films to watch, entertainment suggestions, genres, actors, trending movies, or movies based on mood",

    "learning_recommendation":
    "user is asking for learning resources, tutorials, programming courses, coding help, educational content, or study material",

    "fallback":
    "message is unrelated, unsupported, random, nonsensical, or outside supported chatbot capabilities"
}

# ==================================================
# Load dataset
# ==================================================

with open("app/data/updated_intents.json") as f:
    data = json.load(f)

examples = data["examples"]

# ==================================================
# Generate positive + negative sentence pairs
# ==================================================

sentence1 = []
sentence2 = []
labels = []

all_intents = list(INTENT_DESCRIPTIONS.keys())

for ex in examples:

    text = ex["text"]
    correct_intent = ex["intent"]

    # ----------------------------
    # Positive pair
    # ----------------------------

    sentence1.append(text)
    sentence2.append(INTENT_DESCRIPTIONS[correct_intent])
    labels.append(1)

    # ----------------------------
    # Negative pairs
    # ----------------------------

    negative_intents = [
        i for i in all_intents
        if i != correct_intent
    ]

    for negative_intent in negative_intents:

        sentence1.append(text)

        sentence2.append(
            INTENT_DESCRIPTIONS[negative_intent]
        )

        labels.append(0)

# ==================================================
# Train/test split
# ==================================================

train_s1, val_s1, train_s2, val_s2, train_labels, val_labels = train_test_split(
    sentence1,
    sentence2,
    labels,
    test_size=0.2,
    random_state=42
)

# ==================================================
# Tokenizer
# ==================================================

tokenizer = BertTokenizer.from_pretrained(
    "bert-base-uncased"
)

# train_encodings = tokenizer(
#     train_s1,
#     train_s2,
#     truncation=True,
#     padding=True,
#     max_length=64
# )

# val_encodings = tokenizer(
#     val_s1,
#     val_s2,
#     truncation=True,
#     padding=True
# )

train_encodings = tokenizer(
    train_s1,
    train_s2,
    truncation=True,
    padding="max_length",
    max_length=64
)

val_encodings = tokenizer(
    val_s1,
    val_s2,
    truncation=True,
    padding="max_length",
    max_length=64
)

# Metrics
accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):

    logits, labels = eval_pred

    predictions = np.argmax(logits, axis=-1)

    return accuracy_metric.compute(
        predictions=predictions,
        references=labels
    )

# ==================================================
# Dataset class
# ==================================================

class IntentPairDataset(Dataset):

    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):

        item = {
            k: torch.tensor(v[idx])
            for k, v in self.encodings.items()
        }

        item["labels"] = torch.tensor(self.labels[idx])

        return item

    def __len__(self):
        return len(self.labels)

train_dataset = IntentPairDataset(
    train_encodings,
    train_labels
)

val_dataset = IntentPairDataset(
    val_encodings,
    val_labels
)

# ==================================================
# Model
# ==================================================

model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=2
)

# ==================================================
# Training args
# ==================================================

training_args = TrainingArguments(
    output_dir="./results",
    # num_train_epochs=10,
    learning_rate=2e-5,
    num_train_epochs=5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_steps=5,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    warmup_ratio=0.1,
    fp16=False
)

# ==================================================
# Trainer
# ==================================================

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

# ==================================================
# Train
# ==================================================

trainer.train()

# ==================================================
# Save model
# ==================================================

model.save_pretrained("intent_model")
tokenizer.save_pretrained("intent_model")

with open("intent_model/meta.pkl", "wb") as f:
    pickle.dump(
        {
            "intent_descriptions": INTENT_DESCRIPTIONS
        },
        f
    )

print("Training complete")