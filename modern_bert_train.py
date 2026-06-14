import json
import pickle
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn.functional as F
import evaluate

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from torch.utils.data import Dataset

from intents import INTENT_DESCRIPTIONS

MODEL_NAME = "answerdotai/ModernBERT-base"
MAX_LENGTH = 128
DATA_PATH = "app/data/updated_intents.json"
SAVE_PATH = "intent_model"
PLOT_DIR = Path("Notebooks")
NEGATIVES_PER_EXAMPLE = 3
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def generate_pairs(examples: list[dict]) -> tuple[list[str], list[str], list[int]]:
    sentence1, sentence2, labels = [], [], []
    all_intents = list(INTENT_DESCRIPTIONS.keys())

    for ex in examples:
        text = ex["text"]
        correct_intent = ex["intent"]

        sentence1.append(text)
        sentence2.append(INTENT_DESCRIPTIONS[correct_intent])
        labels.append(1)

        negative_intents = [i for i in all_intents if i != correct_intent]
        sampled_negatives = random.sample(
            negative_intents,
            min(NEGATIVES_PER_EXAMPLE, len(negative_intents)),
        )
        for negative_intent in sampled_negatives:
            sentence1.append(text)
            sentence2.append(INTENT_DESCRIPTIONS[negative_intent])
            labels.append(0)

    return sentence1, sentence2, labels


class IntentPairDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.labels)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return evaluate.load("accuracy").compute(predictions=predictions, references=labels)


def predict_intent(text: str, model, tokenizer) -> tuple[str, float]:
    scores = {}
    model.eval()
    with torch.no_grad():
        for intent, description in INTENT_DESCRIPTIONS.items():
            inputs = tokenizer(
                text,
                description,
                return_tensors="pt",
                truncation=True,
                max_length=MAX_LENGTH,
            )
            outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            scores[intent] = probs[0][1].item()
    best_intent, confidence = max(scores.items(), key=lambda item: item[1])
    return best_intent, confidence


def plot_training_curves(log_history: list[dict], output_path: Path) -> None:
    train_losses = [
        entry["loss"] for entry in log_history if "loss" in entry and "eval_loss" not in entry
    ]
    eval_losses = [
        (entry["epoch"], entry["eval_loss"])
        for entry in log_history
        if "eval_loss" in entry
    ]
    eval_accuracies = [
        (entry["epoch"], entry["eval_accuracy"])
        for entry in log_history
        if "eval_accuracy" in entry
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    if train_losses:
        axes[0].plot(range(1, len(train_losses) + 1), train_losses, color="#e74c3c", linewidth=1.8)
        axes[0].set_title("Training Loss (step-level)")
        axes[0].set_xlabel("Logging step")
        axes[0].set_ylabel("Loss")
        axes[0].grid(True, alpha=0.3)

    if eval_losses:
        epochs, losses = zip(*eval_losses)
        axes[1].plot(epochs, losses, color="#3498db", linewidth=1.8, marker="o", label="Eval loss")
    if eval_accuracies:
        epochs, accs = zip(*eval_accuracies)
        ax2 = axes[1].twinx()
        ax2.plot(epochs, [a * 100 for a in accs], color="#2ecc71", linewidth=1.8, marker="s", label="Pair accuracy")
        ax2.set_ylabel("Pair accuracy (%)")
        ax2.legend(loc="upper right")

    axes[1].set_title("Validation Metrics per Epoch")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Eval loss")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper left")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved training curves → {output_path}")


def plot_confusion_matrix(y_true, y_pred, labels, output_path: Path) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
    )
    ax.set_xlabel("Predicted intent")
    ax.set_ylabel("True intent")
    ax.set_title("ModernBERT Intent Confusion Matrix (utterance-level val set)")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved confusion matrix → {output_path}")


def main() -> None:
    with open(DATA_PATH, encoding="utf-8") as f:
        examples = json.load(f)["examples"]

    train_examples, val_examples = train_test_split(
        examples,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=[ex["intent"] for ex in examples],
    )

    train_s1, train_s2, train_labels = generate_pairs(train_examples)
    val_s1, val_s2, val_labels = generate_pairs(val_examples)

    print(f"Examples: train={len(train_examples)}, val={len(val_examples)}")
    print(f"Pairs: train={len(train_labels)}, val={len(val_labels)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_encodings = tokenizer(train_s1, train_s2, truncation=True, max_length=MAX_LENGTH)
    val_encodings = tokenizer(val_s1, val_s2, truncation=True, max_length=MAX_LENGTH)

    train_dataset = IntentPairDataset(train_encodings, train_labels)
    val_dataset = IntentPairDataset(val_encodings, val_labels)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

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
        report_to="none",
        seed=RANDOM_SEED,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    plot_training_curves(
        trainer.state.log_history,
        PLOT_DIR / "bert_training_curves.png",
    )

    intent_labels = list(INTENT_DESCRIPTIONS.keys())
    y_true, y_pred = [], []
    for ex in val_examples:
        pred, _ = predict_intent(ex["text"], model, tokenizer)
        y_true.append(ex["intent"])
        y_pred.append(pred)

    print("\nUtterance-level validation report:")
    print(classification_report(y_true, y_pred, labels=intent_labels, zero_division=0))

    plot_confusion_matrix(
        y_true,
        y_pred,
        intent_labels,
        PLOT_DIR / "bert_confusion_matrix.png",
    )

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
            f,
        )

    print("\nTraining complete")


if __name__ == "__main__":
    main()
