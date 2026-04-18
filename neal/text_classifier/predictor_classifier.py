"""
Predictor — Category Classifier
════════════════════════════════════════
Standalone predictor for complaint category classification.
Uses the trained pipeline to classify new complaint texts into:
Trade | Packaging | Product

Includes model comparison against ground truth with full evaluation metrics.
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix, cohen_kappa_score,
    matthews_corrcoef,
)

from util.config import (
    DATA_PATH, TEXT_COL, TARGET_COL, MODELS_DIR, RESULTS_DIR,
    LABEL_CLASSES, RANDOM_STATE, TEST_SIZE,
)
from util.logger import get_logger
from util.file_utils import load_pickle, ensure_dir, save_json
from src.preprocessor import TextPreprocessor
from src.featureeng import FeatureEngineer

logger = get_logger("predictor_classifier")


class CategoryClassifier:
    """
    Production category classifier for complaint texts.
    Loads the trained model and preprocessors from disk and
    classifies new text inputs.
    """

    def __init__(self) -> None:
        self.model = None
        self.label_encoder = None
        self.preprocessor = TextPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained model and label encoder from disk."""
        # Find the tuned model
        model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith("_tuned.pkl")]
        if not model_files:
            # Fall back to base models
            model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith("_base.pkl")]

        if not model_files:
            raise FileNotFoundError(
                "No trained model found in models/. Run the pipeline first: "
                "python script/run_pipeline.py"
            )

        model_path = os.path.join(MODELS_DIR, model_files[0])
        self.model = load_pickle(model_path)
        logger.info(f"Loaded model: {model_files[0]}")

        # Load label encoder
        encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")
        self.label_encoder = load_pickle(encoder_path)
        logger.info(f"Loaded label encoder. Classes: {list(self.label_encoder.classes_)}")

    def predict_single(self, text: str) -> dict:
        """
        Classify a single complaint text.

        Args:
            text: Raw complaint text string.

        Returns:
            Dictionary with predicted category and probabilities.
        """
        # Create a mini DataFrame for the pipeline
        df = pd.DataFrame({
            TEXT_COL: [text],
            TARGET_COL: ["Unknown"],
            "sentiment": [0.0],
            "priority": ["Medium"],
            "resolution_time": [36],
        })

        df_clean = self.preprocessor.fit_transform(df)
        X = self.feature_engineer.transform(df_clean)

        pred_encoded = self.model.predict(X)[0]
        pred_category = self.label_encoder.inverse_transform([pred_encoded])[0]

        result = {"text": text, "predicted_category": pred_category}

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)[0]
            result["probabilities"] = {
                self.label_encoder.inverse_transform([i])[0]: round(float(p), 4)
                for i, p in enumerate(probs)
            }

        return result

    def predict_batch(self, texts: list) -> pd.DataFrame:
        """
        Classify a batch of complaint texts.

        Args:
            texts: List of raw complaint text strings.

        Returns:
            DataFrame with texts and predicted categories.
        """
        results = []
        for text in texts:
            result = self.predict_single(text)
            results.append(result)

        return pd.DataFrame(results)

    def evaluate_on_dataset(self) -> dict:
        """
        Evaluate the classifier on the original dataset using a proper train/test split.
        Compares predictions against ground truth labels.

        Returns:
            Dictionary with all evaluation metrics.
        """
        ensure_dir(RESULTS_DIR)

        logger.info("Evaluating category classifier on dataset...")

        # Load full dataset
        df = pd.read_csv(DATA_PATH)

        # Use same split as pipeline
        from sklearn.model_selection import train_test_split
        _, test_df = train_test_split(
            df, test_size=TEST_SIZE, stratify=df[TARGET_COL], random_state=RANDOM_STATE
        )
        test_df = test_df.reset_index(drop=True)

        # Get ground truth
        y_true_labels = test_df[TARGET_COL].values

        # Preprocess and extract features
        preprocessor = TextPreprocessor()
        test_clean = preprocessor.fit_transform(test_df)
        fe = FeatureEngineer()

        # We need to fit on training data first — load from saved artifacts
        X_test = fe.transform(test_clean)

        # Predict
        y_pred_encoded = self.model.predict(X_test)
        y_pred_labels = self.label_encoder.inverse_transform(y_pred_encoded)

        # Compute metrics
        y_true_encoded = self.label_encoder.transform(y_true_labels)

        metrics = {
            "accuracy": round(accuracy_score(y_true_encoded, y_pred_encoded), 4),
            "f1_macro": round(f1_score(y_true_encoded, y_pred_encoded, average="macro"), 4),
            "f1_weighted": round(f1_score(y_true_encoded, y_pred_encoded, average="weighted"), 4),
            "precision_macro": round(precision_score(y_true_encoded, y_pred_encoded, average="macro"), 4),
            "recall_macro": round(recall_score(y_true_encoded, y_pred_encoded, average="macro"), 4),
            "cohen_kappa": round(cohen_kappa_score(y_true_encoded, y_pred_encoded), 4),
            "mcc": round(matthews_corrcoef(y_true_encoded, y_pred_encoded), 4),
        }

        # Classification report
        report = classification_report(
            y_true_labels, y_pred_labels,
            target_names=LABEL_CLASSES,
            digits=4,
        )

        # Confusion matrix
        cm = confusion_matrix(y_true_encoded, y_pred_encoded)

        # Print results
        print("\n" + "═" * 60)
        print("  CATEGORY CLASSIFIER — EVALUATION RESULTS")
        print("═" * 60)
        print(f"\n  Test set size: {len(test_df)}")
        print(f"\n{report}")

        print("  Confusion Matrix:")
        print(f"  {' ':>15} {'|'.join(f'{c:>10}' for c in LABEL_CLASSES)}")
        for i, row in enumerate(cm):
            print(f"  {LABEL_CLASSES[i]:>15} {'|'.join(f'{v:>10}' for v in row)}")

        print(f"\n  Accuracy:      {metrics['accuracy']:.4f}")
        print(f"  F1 Macro:      {metrics['f1_macro']:.4f}")
        print(f"  F1 Weighted:   {metrics['f1_weighted']:.4f}")
        print(f"  MCC:           {metrics['mcc']:.4f}")
        print(f"  Cohen's Kappa: {metrics['cohen_kappa']:.4f}")

        # Save
        save_json(metrics, os.path.join(RESULTS_DIR, "classifier_evaluation.json"))
        logger.info("Category classifier evaluation complete.")

        return metrics


def demo() -> None:
    """Run a demo of the category classifier."""
    print("\n" + "═" * 60)
    print("  CATEGORY CLASSIFIER — DEMO")
    print("═" * 60)

    classifier = CategoryClassifier()

    test_texts = [
        "Need bulk order details",
        "Box was broken",
        "Product stopped working",
        "Poor packaging quality",
        "Inquiry about pricing",
        "Damaged packaging",
        "Product malfunctioning",
        "Trade-related query",
        "Defective item received",
    ]

    print("\n  Predictions:")
    print(f"  {'Text':<30} {'Predicted':>12}")
    print(f"  {'-'*30} {'-'*12}")

    for text in test_texts:
        result = classifier.predict_single(text)
        print(f"  {text:<30} {result['predicted_category']:>12}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Category Classifier")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation on dataset")
    parser.add_argument("--demo", action="store_true", help="Run demo predictions")
    parser.add_argument("--text", type=str, help="Classify a single text")
    args = parser.parse_args()

    if args.evaluate:
        classifier = CategoryClassifier()
        classifier.evaluate_on_dataset()
    elif args.text:
        classifier = CategoryClassifier()
        result = classifier.predict_single(args.text)
        print(f"\nText: {result['text']}")
        print(f"Category: {result['predicted_category']}")
        if "probabilities" in result:
            print(f"Probabilities: {result['probabilities']}")
    else:
        demo()
