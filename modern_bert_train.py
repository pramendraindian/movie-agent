import json
import random
import pickle
import numpy as np
import torch
import evaluate

from sklearn.model_selection import train_test_split

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)

from torch.utils.data import Dataset

from intents import INTENT_DESCRIPTIONS

# ==================================================
# Config
# ==================================================

MODEL_NAME = "answerdotai/ModernBERT-base"

MAX_LENGTH = 128

# ==================================================
# Load dataset
# ==================================================

with open("app/data/updated_intents.json") as f:
    data = json.load(f)

examples = data["examples"]

# ==================================================
# Generate sentence pairs
# ==================================================

sentence1 = []
sentence2 = []
labels = []

all_intents = list(INTENT_DESCRIPTIONS.keys())

for ex in examples:

    text = ex["text"]
    correct_intent = ex["intent"]

    # --------------------------------------
    # Positive pair
    # --------------------------------------

    sentence1.append(text)

    sentence2.append(
        INTENT_DESCRIPTIONS[correct_intent]
    )

    labels.append(1)

    # --------------------------------------
    # Negative pairs
    # --------------------------------------

    negative_intents = [
        i for i in all_intents
        if i != correct_intent
    ]

    # Optional:
    # sample fewer negatives
    sampled_negatives = random.sample(
        negative_intents,
        min(3, len(negative_intents))
    )

    for negative_intent in sampled_negatives:

        sentence1.append(text)

        sentence2.append(
            INTENT_DESCRIPTIONS[negative_intent]
        )

        labels.append(0)

# ==================================================
# Train / validation split
# ==================================================

(
    train_s1,
    val_s1,
    train_s2,
    val_s2,
    train_labels,
    val_labels
) = train_test_split(
    sentence1,
    sentence2,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

# ==================================================
# Tokenizer
# ==================================================

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

train_encodings = tokenizer(
    train_s1,
    train_s2,
    truncation=True,
    max_length=MAX_LENGTH
)

val_encodings = tokenizer(
    val_s1,
    val_s2,
    truncation=True,
    max_length=MAX_LENGTH
)

# ==================================================
# Dataset
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

        item["labels"] = torch.tensor(
            self.labels[idx],
            dtype=torch.long
        )

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
# Metrics
# ==================================================

accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):

    logits, labels = eval_pred

    predictions = np.argmax(
        logits,
        axis=-1
    )

    return accuracy_metric.compute(
        predictions=predictions,
        references=labels
    )

# ==================================================
# Model
# ==================================================

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2
)

# ==================================================
# Dynamic padding
# ==================================================

data_collator = DataCollatorWithPadding(
    tokenizer=tokenizer
)

# ==================================================
# Training args
# ==================================================

training_args = TrainingArguments(

    output_dir="./results",

    learning_rate=2e-5,

    num_train_epochs=5,

    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,

    weight_decay=0.01,

    eval_strategy="epoch",

    save_strategy="epoch",

    logging_steps=10,

    load_best_model_at_end=True,

    metric_for_best_model="eval_loss",

    warmup_ratio=0.1,

    fp16=torch.cuda.is_available(),

    save_total_limit=2,

    report_to="none"
)

# ==================================================
# Trainer
# ==================================================

trainer = Trainer(

    model=model,

    args=training_args,

    train_dataset=train_dataset,

    eval_dataset=val_dataset,

    data_collator=data_collator,

    compute_metrics=compute_metrics
)

# ==================================================
# Train
# ==================================================

trainer.train()

# ==================================================
# Save
# ==================================================

SAVE_PATH = "intent_model"

model.save_pretrained(SAVE_PATH)

tokenizer.save_pretrained(SAVE_PATH)

with open(f"{SAVE_PATH}/meta.pkl", "wb") as f:

    pickle.dump(
        {
            "strategy": "sentence_pair",
            "intent_descriptions": INTENT_DESCRIPTIONS,
            "model_name": MODEL_NAME,
            "max_length": MAX_LENGTH,
            "threshold": 0.65,
        },
        f
    )

print("\nTraining complete")