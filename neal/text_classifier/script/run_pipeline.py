import sys
import os
import warnings

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

RUN_EDA             = False   # Set True only first time
USE_NLP_EMBEDDINGS  = True    # Set False for faster runs
N_OPTUNA_TRIALS     = 50
RUN_KFOLD           = True
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
from src.featureeng import FeatureEngineer
from src.nlp import NLPLayer
from src.trainer import ModelTrainer
from src.optuna_tuner import OptunaTuner
from src.evaluator import ModelEvaluator

logger = get_logger("run_pipeline")

# Set global random seed
np.random.seed(RANDOM_STATE)


def print_banner() -> None:
    """Print the pipeline ASCII banner."""
    banner = """🚀 TEXT CLASSIFICATION PIPELINE"""
    print(banner)
    logger.info("Pipeline started.")


def setup() -> None:
    """Create all output directories."""
    for d in [GRAPH_OP_DIR, MODELS_DIR, RESULTS_DIR]:
        ensure_dir(d)
    logger.info("Output directories created/verified.")

@timeit
def load_data() -> pd.DataFrame:
    """Load and validate the raw dataset."""
    logger.info(f"Loading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Class distribution:\n{df[TARGET_COL].value_counts().to_string()}")
    logger.info(f"Null counts:\n{df.isnull().sum().to_string()}")

    # Validate
    assert df[TEXT_COL].isnull().sum() == 0, f"Nulls found in {TEXT_COL}!"
    assert df[TARGET_COL].isnull().sum() == 0, f"Nulls found in {TARGET_COL}!"

    return df


@timeit
def run_eda_step() -> None:
    """Run exploratory data analysis (conditional)."""
    if RUN_EDA:
        logger.info("Running EDA...")
        run_eda()
    else:
        logger.info("EDA skipped — set RUN_EDA=True to run")


@timeit
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply text preprocessing pipeline."""
    logger.info("Starting text preprocessing...")
    preprocessor = TextPreprocessor()
    df_clean = preprocessor.fit_transform(df)
    return df_clean


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
    relative_val_size = VAL_SIZE / (1 - TEST_SIZE)  # ~0.125

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

@timeit
def engineer_features(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    """Build feature matrices for all splits."""
    logger.info("Starting feature engineering...")

    fe = FeatureEngineer()
    X_train, feature_names = fe.fit_transform(train_df)
    X_val = fe.transform(val_df)
    X_test = fe.transform(test_df)

    logger.info(f"X_train: {X_train.shape} | X_val: {X_val.shape} | X_test: {X_test.shape}")

    return X_train, X_val, X_test, feature_names


@timeit
def add_nlp_embeddings(
    train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame,
    X_train: np.ndarray, X_val: np.ndarray, X_test: np.ndarray,
) -> tuple:
    """Add sentence embeddings to the feature matrix (optional)."""
    if not USE_NLP_EMBEDDINGS:
        logger.info("NLP embeddings skipped — set USE_NLP_EMBEDDINGS=True to enable")
        return X_train, X_val, X_test

    logger.info("Computing NLP embeddings...")
    nlp_layer = NLPLayer()

    train_texts = train_df[TEXT_COL].astype(str).tolist()
    val_texts = val_df[TEXT_COL].astype(str).tolist()
    test_texts = test_df[TEXT_COL].astype(str).tolist()
    all_texts = train_texts + val_texts + test_texts
    all_embeds = nlp_layer.get_embedding_features(all_texts, fit=True, use_cache=False)

    n_train = len(train_texts)
    n_val = len(val_texts)
    embed_train = all_embeds[:n_train]
    embed_val = all_embeds[n_train:n_train + n_val]
    embed_test = all_embeds[n_train + n_val:]

    X_train = np.hstack([X_train, embed_train])
    X_val = np.hstack([X_val, embed_val])
    X_test = np.hstack([X_test, embed_test])

    logger.info(f"After embeddings — X_train: {X_train.shape} | X_val: {X_val.shape} | X_test: {X_test.shape}")

    return X_train, X_val, X_test

@timeit
def train_baseline_models(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
) -> tuple:
    """Train all baseline models and get the best one."""
    logger.info("Training baseline models...")

    trainer = ModelTrainer(X_train, y_train, X_val, y_val)
    results = trainer.train_all()

    best_name, best_model = trainer.get_best_model()
    trainer.save_model(best_model, best_name)

    return best_name, best_model, results

@timeit
def optimize_hyperparameters(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    best_name: str,
) -> tuple:
    """Run Optuna tuning on the best model."""
    logger.info(f"Starting Optuna tuning for {best_name}...")

    tuner = OptunaTuner(
        X_train, y_train, X_val, y_val,
        model_name=best_name,
        n_trials=N_OPTUNA_TRIALS,
    )
    tuned_model, best_params, best_score = tuner.tune()

    return tuned_model, best_params, best_score

@timeit
def evaluate_model(
    tuned_model: object,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str,
    feature_names: list,
) -> dict:
    """Run full evaluation on the held-out test set."""
    logger.info("Running final evaluation on test set...")

    evaluator = ModelEvaluator(
        model=tuned_model,
        X_test=X_test,
        y_test=y_test,
        label_names=LABEL_CLASSES,
        model_name=f"{model_name}_tuned",
        feature_names=feature_names,
    )
    metrics = evaluator.run_full_evaluation()
    return metrics

@timeit
def run_kfold_validation(
    tuned_model: object,
    X_trainval: np.ndarray,
    y_trainval: np.ndarray,
    model_name: str,
) -> dict:
    """Run stratified K-fold cross-validation."""
    if not RUN_KFOLD:
        logger.info("K-Fold validation skipped — set RUN_KFOLD=True to enable")
        return {}

    from util.config import KFOLD_SPLITS
    import matplotlib.pyplot as plt

    logger.info(f"Running {KFOLD_SPLITS}-Fold Stratified Cross-Validation...")

    skf = StratifiedKFold(n_splits=KFOLD_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    fold_results = {
        "accuracy": [],
        "f1_macro": [],
        "precision_macro": [],
        "recall_macro": [],
    }

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X_trainval, y_trainval)):
        X_fold_train = X_trainval[train_idx]
        y_fold_train = y_trainval[train_idx]
        X_fold_test = X_trainval[test_idx]
        y_fold_test = y_trainval[test_idx]

        # Clone the model with same params
        from sklearn.base import clone
        fold_model = clone(tuned_model)
        fold_model.fit(X_fold_train, y_fold_train)
        y_pred = fold_model.predict(X_fold_test)

        fold_results["accuracy"].append(accuracy_score(y_fold_test, y_pred))
        fold_results["f1_macro"].append(f1_score(y_fold_test, y_pred, average="macro"))
        fold_results["precision_macro"].append(precision_score(y_fold_test, y_pred, average="macro"))
        fold_results["recall_macro"].append(recall_score(y_fold_test, y_pred, average="macro"))

        logger.info(
            f"  Fold {fold_idx + 1}/{KFOLD_SPLITS}: "
            f"Acc={fold_results['accuracy'][-1]:.4f} | "
            f"F1={fold_results['f1_macro'][-1]:.4f}"
        )

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

    # Plot: box plot of f1_macro across folds
    fig, ax = plt.subplots(figsize=(8, 6))
    bp = ax.boxplot(
        [fold_results["accuracy"], fold_results["f1_macro"],
         fold_results["precision_macro"], fold_results["recall_macro"]],
        labels=["Accuracy", "F1 Macro", "Precision", "Recall"],
        patch_artist=True,
        boxprops=dict(facecolor="#6C5CE7", alpha=0.6),
        medianprops=dict(color="white", linewidth=2),
    )
    ax.set_title(f"{KFOLD_SPLITS}-Fold Cross-Validation Results — {model_name}",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12)
    ax.grid(True, alpha=0.3)
    from util.file_utils import save_figure
    save_figure(fig, "kfold_f1_distribution.png")

    return kfold_summary

def save_final_summary(
    model_name: str,
    metrics: dict,
    kfold_summary: dict,
    feature_names: list,
) -> None:
    """Aggregate all timings and results into a final summary."""

    # Calculate total runtime
    total_seconds = sum(TIMING_REGISTRY.values())
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    total_runtime = f"{minutes}m {seconds}s"

    features_used = ["tfidf", "statistical", "domain", "metadata"]
    if USE_NLP_EMBEDDINGS:
        features_used.append("nlp_embeddings")

    kfold_f1_str = kfold_summary.get("f1_macro", {}).get("summary", "N/A") if kfold_summary else "N/A"

    summary = {
        "model": f"{model_name}_tuned",
        "test_accuracy": metrics.get("accuracy", 0),
        "f1_macro": metrics.get("f1_macro", 0),
        "mcc": metrics.get("mcc", 0),
        "roc_auc_macro": metrics.get("roc_auc_macro", 0),
        "kfold_mean_f1": kfold_f1_str,
        "total_runtime": total_runtime,
        "features_used": features_used,
        "n_optuna_trials": N_OPTUNA_TRIALS,
        "step_timings": {k: f"{v:.2f}s" for k, v in TIMING_REGISTRY.items()},
    }

    save_json(summary, os.path.join(RESULTS_DIR, "pipeline_summary.json"))

    print(f"\n✅ Pipeline complete. Results in results/ | Plots in graph_op/")
    print(f"   Total runtime: {total_runtime}")
    logger.info(f"Pipeline complete. Total runtime: {total_runtime}")

def main() -> None:
    """Run the complete text classification pipeline."""

    print_banner()
    setup()
    df = load_data()
    run_eda_step()
    df_clean = preprocess_data(df)
    train_df, val_df, test_df = split_data(df_clean)

    y_train = train_df["label"].values
    y_val = val_df["label"].values
    y_test = test_df["label"].values

    X_train, X_val, X_test, feature_names = engineer_features(train_df, val_df, test_df)

    X_train, X_val, X_test = add_nlp_embeddings(
        train_df, val_df, test_df, X_train, X_val, X_test
    )

    if USE_NLP_EMBEDDINGS:
        from util.config import PCA_COMPONENTS
        embed_names = [f"embed_pca_{i}" for i in range(PCA_COMPONENTS)]
        feature_names = feature_names + embed_names

    best_name, best_model, baseline_results = train_baseline_models(
        X_train, y_train, X_val, y_val
    )
    tuned_model, best_params, best_score = optimize_hyperparameters(
        X_train, y_train, X_val, y_val, best_name
    )
    metrics = evaluate_model(tuned_model, X_test, y_test, best_name, feature_names)
    X_trainval = np.vstack([X_train, X_val])
    y_trainval = np.concatenate([y_train, y_val])
    kfold_summary = run_kfold_validation(tuned_model, X_trainval, y_trainval, best_name)
    save_final_summary(best_name, metrics, kfold_summary, feature_names)

if __name__ == "__main__":
    main()
