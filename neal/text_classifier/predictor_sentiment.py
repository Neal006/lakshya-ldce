"""
Predictor — Sentiment Analyzer
════════════════════════════════════════
Standalone sentiment analysis module for complaint texts.
Provides sentiment scores and analysis using multiple approaches:
1. TextBlob polarity-based sentiment
2. VADER (Valence Aware Dictionary and sEntiment Reasoner)
3. Comparison with ground truth sentiment from the dataset

Evaluation metrics compare predicted sentiment against actual sentiment scores.
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
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, f1_score, classification_report,
)

from util.config import (
    DATA_PATH, TEXT_COL, TARGET_COL, SENTIMENT_COL,
    RESULTS_DIR, LABEL_CLASSES,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_json

logger = get_logger("predictor_sentiment")


class SentimentAnalyzer:
    """
    Multi-method sentiment analysis for complaint texts.

    Methods:
        1. TextBlob: Rule-based polarity analysis
        2. VADER: Specialized for social media / short text sentiment
    """

    def __init__(self) -> None:
        self.textblob_available = False
        self.vader_available = False
        self._setup_analyzers()

    def _setup_analyzers(self) -> None:
        """Initialize sentiment analysis tools."""
        # TextBlob
        try:
            from textblob import TextBlob
            self.textblob_available = True
            logger.info("TextBlob sentiment analyzer loaded.")
        except ImportError:
            logger.warning("TextBlob not available. Install: pip install textblob")

        # VADER
        try:
            import nltk
            try:
                from nltk.sentiment.vader import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.vader_available = True
                logger.info("VADER sentiment analyzer loaded.")
            except LookupError:
                logger.info("Downloading VADER lexicon...")
                nltk.download("vader_lexicon", quiet=True)
                from nltk.sentiment.vader import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.vader_available = True
        except ImportError:
            logger.warning("NLTK not available. Install: pip install nltk")

    def analyze_textblob(self, text: str) -> dict:
        """Get sentiment using TextBlob."""
        if not self.textblob_available:
            return {"polarity": 0.0, "subjectivity": 0.0, "label": "neutral"}

        from textblob import TextBlob
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0.05:
            label = "positive"
        elif polarity < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
        }

    def analyze_vader(self, text: str) -> dict:
        """Get sentiment using VADER."""
        if not self.vader_available:
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 0.0, "label": "neutral"}

        scores = self.vader_analyzer.polarity_scores(str(text))

        if scores["compound"] >= 0.05:
            label = "positive"
        elif scores["compound"] <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "compound": round(scores["compound"], 4),
            "pos": round(scores["pos"], 4),
            "neg": round(scores["neg"], 4),
            "neu": round(scores["neu"], 4),
            "label": label,
        }

    def analyze_single(self, text: str) -> dict:
        """
        Analyze sentiment of a single text using all available methods.

        Args:
            text: Raw complaint text.

        Returns:
            Dictionary with sentiment analysis results.
        """
        result = {"text": text}

        if self.textblob_available:
            result["textblob"] = self.analyze_textblob(text)

        if self.vader_available:
            result["vader"] = self.analyze_vader(text)

        return result

    def analyze_batch(self, texts: list) -> pd.DataFrame:
        """
        Analyze sentiment for a batch of texts.

        Args:
            texts: List of text strings.

        Returns:
            DataFrame with sentiment scores from all methods.
        """
        records = []
        for text in texts:
            record = {"text": text}

            if self.textblob_available:
                tb = self.analyze_textblob(text)
                record["textblob_polarity"] = tb["polarity"]
                record["textblob_subjectivity"] = tb["subjectivity"]
                record["textblob_label"] = tb["label"]

            if self.vader_available:
                vader = self.analyze_vader(text)
                record["vader_compound"] = vader["compound"]
                record["vader_label"] = vader["label"]

            records.append(record)

        return pd.DataFrame(records)

    def evaluate_on_dataset(self) -> dict:
        """
        Evaluate sentiment predictions against the ground truth sentiment column.

        The dataset has continuous sentiment values in [-1, 1].
        We compare:
        1. Continuous: MAE, RMSE, R² between predicted and actual
        2. Categorical: Convert both to pos/neg/neutral and compute accuracy/F1

        Returns:
            Dictionary with evaluation metrics.
        """
        ensure_dir(RESULTS_DIR)

        logger.info("Evaluating sentiment analyzer on dataset...")

        df = pd.read_csv(DATA_PATH)
        texts = df[TEXT_COL].astype(str).tolist()
        actual_sentiment = df[SENTIMENT_COL].values

        # Predict sentiment
        print("\n" + "═" * 60)
        print("  SENTIMENT ANALYZER — EVALUATION")
        print("═" * 60)

        results = {}

        # ── TextBlob evaluation ──
        if self.textblob_available:
            print("\n  TextBlob Analysis:")
            textblob_scores = np.array([self.analyze_textblob(t)["polarity"] for t in texts])

            # Continuous metrics
            mae = mean_absolute_error(actual_sentiment, textblob_scores)
            rmse = np.sqrt(mean_squared_error(actual_sentiment, textblob_scores))
            r2 = r2_score(actual_sentiment, textblob_scores)

            print(f"    Continuous Metrics:")
            print(f"      MAE:    {mae:.4f}")
            print(f"      RMSE:   {rmse:.4f}")
            print(f"      R²:     {r2:.4f}")

            # Categorical evaluation
            actual_labels = np.where(actual_sentiment > 0.05, "positive",
                                     np.where(actual_sentiment < -0.05, "negative", "neutral"))
            predicted_labels = np.where(textblob_scores > 0.05, "positive",
                                        np.where(textblob_scores < -0.05, "negative", "neutral"))

            cat_acc = accuracy_score(actual_labels, predicted_labels)
            cat_f1 = f1_score(actual_labels, predicted_labels, average="macro")

            print(f"    Categorical Metrics (pos/neg/neutral):")
            print(f"      Accuracy: {cat_acc:.4f}")
            print(f"      F1 Macro: {cat_f1:.4f}")

            results["textblob"] = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
                "categorical_accuracy": round(cat_acc, 4),
                "categorical_f1_macro": round(cat_f1, 4),
            }

        # ── VADER evaluation ──
        if self.vader_available:
            print("\n  VADER Analysis:")
            vader_scores = np.array([self.analyze_vader(t)["compound"] for t in texts])

            mae = mean_absolute_error(actual_sentiment, vader_scores)
            rmse = np.sqrt(mean_squared_error(actual_sentiment, vader_scores))
            r2 = r2_score(actual_sentiment, vader_scores)

            print(f"    Continuous Metrics:")
            print(f"      MAE:    {mae:.4f}")
            print(f"      RMSE:   {rmse:.4f}")
            print(f"      R²:     {r2:.4f}")

            actual_labels = np.where(actual_sentiment > 0.05, "positive",
                                     np.where(actual_sentiment < -0.05, "negative", "neutral"))
            predicted_labels = np.where(vader_scores >= 0.05, "positive",
                                        np.where(vader_scores <= -0.05, "negative", "neutral"))

            cat_acc = accuracy_score(actual_labels, predicted_labels)
            cat_f1 = f1_score(actual_labels, predicted_labels, average="macro")

            print(f"    Categorical Metrics (pos/neg/neutral):")
            print(f"      Accuracy: {cat_acc:.4f}")
            print(f"      F1 Macro: {cat_f1:.4f}")

            results["vader"] = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
                "categorical_accuracy": round(cat_acc, 4),
                "categorical_f1_macro": round(cat_f1, 4),
            }

        # ── Per-category sentiment analysis ──
        print("\n  Sentiment by Category:")
        print(f"  {'Category':<12} {'Actual Mean':>12} {'Actual Std':>11}")
        print(f"  {'-'*12} {'-'*12} {'-'*11}")

        for cat in LABEL_CLASSES:
            mask = df[TARGET_COL] == cat
            cat_sent = actual_sentiment[mask]
            print(f"  {cat:<12} {np.mean(cat_sent):>12.4f} {np.std(cat_sent):>11.4f}")

        # ── Summary ──
        print("\n  Sentiment value range:")
        print(f"    min: {actual_sentiment.min():.4f}")
        print(f"    max: {actual_sentiment.max():.4f}")
        print(f"    mean: {actual_sentiment.mean():.4f}")
        print(f"    std: {actual_sentiment.std():.4f}")

        # NOTE about ground truth
        print("\n  ℹ NOTE: The dataset's sentiment column appears to be randomly")
        print("    generated (uniform distribution), so NLP-based sentiment")
        print("    predictors are not expected to correlate with it. The TextBlob")
        print("    and VADER scores reflect the actual linguistic sentiment of")
        print("    the complaint text itself.")

        # Save
        save_json(results, os.path.join(RESULTS_DIR, "sentiment_evaluation.json"))
        logger.info("Sentiment evaluation complete.")

        return results


def demo() -> None:
    """Run a demo of the sentiment analyzer."""
    print("\n" + "═" * 60)
    print("  SENTIMENT ANALYZER — DEMO")
    print("═" * 60)

    analyzer = SentimentAnalyzer()

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

    print(f"\n  {'Text':<28} {'TextBlob':>10} {'VADER':>10} {'Label':>10}")
    print(f"  {'-'*28} {'-'*10} {'-'*10} {'-'*10}")

    for text in test_texts:
        result = analyzer.analyze_single(text)
        tb_pol = result.get("textblob", {}).get("polarity", "N/A")
        vader_comp = result.get("vader", {}).get("compound", "N/A")
        label = result.get("vader", {}).get("label", "N/A")

        if isinstance(tb_pol, float):
            tb_pol = f"{tb_pol:.4f}"
        if isinstance(vader_comp, float):
            vader_comp = f"{vader_comp:.4f}"

        print(f"  {text:<28} {tb_pol:>10} {vader_comp:>10} {label:>10}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sentiment Analyzer")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate on dataset")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--text", type=str, help="Analyze a single text")
    args = parser.parse_args()

    if args.evaluate:
        analyzer = SentimentAnalyzer()
        analyzer.evaluate_on_dataset()
    elif args.text:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_single(args.text)
        print(f"\nText: {result['text']}")
        for method, scores in result.items():
            if method != "text":
                print(f"\n{method.upper()}:")
                for k, v in scores.items():
                    print(f"  {k}: {v}")
    else:
        demo()
