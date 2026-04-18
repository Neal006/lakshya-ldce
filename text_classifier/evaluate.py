import os
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.preprocessing import label_binarize

from nlp import ComplaintClassifier, CATEGORY_LABELS

warnings.filterwarnings("ignore")

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "data.csv")

CATEGORY_LABELS = ["Trade", "Product", "Packaging"]
PRIORITY_LABELS = ["High", "Low", "Medium"]


def evaluate():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)

    print("Initializing classifier...\n")
    clf = ComplaintClassifier(DATA_PATH)

    y_true_cat = []
    y_pred_cat = []
    y_true_pri = []
    y_pred_pri = []
    y_cat_proba = []

    total = len(df)
    print(f"Processing {total} rows...\n")

    batch_size = 500
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        print(f"  Rows {start + 1}-{end} / {total}")
        for idx in range(start, end):
            row = df.iloc[idx]
            result = clf.process(row["complaint_id"], row["text"])

            y_true_cat.append(row["category"])
            y_pred_cat.append(result["Category"])
            y_true_pri.append(row["priority"])
            y_pred_pri.append(result["Priority"])

    y_true_cat = np.array(y_true_cat)
    y_pred_cat = np.array(y_pred_cat)
    y_true_pri = np.array(y_true_pri)
    y_pred_pri = np.array(y_pred_pri)

    cat_proba_df = _compute_category_probabilities(clf, df)

    print("CATEGORY CLASSIFICATION METRICS")

    _print_metrics(
        y_true_cat, y_pred_cat, cat_proba_df, CATEGORY_LABELS, "Category"
    )

    print("PRIORITY CLASSIFICATION METRICS")

    pri_proba_df = _compute_priority_probabilities(clf, df, y_pred_cat)

    _print_metrics(
        y_true_pri, y_pred_pri, pri_proba_df, PRIORITY_LABELS, "Priority"
    )

    print("SENTIMENT CORRELATION")

    pred_sentiments = df["text"].apply(
        lambda x: clf.get_sentiment_score(x)
    ).values
    true_sentiments = df["sentiment"].values
    corr = np.corrcoef(pred_sentiments, true_sentiments)[0, 1]
    print(f"\n  Pearson Correlation (VADER vs Ground Truth): {corr:.4f}")
    mae = np.mean(np.abs(pred_sentiments - true_sentiments))
    print(f"  Mean Absolute Error:                        {mae:.4f}")
    rmse = np.sqrt(np.mean((pred_sentiments - true_sentiments) ** 2))
    print(f"  Root Mean Squared Error:                     {rmse:.4f}")

    print("OVERALL SUMMARY")
    
    cat_acc = accuracy_score(y_true_cat, y_pred_cat)
    pri_acc = accuracy_score(y_true_pri, y_pred_pri)

    cat_f1 = f1_score(y_true_cat, y_pred_cat, average="weighted")
    pri_f1 = f1_score(y_true_pri, y_pred_pri, average="weighted")

    print(f"\n  Category Accuracy:  {cat_acc:.4f} ({cat_acc * 100:.2f}%)")
    print(f"  Category F1:       {cat_f1:.4f}")
    print(f"  Priority Accuracy:  {pri_acc:.4f} ({pri_acc * 100:.2f}%)")
    print(f"  Priority F1:       {pri_f1:.4f}")
    print(f"  Sentiment Corr:     {corr:.4f}")


def _compute_category_probabilities(clf, df):
    print("  Computing category probabilities for AUC-ROC...")
    proba_rows = []
    for _, row in df.iterrows():
        _, confidences = clf.predict_category(row["text"])
        proba_rows.append([confidences[c] for c in CATEGORY_LABELS])
    return pd.DataFrame(proba_rows, columns=CATEGORY_LABELS)


def _compute_priority_probabilities(clf, df, y_pred_cat):
    print("  Computing priority probabilities for AUC-ROC...")
    proba_rows = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        sentiment = clf.get_sentiment_score(row["text"])
        features = _priority_features(clf, row["text"], y_pred_cat[idx], sentiment)
        proba = clf.priority_model.predict_proba(features)[0]
        class_order = clf.le_pri.classes_
        row_dict = {}
        for i, cls in enumerate(class_order):
            row_dict[cls] = proba[i]
        proba_rows.append(row_dict)
    return pd.DataFrame(proba_rows, columns=PRIORITY_LABELS)


def _priority_features(clf, text, category, sentiment_score):
    cat_encoded = clf.le_cat.transform([category])[0]
    text_len = len(text)
    word_count = len(text.split())
    abs_sentiment = abs(sentiment_score)
    return np.array([[sentiment_score, abs_sentiment, cat_encoded, text_len, word_count]])


def _print_metrics(y_true, y_pred, proba_df, labels, task_name):
    acc = accuracy_score(y_true, y_pred)
    prec_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    prec_weighted = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec_weighted = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    y_true_bin = label_binarize(y_true, classes=labels)
    y_score = proba_df[labels].values

    if y_true_bin.shape[1] == 1:
        y_true_bin = np.hstack([1 - y_true_bin, y_true_bin])
        y_score = np.hstack([1 - y_score, y_score])

    auc_ovr = roc_auc_score(y_true_bin, y_score, multi_class="ovr", average="macro")

    print(f"\n  {task_name} Accuracy:              {acc:.4f} ({acc * 100:.2f}%)")
    print(f"  {task_name} Precision (Macro):      {prec_macro:.4f}")
    print(f"  {task_name} Recall (Macro):         {rec_macro:.4f}")
    print(f"  {task_name} F1 Score (Macro):       {f1_macro:.4f}")
    print(f"  {task_name} Precision (Weighted):   {prec_weighted:.4f}")
    print(f"  {task_name} Recall (Weighted):      {rec_weighted:.4f}")
    print(f"  {task_name} F1 Score (Weighted):    {f1_weighted:.4f}")
    print(f"  {task_name} AUC-ROC (OvR Macro):    {auc_ovr:.4f}")

    print(f"\n  Per-Class Metrics ({task_name}):")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print(f"  Confusion Matrix ({task_name}):")
    _print_confusion_matrix(cm, labels)


def _print_confusion_matrix(cm, labels):
    header = "         " + "  ".join(f"{l:>10}" for l in labels)
    print(f"  {header}")
    print(f"  {'─' * len(header)}")
    for i, label in enumerate(labels):
        row_str = "  ".join(f"{cm[i][j]:>10}" for j in range(len(labels)))
        print(f"  {label:>10}  {row_str}")
    print()


if __name__ == "__main__":
    evaluate()