import os
from collections import Counter

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from util.config import (
    DATA_PATH, TEXT_COL, TARGET_COL, SENTIMENT_COL,
    PRIORITY_COL, RESOLUTION_TIME_COL, GRAPH_OP_DIR,
    LABEL_CLASSES,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_json, save_figure

logger = get_logger("data_analysis")

CLASS_COLORS = {"Trade": "#6C5CE7", "Packaging": "#00B894", "Product": "#E17055"}
PALETTE = list(CLASS_COLORS.values())


def run_eda() -> None:
    """Run the complete EDA pipeline and save all outputs to graph_op/."""

    ensure_dir(GRAPH_OP_DIR)

    # ── Load data ──
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded data: {df.shape[0]} rows × {df.shape[1]} columns")

    # SECTION A — Quantitative Analysis
    logger.info("Running quantitative analysis...")
    class_dist = df[TARGET_COL].value_counts().to_dict()
    class_pct = df[TARGET_COL].value_counts(normalize=True).mul(100).round(2).to_dict()
    text_lengths = df[TEXT_COL].astype(str).str.len()

    quant_summary = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "unique_texts": int(df[TEXT_COL].nunique()),
        "null_counts": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "class_distribution": {
            cat: {"count": int(class_dist.get(cat, 0)),
                  "percentage": float(class_pct.get(cat, 0))}
            for cat in LABEL_CLASSES
        },
        "text_length_stats": {
            "min": int(text_lengths.min()),
            "max": int(text_lengths.max()),
            "mean": round(float(text_lengths.mean()), 2),
            "median": float(text_lengths.median()),
            "std": round(float(text_lengths.std()), 2),
        },
    }
    save_json(quant_summary, os.path.join(GRAPH_OP_DIR, "quantitative_summary.json"))
    logger.info("Quantitative summary saved.")
    # SECTION B — Visual EDA
    logger.info("Generating EDA plots...")
    sns.set_style("whitegrid")
    plt.rcParams.update({"font.size": 11, "figure.figsize": (10, 6)})
    plot_count = 0
    # ── Plot 1: Class distribution bar chart ──
    fig, ax = plt.subplots(figsize=(10, 6))
    counts = df[TARGET_COL].value_counts()
    bars = ax.bar(counts.index, counts.values,
                  color=[CLASS_COLORS.get(c, "#636e72") for c in counts.index],
                  edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
                f"{val:,}", ha="center", va="bottom", fontweight="bold", fontsize=12)
    ax.set_title("Class Distribution", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category", fontsize=13)
    ax.set_ylabel("Count", fontsize=13)
    ax.set_ylim(0, counts.max() * 1.15)
    save_figure(fig, "plot_01_class_dist.png")
    plot_count += 1

    df["text_length"] = df[TEXT_COL].astype(str).str.len()
    fig, ax = plt.subplots(figsize=(10, 6))
    for cat in LABEL_CLASSES:
        subset = df[df[TARGET_COL] == cat]["text_length"]
        ax.hist(subset, bins=20, alpha=0.6, label=cat,
                color=CLASS_COLORS[cat], edgecolor="white")
    ax.set_title("Text Length Distribution by Category", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Character Count", fontsize=13)
    ax.set_ylabel("Frequency", fontsize=13)
    ax.legend(fontsize=11)
    save_figure(fig, "plot_02_text_length_dist.png")
    plot_count += 1

    # ── Plot 3: Heatmap — text vs category co-occurrence ──
    cross_tab = pd.crosstab(df[TEXT_COL], df[TARGET_COL])
    fig, ax = plt.subplots(figsize=(10, max(6, len(cross_tab) * 0.6)))
    sns.heatmap(cross_tab, annot=True, fmt="d", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Count"})
    ax.set_title("Text vs Category Co-occurrence Matrix", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category", fontsize=13)
    ax.set_ylabel("Text", fontsize=13)
    plt.yticks(rotation=0)
    save_figure(fig, "plot_03_text_category_heatmap.png")
    plot_count += 1

    # ── Plot 4: Pie chart — class share ──
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct="%1.1f%%",
        colors=[CLASS_COLORS.get(c, "#636e72") for c in counts.index],
        startangle=140, pctdistance=0.85,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_fontsize(12)
    centre = plt.Circle((0, 0), 0.65, fc="white")
    ax.add_artist(centre)
    ax.set_title("Class Share (Donut Chart)", fontsize=16, fontweight="bold", pad=20)
    save_figure(fig, "plot_04_class_pie.png")
    plot_count += 1

    # ── Plot 5: Sentiment distribution boxplot per category ──
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x=TARGET_COL, y=SENTIMENT_COL,
                palette=CLASS_COLORS, order=LABEL_CLASSES, ax=ax,
                flierprops={"marker": "o", "alpha": 0.3})
    ax.set_title("Sentiment Distribution by Category", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category", fontsize=13)
    ax.set_ylabel("Sentiment Score", fontsize=13)
    save_figure(fig, "plot_05_sentiment_boxplot.png")
    plot_count += 1

    # ── Plot 6: Priority distribution stacked bar per category ──
    priority_cross = pd.crosstab(df[TARGET_COL], df[PRIORITY_COL])
    priority_order = ["Low", "Medium", "High"]
    priority_cross = priority_cross.reindex(columns=priority_order, fill_value=0)
    priority_colors = {"Low": "#74b9ff", "Medium": "#ffeaa7", "High": "#ff7675"}
    fig, ax = plt.subplots(figsize=(10, 6))
    priority_cross.plot(kind="bar", stacked=True, ax=ax,
                        color=[priority_colors[p] for p in priority_order],
                        edgecolor="white", linewidth=1)
    ax.set_title("Priority Distribution by Category", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category", fontsize=13)
    ax.set_ylabel("Count", fontsize=13)
    ax.legend(title="Priority", fontsize=10)
    plt.xticks(rotation=0)
    save_figure(fig, "plot_06_priority_stacked.png")
    plot_count += 1

    # ── Plot 7: Resolution time violin plot per category ──
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=df, x=TARGET_COL, y=RESOLUTION_TIME_COL,
                   palette=CLASS_COLORS, order=LABEL_CLASSES, ax=ax,
                   inner="box", cut=0)
    ax.set_title("Resolution Time Distribution by Category", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Category", fontsize=13)
    ax.set_ylabel("Resolution Time (hours)", fontsize=13)
    save_figure(fig, "plot_07_resolution_time_violin.png")
    plot_count += 1

    # ── Plot 8: Correlation heatmap of numeric features ──
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        fig, ax = plt.subplots(figsize=(10, 8))
        corr_matrix = df[numeric_cols].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        sns.heatmap(corr_matrix, annot=True, fmt=".3f", cmap="coolwarm",
                    mask=mask, linewidths=0.5, ax=ax,
                    vmin=-1, vmax=1, center=0,
                    cbar_kws={"label": "Correlation"})
        ax.set_title("Correlation Heatmap (Numeric Features)", fontsize=16, fontweight="bold", pad=15)
        save_figure(fig, "plot_08_corr_heatmap.png")
        plot_count += 1

    # SECTION C — Qualitative Analysis
    logger.info("Running qualitative analysis...")

    unique_texts_per_cat = {}
    top_keywords_per_cat = {}

    for cat in LABEL_CLASSES:
        cat_texts = df[df[TARGET_COL] == cat][TEXT_COL].unique().tolist()
        unique_texts_per_cat[cat] = cat_texts

        # Simple word frequency
        all_words = " ".join(df[df[TARGET_COL] == cat][TEXT_COL].astype(str).str.lower()).split()
        word_freq = Counter(all_words)
        top_keywords_per_cat[cat] = dict(word_freq.most_common(15))

    qual_summary = {
        "unique_texts_per_category": unique_texts_per_cat,
        "top_keywords_per_category": top_keywords_per_cat,
    }

    save_json(qual_summary, os.path.join(GRAPH_OP_DIR, "qualitative_summary.json"))

    # Clean up temp column
    df.drop(columns=["text_length"], inplace=True, errors="ignore")

    print(f"✓ EDA complete. {plot_count} plots saved to graph_op/")
    logger.info(f"EDA complete. {plot_count} plots saved to {GRAPH_OP_DIR}")

if __name__ == "__main__":
    run_eda()
