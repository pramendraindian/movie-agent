import json
import torch
from sklearn.model_selection import train_test_split
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset

# ========================
# Load and preprocess data
# ========================
with open("intents.json") as f:
    data = json.load(f)

texts = []
labels = []
tags = []

for intent in data["intents"]:
    tag = intent["tag"]
    tags.append(tag)
    for pattern in intent["patterns"]:
        texts.append(pattern)
        labels.append(tag)

# unique tags
tags = sorted(set(tags))
tag2id = {tag: i for i, tag in enumerate(tags)}
id2tag = {i: tag for tag, i in tag2id.items()}

labels = [tag2id[label] for label in labels]

# train/test split
train_texts, val_texts, train_labels, val_labels = train_test_split(
    texts, labels, test_size=0.2, random_state=42
)

# ========================
# Tokenization
# ========================
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)

# ========================
# Dataset class
# ========================
class IntentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = IntentDataset(train_encodings, train_labels)
val_dataset = IntentDataset(val_encodings, val_labels)

# ========================
# Model
# ========================
model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=len(tags)
)

# ========================
# Training config
# ========================
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    evaluation_strategy="epoch",
    logging_dir="./logs",
    save_strategy="epoch"
)

# ========================
# Trainer
# ========================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

# ========================
# Train
# ========================
trainer.train()

# ========================
# Save model
# ========================
model.save_pretrained("intent_model")
tokenizer.save_pretrained("intent_model")

# Save mappings
import pickle
with open("intent_model/meta.pkl", "wb") as f:
    pickle.dump({"tag2id": tag2id, "id2tag": id2tag}, f)

print("Training complete")