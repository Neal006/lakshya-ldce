import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    cohen_kappa_score, matthews_corrcoef, roc_auc_score,
    log_loss, confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve, average_precision_score,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import label_binarize

from util.config import GRAPH_OP_DIR, RESULTS_DIR, LABEL_CLASSES
from util.logger import get_logger
from util.file_utils import ensure_dir, save_json, save_figure

logger = get_logger("evaluator")


class ModelEvaluator:
    """
    Full industry-grade model evaluation suite.

    Computes comprehensive metrics and generates publication-quality
    evaluation plots for the held-out test set.
    """

    def __init__(
        self,
        model: object,
        X_test: np.ndarray,
        y_test: np.ndarray,
        label_names: list,
        model_name: str,
        feature_names: list = None,
    ) -> None:
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.label_names = label_names
        self.model_name = model_name
        self.feature_names = feature_names

        # Predictions
        self.y_pred = model.predict(X_test)
        self.y_prob = self._get_probabilities()

    def _get_probabilities(self) -> np.ndarray:
        """Get probability predictions, using calibration if needed."""
        if hasattr(self.model, "predict_proba"):
            try:
                return self.model.predict_proba(self.X_test)
            except Exception:
                pass

        logger.warning("Model doesn't support predict_proba. Using decision_function or zeros.")
        if hasattr(self.model, "decision_function"):
            from scipy.special import softmax
            decisions = self.model.decision_function(self.X_test)
            return softmax(decisions, axis=1)

        # Fallback: one-hot encode predictions
        n_classes = len(self.label_names)
        probs = np.zeros((len(self.y_test), n_classes))
        for i, pred in enumerate(self.y_pred):
            probs[i, pred] = 1.0
        return probs

    def run_full_evaluation(self) -> dict:
        """
        Run the complete evaluation suite: metrics, plots, and reports.
        """
        ensure_dir(GRAPH_OP_DIR)
        ensure_dir(RESULTS_DIR)

        logger.info("=" * 60)
        logger.info(f"EVALUATING: {self.model_name}")
        logger.info("=" * 60)

        metrics = self._compute_metrics()
        self._save_classification_report()
        self._plot_confusion_matrix()
        self._plot_normalized_confusion_matrix()
        self._plot_roc_curve()
        self._plot_precision_recall_curve()
        self._plot_feature_importance()
        self._plot_classification_report_heatmap()

        # Save all metrics
        save_json(metrics, os.path.join(RESULTS_DIR, "evaluation_metrics.json"))

        # Print final summary
        self._print_final_summary(metrics)

        return metrics

    def _compute_metrics(self) -> dict:
        """Compute all evaluation metrics."""
        metrics = {}

        # Basic metrics
        metrics["accuracy"] = round(accuracy_score(self.y_test, self.y_pred), 4)
        metrics["f1_macro"] = round(f1_score(self.y_test, self.y_pred, average="macro"), 4)
        metrics["f1_micro"] = round(f1_score(self.y_test, self.y_pred, average="micro"), 4)
        metrics["f1_weighted"] = round(f1_score(self.y_test, self.y_pred, average="weighted"), 4)
        metrics["precision_macro"] = round(precision_score(self.y_test, self.y_pred, average="macro"), 4)
        metrics["precision_weighted"] = round(precision_score(self.y_test, self.y_pred, average="weighted"), 4)
        metrics["recall_macro"] = round(recall_score(self.y_test, self.y_pred, average="macro"), 4)
        metrics["recall_weighted"] = round(recall_score(self.y_test, self.y_pred, average="weighted"), 4)

        # Advanced metrics
        metrics["cohen_kappa"] = round(cohen_kappa_score(self.y_test, self.y_pred), 4)
        metrics["mcc"] = round(matthews_corrcoef(self.y_test, self.y_pred), 4)

        # ROC-AUC (one-vs-rest)
        try:
            n_classes = len(self.label_names)
            y_test_bin = label_binarize(self.y_test, classes=list(range(n_classes)))
            metrics["roc_auc_macro"] = round(
                roc_auc_score(y_test_bin, self.y_prob, average="macro", multi_class="ovr"), 4
            )
        except Exception as e:
            logger.warning(f"ROC-AUC calculation failed: {e}")
            metrics["roc_auc_macro"] = None

        # Log loss
        try:
            metrics["log_loss"] = round(log_loss(self.y_test, self.y_prob), 4)
        except Exception as e:
            logger.warning(f"Log loss calculation failed: {e}")
            metrics["log_loss"] = None

        # Confusion matrix
        cm = confusion_matrix(self.y_test, self.y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        cm_norm = confusion_matrix(self.y_test, self.y_pred, normalize="true")
        metrics["confusion_matrix_normalized"] = np.round(cm_norm, 4).tolist()

        metrics["model_name"] = self.model_name
        logger.info(f"All metrics computed for {self.model_name}")

        return metrics

    def _save_classification_report(self) -> None:
        """Save sklearn classification report to file."""
        report = classification_report(
            self.y_test, self.y_pred,
            target_names=self.label_names,
            digits=4,
        )
        report_path = os.path.join(RESULTS_DIR, "classification_report.txt")
        with open(report_path, "w") as f:
            f.write(f"Classification Report — {self.model_name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)
        logger.info(f"Classification report saved → {report_path}")

    def _plot_confusion_matrix(self) -> None:
        """Plot A: Confusion Matrix heatmap."""
        cm = confusion_matrix(self.y_test, self.y_pred)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                    xticklabels=self.label_names, yticklabels=self.label_names,
                    linewidths=0.5, ax=ax)
        ax.set_title(f"Confusion Matrix — {self.model_name}", fontsize=14, fontweight="bold")
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("Actual", fontsize=12)
        save_figure(fig, "eval_confusion_matrix.png")

    def _plot_normalized_confusion_matrix(self) -> None:
        """Plot B: Normalized Confusion Matrix."""
        cm = confusion_matrix(self.y_test, self.y_pred, normalize="true")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt=".3f", cmap="Blues",
                    xticklabels=self.label_names, yticklabels=self.label_names,
                    linewidths=0.5, ax=ax, vmin=0, vmax=1)
        ax.set_title(f"Normalized Confusion Matrix — {self.model_name}", fontsize=14, fontweight="bold")
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("Actual", fontsize=12)
        save_figure(fig, "eval_confusion_matrix_normalized.png")

    def _plot_roc_curve(self) -> None:
        """Plot C: ROC Curve (one curve per class, OvR)."""
        n_classes = len(self.label_names)
        y_test_bin = label_binarize(self.y_test, classes=list(range(n_classes)))

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = ["#6C5CE7", "#00B894", "#E17055"]

        for i, (name, color) in enumerate(zip(self.label_names, colors)):
            try:
                fpr, tpr, _ = roc_curve(y_test_bin[:, i], self.y_prob[:, i])
                roc_auc = auc(fpr, tpr)
                ax.plot(fpr, tpr, color=color, lw=2,
                        label=f"{name} (AUC = {roc_auc:.4f})")
            except Exception as e:
                logger.warning(f"ROC curve for class {name} failed: {e}")

        ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel("False Positive Rate", fontsize=12)
        ax.set_ylabel("True Positive Rate", fontsize=12)
        ax.set_title(f"ROC Curve (One-vs-Rest) — {self.model_name}", fontsize=14, fontweight="bold")
        ax.legend(loc="lower right", fontsize=11)
        ax.grid(True, alpha=0.3)
        save_figure(fig, "eval_roc_curve.png")

    def _plot_precision_recall_curve(self) -> None:
        """Plot D: Precision-Recall Curve (one per class)."""
        n_classes = len(self.label_names)
        y_test_bin = label_binarize(self.y_test, classes=list(range(n_classes)))

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = ["#6C5CE7", "#00B894", "#E17055"]

        for i, (name, color) in enumerate(zip(self.label_names, colors)):
            try:
                precision, recall, _ = precision_recall_curve(y_test_bin[:, i], self.y_prob[:, i])
                ap = average_precision_score(y_test_bin[:, i], self.y_prob[:, i])
                ax.plot(recall, precision, color=color, lw=2,
                        label=f"{name} (AP = {ap:.4f})")
            except Exception as e:
                logger.warning(f"PR curve for class {name} failed: {e}")

        ax.set_xlabel("Recall", fontsize=12)
        ax.set_ylabel("Precision", fontsize=12)
        ax.set_title(f"Precision-Recall Curve — {self.model_name}", fontsize=14, fontweight="bold")
        ax.legend(loc="lower left", fontsize=11)
        ax.grid(True, alpha=0.3)
        save_figure(fig, "eval_precision_recall_curve.png")

    def _plot_feature_importance(self) -> None:
        """Plot E: Feature importance (top 20, horizontal bar chart)."""
        try:
            if hasattr(self.model, "feature_importances_"):
                importances = self.model.feature_importances_
            elif hasattr(self.model, "coef_"):
                importances = np.abs(self.model.coef_).mean(axis=0)
            else:
                logger.info("Model doesn't support feature importance extraction. Skipping plot.")
                return

            if self.feature_names and len(self.feature_names) == len(importances):
                names = self.feature_names
            else:
                names = [f"feature_{i}" for i in range(len(importances))]

            # Top 20
            top_idx = np.argsort(importances)[-20:]
            top_names = [names[i] for i in top_idx]
            top_imp = importances[top_idx]

            fig, ax = plt.subplots(figsize=(10, 8))
            bars = ax.barh(range(len(top_names)), top_imp, color="#6C5CE7",
                           edgecolor="white", linewidth=0.5)
            ax.set_yticks(range(len(top_names)))
            ax.set_yticklabels(top_names, fontsize=10)
            ax.set_xlabel("Importance", fontsize=12)
            ax.set_title(f"Top 20 Feature Importance — {self.model_name}",
                         fontsize=14, fontweight="bold")
            ax.grid(True, axis="x", alpha=0.3)
            save_figure(fig, "eval_feature_importance.png")

        except Exception as e:
            logger.warning(f"Feature importance plot failed: {e}")

    def _plot_classification_report_heatmap(self) -> None:
        """Plot F: Classification report as a heatmap."""
        report_dict = classification_report(
            self.y_test, self.y_pred,
            target_names=self.label_names,
            output_dict=True,
        )

        # Build heatmap data (per-class only)
        heatmap_data = []
        for name in self.label_names:
            if name in report_dict:
                heatmap_data.append([
                    report_dict[name]["precision"],
                    report_dict[name]["recall"],
                    report_dict[name]["f1-score"],
                ])

        df_report = pd.DataFrame(
            heatmap_data,
            index=self.label_names,
            columns=["Precision", "Recall", "F1-Score"],
        )

        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(df_report, annot=True, fmt=".4f", cmap="YlGnBu",
                    linewidths=0.5, ax=ax, vmin=0, vmax=1,
                    cbar_kws={"label": "Score"})
        ax.set_title(f"Classification Report — {self.model_name}",
                     fontsize=14, fontweight="bold")
        ax.set_ylabel("")
        save_figure(fig, "eval_classification_report_heatmap.png")

    def _print_final_summary(self, metrics: dict) -> None:
        """Print the final evaluation summary box."""
        acc = metrics.get("accuracy", 0)
        f1 = metrics.get("f1_macro", 0)
        mcc = metrics.get("mcc", 0)
        roc = metrics.get("roc_auc_macro", "N/A")
        kappa = metrics.get("cohen_kappa", 0)

        roc_str = f"{roc:.4f}" if isinstance(roc, (int, float)) else str(roc)

        summary = f"""
FINAL EVALUATION RESULTS
Model       : {self.model_name:<25}
Accuracy    : {acc*100:.2f}%{' '*21}
F1 Macro    : {f1:.4f}{' '*22}
MCC         : {mcc:.4f}{' '*22}
ROC-AUC     : {roc_str:<26}
Kappa       : {kappa:.4f}{' '*22}
"""

        print(summary)
        logger.info(summary)


if __name__ == "__main__":
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier

    X, y = make_classification(n_samples=1000, n_features=20, n_classes=3,
                                n_informative=15, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    evaluator = ModelEvaluator(model, X_test, y_test, ["A", "B", "C"], "RandomForest_test")
    metrics = evaluator.run_full_evaluation()
