"""
MASTER PIPELINE RUNNER — NLP-Only Text Classification Engine
═══════════════════════════════════════════════════════════════
Pure NLP approach using fine-tuned DistilBERT transformer.
NO traditional ML models — the transformer learns everything from text.

Categories: Trade | Packaging | Product
Usage: python script/run_pipeline.py
"""

import sys
import os
import warnings

# Fix Windows Unicode encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Fix imports: add project root to path ──
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

# ════════════════════════════════════════════
# FLAGS — Easy to toggle
# ════════════════════════════════════════════
RUN_EDA             = False   # Set True only first time
NUM_EPOCHS          = 5       # Transformer training epochs
BATCH_SIZE          = 32      # Batch size for training
LEARNING_RATE       = 2e-5    # DistilBERT fine-tuning LR
RUN_KFOLD           = True    # Run K-Fold cross-validation

# ════════════════════════════════════════════
# IMPORTS
# ════════════════════════════════════════════
from util.config import (
    DATA_PATH, TEXT_COL, TARGET_COL, RANDOM_STATE,
    TEST_SIZE, VAL_SIZE, LABEL_CLASSES,
    GRAPH_OP_DIR, MODELS_DIR, RESULTS_DIR,
)
from util.logger import get_logger
from util.timer import timeit, Timer, TIMING_REGISTRY
from util.file_utils import ensure_dir, save_json

from src.data_analysis import run_eda
from src.preprocessor import TextPreprocessor
from src.trainer import TransformerTrainer
from src.evaluator import ModelEvaluator

logger = get_logger("run_pipeline")

# Set global random seed
np.random.seed(RANDOM_STATE)


def print_banner() -> None:
    """Print the pipeline ASCII banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🚀 NLP TEXT CLASSIFICATION PIPELINE                             ║
║   ─────────────────────────────────                               ║
║   Model:       DistilBERT (Fine-tuned Transformer)                ║
║   Categories:  Trade  │  Packaging  │  Product                    ║
║   Approach:    Pure NLP — No Traditional ML Models                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    logger.info("Pipeline started (NLP-only mode).")


# ════════════════════════════════════════════
# STEP 0 — Setup
# ════════════════════════════════════════════
def setup() -> None:
    """Create all output directories."""
    for d in [GRAPH_OP_DIR, MODELS_DIR, RESULTS_DIR]:
        ensure_dir(d)
    logger.info("Output directories created/verified.")


# ════════════════════════════════════════════
# STEP 1 — Load Data
# ════════════════════════════════════════════
@timeit
def load_data() -> pd.DataFrame:
    """Load and validate the raw dataset."""
    logger.info(f"Loading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Class distribution:\n{df[TARGET_COL].value_counts().to_string()}")

    # Validate
    assert df[TEXT_COL].isnull().sum() == 0, f"Nulls found in {TEXT_COL}!"
    assert df[TARGET_COL].isnull().sum() == 0, f"Nulls found in {TARGET_COL}!"

    return df


# ════════════════════════════════════════════
# STEP 2 — EDA
# ════════════════════════════════════════════
@timeit
def run_eda_step() -> None:
    """Run exploratory data analysis (conditional)."""
    if RUN_EDA:
        logger.info("Running EDA...")
        run_eda()
    else:
        logger.info("EDA skipped — set RUN_EDA=True to run")


# ════════════════════════════════════════════
# STEP 3 — Preprocessing
# ════════════════════════════════════════════
@timeit
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply text preprocessing pipeline."""
    logger.info("Starting text preprocessing...")
    preprocessor = TextPreprocessor()
    df_clean = preprocessor.fit_transform(df)
    return df_clean


# ════════════════════════════════════════════
# STEP 4 — Train/Val/Test Split
# ════════════════════════════════════════════
@timeit
def split_data(df: pd.DataFrame) -> tuple:
    """Stratified train/val/test split."""
    logger.info("Splitting data into train/val/test...")

    y = df["label"].values

    # First split: 80% train+val / 20% test
    train_val_idx, test_idx = train_test_split(
        np.arange(len(df)),
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    # Second split: ~90% train / ~10% val from train+val
    train_val_y = y[train_val_idx]
    relative_val_size = VAL_SIZE / (1 - TEST_SIZE)

    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=relative_val_size,
        stratify=train_val_y,
        random_state=RANDOM_STATE,
    )

    train_df = df.iloc[train_idx].reset_index(drop=True)
    val_df = df.iloc[val_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    logger.info(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    for split_name, split_df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        dist = split_df[TARGET_COL].value_counts().to_dict()
        logger.info(f"  {split_name} class distribution: {dist}")

    return train_df, val_df, test_df


# ════════════════════════════════════════════
# STEP 5 — Train DistilBERT Transformer
# ════════════════════════════════════════════
@timeit
def train_transformer(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
) -> TransformerTrainer:
    """Fine-tune DistilBERT for complaint classification."""
    logger.info("Starting DistilBERT fine-tuning...")

    trainer = TransformerTrainer(
        model_name="distilbert-base-uncased",
        num_labels=len(LABEL_CLASSES),
        max_length=64,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        num_epochs=NUM_EPOCHS,
    )

    # Get texts and labels
    train_texts = train_df[TEXT_COL].astype(str).tolist()
    train_labels = train_df["label"].values
    val_texts = val_df[TEXT_COL].astype(str).tolist()
    val_labels = val_df["label"].values

    # Train
    results = trainer.train(train_texts, train_labels, val_texts, val_labels)

    # Load the best checkpoint
    trainer.load_model()

    return trainer


# ════════════════════════════════════════════
# STEP 6 — Final Evaluation on Test Set
# ════════════════════════════════════════════
@timeit
def evaluate_model(
    trainer: TransformerTrainer,
    test_df: pd.DataFrame,
) -> dict:
    """Run full evaluation on the held-out test set."""
    logger.info("Running final evaluation on test set...")

    test_texts = test_df[TEXT_COL].astype(str).tolist()
    y_test = test_df["label"].values

    # Get predictions
    y_pred, y_probs = trainer.predict(test_texts)

    # Use the evaluator for comprehensive metrics and plots
    evaluator = ModelEvaluator(
        model=None,  # We pass predictions directly
        X_test=None,
        y_test=y_test,
        label_names=LABEL_CLASSES,
        model_name="DistilBERT_finetuned",
        feature_names=[],
    )

    # Override with our predictions
    evaluator.y_pred = y_pred
    evaluator.y_prob = y_probs

    metrics = evaluator.run_full_evaluation()
    return metrics


# ════════════════════════════════════════════
# STEP 7 — Stratified K-Fold Cross-Validation
# ════════════════════════════════════════════
@timeit
def run_kfold_validation(
    df: pd.DataFrame,
) -> dict:
    """Run stratified K-fold cross-validation with DistilBERT."""
    if not RUN_KFOLD:
        logger.info("K-Fold validation skipped — set RUN_KFOLD=True to enable")
        return {}

    from util.config import KFOLD_SPLITS
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    logger.info(f"Running {KFOLD_SPLITS}-Fold Stratified Cross-Validation with DistilBERT...")

    texts = df[TEXT_COL].astype(str).tolist()
    labels = df["label"].values

    skf = StratifiedKFold(n_splits=KFOLD_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    fold_results = {
        "accuracy": [],
        "f1_macro": [],
        "precision_macro": [],
        "recall_macro": [],
    }

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(texts, labels)):
        fold_train_texts = [texts[i] for i in train_idx]
        fold_train_labels = labels[train_idx]
        fold_test_texts = [texts[i] for i in test_idx]
        fold_test_labels = labels[test_idx]

        # Quick train (fewer epochs for K-fold)
        fold_trainer = TransformerTrainer(
            num_labels=len(LABEL_CLASSES),
            max_length=64,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            num_epochs=2,  # Fewer epochs for K-fold efficiency
        )

        # Split some of train as val
        val_size = int(len(fold_train_texts) * 0.1)
        fold_val_texts = fold_train_texts[:val_size]
        fold_val_labels = fold_train_labels[:val_size]
        fold_train_texts_actual = fold_train_texts[val_size:]
        fold_train_labels_actual = fold_train_labels[val_size:]

        fold_trainer.train(
            fold_train_texts_actual, fold_train_labels_actual,
            fold_val_texts, fold_val_labels
        )
        fold_trainer.load_model()

        y_pred, _ = fold_trainer.predict(fold_test_texts)

        fold_results["accuracy"].append(accuracy_score(fold_test_labels, y_pred))
        fold_results["f1_macro"].append(f1_score(fold_test_labels, y_pred, average="macro"))
        fold_results["precision_macro"].append(precision_score(fold_test_labels, y_pred, average="macro"))
        fold_results["recall_macro"].append(recall_score(fold_test_labels, y_pred, average="macro"))

        logger.info(
            f"  Fold {fold_idx + 1}/{KFOLD_SPLITS}: "
            f"Acc={fold_results['accuracy'][-1]:.4f} | "
            f"F1={fold_results['f1_macro'][-1]:.4f}"
        )

        # Free GPU memory
        del fold_trainer
        if hasattr(torch, 'cuda'):
            torch.cuda.empty_cache()

    # Summary
    kfold_summary = {}
    for metric, values in fold_results.items():
        mean_val = np.mean(values)
        std_val = np.std(values)
        kfold_summary[metric] = {
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "per_fold": [round(v, 4) for v in values],
            "summary": f"{mean_val:.4f} ± {std_val:.4f}",
        }
        logger.info(f"  {metric}: {mean_val:.4f} ± {std_val:.4f}")

    # Save results
    save_json(kfold_summary, os.path.join(RESULTS_DIR, "kfold_results.json"))

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.boxplot(
        [fold_results["accuracy"], fold_results["f1_macro"],
         fold_results["precision_macro"], fold_results["recall_macro"]],
        labels=["Accuracy", "F1 Macro", "Precision", "Recall"],
        patch_artist=True,
        boxprops=dict(facecolor="#6C5CE7", alpha=0.6),
        medianprops=dict(color="white", linewidth=2),
    )
    ax.set_title(f"{KFOLD_SPLITS}-Fold Cross-Validation — DistilBERT",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12)
    ax.grid(True, alpha=0.3)
    from util.file_utils import save_figure
    save_figure(fig, "kfold_f1_distribution.png")

    return kfold_summary


# ════════════════════════════════════════════
# STEP 8 — Save Final Summary
# ════════════════════════════════════════════
def save_final_summary(
    metrics: dict,
    kfold_summary: dict,
) -> None:
    """Aggregate all timings and results into a final summary."""
    import torch

    total_seconds = sum(TIMING_REGISTRY.values())
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    total_runtime = f"{minutes}m {seconds}s"

    kfold_f1_str = kfold_summary.get("f1_macro", {}).get("summary", "N/A") if kfold_summary else "N/A"

    summary = {
        "approach": "Pure NLP — DistilBERT Fine-tuned Transformer",
        "model": "distilbert-base-uncased (fine-tuned)",
        "test_accuracy": metrics.get("accuracy", 0),
        "f1_macro": metrics.get("f1_macro", 0),
        "mcc": metrics.get("mcc", 0),
        "roc_auc_macro": metrics.get("roc_auc_macro", 0),
        "kfold_mean_f1": kfold_f1_str,
        "total_runtime": total_runtime,
        "device": str(torch.device("cuda" if torch.cuda.is_available() else "cpu")),
        "num_epochs": NUM_EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "step_timings": {k: f"{v:.2f}s" for k, v in TIMING_REGISTRY.items()},
    }

    save_json(summary, os.path.join(RESULTS_DIR, "pipeline_summary.json"))

    print(f"\n✅ Pipeline complete. Results in results/ | Plots in graph_op/")
    print(f"   Total runtime: {total_runtime}")
    logger.info(f"Pipeline complete. Total runtime: {total_runtime}")


# ════════════════════════════════════════════
# MAIN — Orchestrate everything
# ════════════════════════════════════════════
def main() -> None:
    """Run the complete NLP text classification pipeline."""
    import torch

    print_banner()

    # STEP 0 — Setup
    setup()

    # STEP 1 — Load Data
    df = load_data()

    # STEP 2 — EDA
    run_eda_step()

    # STEP 3 — Preprocessing
    df_clean = preprocess_data(df)

    # STEP 4 — Train/Val/Test Split
    train_df, val_df, test_df = split_data(df_clean)

    # STEP 5 — Train DistilBERT Transformer (pure NLP)
    trainer = train_transformer(train_df, val_df)

    # STEP 6 — Final Evaluation on Test Set
    metrics = evaluate_model(trainer, test_df)

    # STEP 7 — K-Fold Cross-Validation
    train_val_df = pd.concat([train_df, val_df]).reset_index(drop=True)
    kfold_summary = run_kfold_validation(train_val_df)

    # STEP 8 — Save Final Summary
    save_final_summary(metrics, kfold_summary)


if __name__ == "__main__":
    main()
