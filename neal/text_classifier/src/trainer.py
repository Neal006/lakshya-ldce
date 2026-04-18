"""
NLP Trainer — Fine-tunes a DistilBERT transformer for text classification.

This is a pure NLP approach:
- DistilBERT tokenizer handles text → token IDs
- DistilBERT model learns its own internal representations
- Classification head maps representations → class labels
- NO traditional ML models (no sklearn classifiers, no XGBoost, etc.)

The model LEARNS which text patterns correspond to which class
from the training data — no static keyword mapping.
"""

import os
import time

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, f1_score

from util.config import MODELS_DIR, RANDOM_STATE, LABEL_CLASSES
from util.logger import get_logger
from util.file_utils import ensure_dir, save_json

logger = get_logger("trainer")

# Reproducibility
torch.manual_seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


class ComplaintDataset(Dataset):
    """PyTorch Dataset for complaint text classification."""

    def __init__(self, texts: list, labels: np.ndarray, tokenizer, max_length: int = 64):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        text = str(self.texts[idx])
        label = int(self.labels[idx])

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


class TransformerTrainer:
    """
    Fine-tunes a DistilBERT model for multi-class text classification.

    This is 100% NLP — no traditional ML models involved.
    The transformer learns its own feature representations internally.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        num_labels: int = 3,
        max_length: int = 64,
        batch_size: int = 32,
        learning_rate: float = 2e-5,
        num_epochs: int = 5,
        warmup_ratio: float = 0.1,
        device: str = None,
    ) -> None:
        self.model_name = model_name
        self.num_labels = num_labels
        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.warmup_ratio = warmup_ratio

        # Auto-detect GPU
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Device: {self.device}")

        self.tokenizer = None
        self.model = None
        self.training_history: list = []

    def _load_model(self) -> None:
        """Load the pre-trained DistilBERT model and tokenizer."""
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

        logger.info(f"Loading pre-trained model: {self.model_name}")

        self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
        self.model = DistilBertForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=self.num_labels,
        )
        self.model.to(self.device)

        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info(f"Total parameters: {total_params:,}")
        logger.info(f"Trainable parameters: {trainable_params:,}")

    def _create_dataloader(self, texts: list, labels: np.ndarray, shuffle: bool = True) -> DataLoader:
        """Create a DataLoader from texts and labels."""
        dataset = ComplaintDataset(texts, labels, self.tokenizer, self.max_length)
        return DataLoader(dataset, batch_size=self.batch_size, shuffle=shuffle)

    def train(
        self,
        train_texts: list,
        train_labels: np.ndarray,
        val_texts: list,
        val_labels: np.ndarray,
    ) -> dict:
        """
        Fine-tune the DistilBERT model.

        Returns:
            Dictionary with training history and best metrics.
        """
        self._load_model()

        train_loader = self._create_dataloader(train_texts, train_labels, shuffle=True)
        val_loader = self._create_dataloader(val_texts, val_labels, shuffle=False)

        # Optimizer
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate, weight_decay=0.01)

        # Learning rate scheduler with warmup
        total_steps = len(train_loader) * self.num_epochs
        warmup_steps = int(total_steps * self.warmup_ratio)

        from transformers import get_linear_schedule_with_warmup
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        logger.info("=" * 60)
        logger.info("TRANSFORMER FINE-TUNING")
        logger.info("=" * 60)
        logger.info(f"Model:          {self.model_name}")
        logger.info(f"Epochs:         {self.num_epochs}")
        logger.info(f"Batch size:     {self.batch_size}")
        logger.info(f"Learning rate:  {self.learning_rate}")
        logger.info(f"Train samples:  {len(train_texts)}")
        logger.info(f"Val samples:    {len(val_texts)}")
        logger.info(f"Total steps:    {total_steps}")
        logger.info(f"Warmup steps:   {warmup_steps}")

        best_val_f1 = 0.0
        best_epoch = 0

        for epoch in range(self.num_epochs):
            epoch_start = time.perf_counter()

            # ── Training phase ──
            self.model.train()
            total_loss = 0
            train_preds = []
            train_true = []

            for batch_idx, batch in enumerate(train_loader):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].to(self.device)

                optimizer.zero_grad()

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                loss = outputs.loss
                total_loss += loss.item()

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()

                # Collect predictions
                preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
                train_preds.extend(preds)
                train_true.extend(labels.cpu().numpy())

            avg_train_loss = total_loss / len(train_loader)
            train_acc = accuracy_score(train_true, train_preds)
            train_f1 = f1_score(train_true, train_preds, average="macro")

            # ── Validation phase ──
            val_acc, val_f1, val_loss = self._evaluate(val_loader)

            epoch_time = time.perf_counter() - epoch_start

            # Record history
            epoch_record = {
                "epoch": epoch + 1,
                "train_loss": round(avg_train_loss, 4),
                "train_acc": round(train_acc, 4),
                "train_f1": round(train_f1, 4),
                "val_loss": round(val_loss, 4),
                "val_acc": round(val_acc, 4),
                "val_f1": round(val_f1, 4),
                "lr": scheduler.get_last_lr()[0],
                "time": round(epoch_time, 1),
            }
            self.training_history.append(epoch_record)

            logger.info(
                f"Epoch {epoch + 1}/{self.num_epochs} | "
                f"Train Loss: {avg_train_loss:.4f} | Train F1: {train_f1:.4f} | "
                f"Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f} | "
                f"Val Acc: {val_acc:.4f} | Time: {epoch_time:.1f}s"
            )

            # Save best model
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch + 1
                self._save_model()
                logger.info(f"  ★ New best model saved (F1={val_f1:.4f})")

        logger.info(f"\nBest epoch: {best_epoch} | Best val F1: {best_val_f1:.4f}")

        # Save training history
        save_json(self.training_history, os.path.join(MODELS_DIR, "training_history.json"))
        self._plot_training_curves()

        return {
            "best_epoch": best_epoch,
            "best_val_f1": best_val_f1,
            "training_history": self.training_history,
        }

    def _evaluate(self, dataloader: DataLoader) -> tuple:
        """Evaluate model on a dataloader."""
        self.model.eval()
        all_preds = []
        all_labels = []
        total_loss = 0

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                total_loss += outputs.loss.item()
                preds = torch.argmax(outputs.logits, dim=-1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.cpu().numpy())

        avg_loss = total_loss / len(dataloader)
        acc = accuracy_score(all_labels, all_preds)
        f1 = f1_score(all_labels, all_preds, average="macro")

        return acc, f1, avg_loss

    def predict(self, texts: list) -> tuple:
        """
        Get predictions and probabilities for a list of texts.

        Returns:
            (predictions, probabilities) tuple.
        """
        self.model.eval()
        all_preds = []
        all_probs = []

        dataset = ComplaintDataset(texts, np.zeros(len(texts)), self.tokenizer, self.max_length)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits

                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                preds = np.argmax(probs, axis=-1)

                all_preds.extend(preds)
                all_probs.extend(probs)

        return np.array(all_preds), np.array(all_probs)

    def _save_model(self) -> None:
        """Save the fine-tuned model and tokenizer."""
        ensure_dir(MODELS_DIR)
        model_path = os.path.join(MODELS_DIR, "distilbert_finetuned")
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(model_path)
        logger.info(f"Model saved → {model_path}")

    def load_model(self) -> None:
        """Load a previously saved fine-tuned model."""
        from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

        model_path = os.path.join(MODELS_DIR, "distilbert_finetuned")
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Loaded fine-tuned model from {model_path}")

    def _plot_training_curves(self) -> None:
        """Plot training and validation loss/F1 curves."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from util.file_utils import save_figure

        epochs = [r["epoch"] for r in self.training_history]
        train_loss = [r["train_loss"] for r in self.training_history]
        val_loss = [r["val_loss"] for r in self.training_history]
        train_f1 = [r["train_f1"] for r in self.training_history]
        val_f1 = [r["val_f1"] for r in self.training_history]

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Loss curve
        axes[0].plot(epochs, train_loss, "o-", label="Train Loss", color="#6C5CE7", linewidth=2)
        axes[0].plot(epochs, val_loss, "s-", label="Val Loss", color="#E17055", linewidth=2)
        axes[0].set_xlabel("Epoch")
        axes[0].set_ylabel("Loss")
        axes[0].set_title("Training & Validation Loss", fontweight="bold")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # F1 curve
        axes[1].plot(epochs, train_f1, "o-", label="Train F1", color="#6C5CE7", linewidth=2)
        axes[1].plot(epochs, val_f1, "s-", label="Val F1", color="#E17055", linewidth=2)
        axes[1].set_xlabel("Epoch")
        axes[1].set_ylabel("F1 Macro")
        axes[1].set_title("Training & Validation F1 Score", fontweight="bold")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        save_figure(fig, "training_curves.png")


if __name__ == "__main__":
    print("Trainer module — use via run_pipeline.py")
