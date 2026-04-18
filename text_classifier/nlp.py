import os
import warnings
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

warnings.filterwarnings("ignore")

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "data.csv")
CATEGORY_LABELS = ["Trade", "Product", "Packaging"]


class ComplaintClassifier:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path
        self.df = pd.read_csv(data_path)

        print("[1/5] Loading zero-shot classifier (DistilBERT-MNLI)...")
        self.zs_classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1,
        )

        print("[2/5] Loading semantic similarity model (MiniLM-L6)...")
        self.sim_model = SentenceTransformer("all-MiniLM-L6-v2")

        print("[3/5] Initializing VADER sentiment analyzer...")
        self.vader = SentimentIntensityAnalyzer()

        print("[4/5] Building reference embeddings for semantic similarity...")
        self.ref_map = {}
        self.ref_embeddings = {}
        for cat in CATEGORY_LABELS:
            texts = self.df[self.df["category"] == cat]["text"].unique().tolist()
            self.ref_map[cat] = texts
            self.ref_embeddings[cat] = self.sim_model.encode(
                texts, convert_to_tensor=True, normalize_embeddings=True
            )

        print("[5/5] Training smart priority model from data...")
        self._train_priority_model()
        print("All models ready!\n")

    def _train_priority_model(self):
        self.le_cat = LabelEncoder()
        self.le_pri = LabelEncoder()

        vader_scores = self.df["text"].apply(
            lambda x: self.vader.polarity_scores(x)["compound"]
        )

        self.df["_vader"] = vader_scores
        self.df["_cat_enc"] = self.le_cat.fit_transform(self.df["category"])
        self.df["_pri_enc"] = self.le_pri.fit_transform(self.df["priority"])
        self.df["_text_len"] = self.df["text"].str.len()
        self.df["_word_count"] = self.df["text"].str.split().str.len()

        self.df["_abs_sentiment"] = self.df["_vader"].abs()

        X = self.df[
            ["_vader", "_abs_sentiment", "_cat_enc", "_text_len", "_word_count"]
        ].values
        y = self.df["_pri_enc"].values

        self.priority_model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self.priority_model.fit(X, y)

    def predict_category(self, text):
        zs_result = self.zs_classifier(text, CATEGORY_LABELS, multi_label=False)
        zs_scores = {}
        for label, score in zip(zs_result["labels"], zs_result["scores"]):
            zs_scores[label] = score
        zs_probs = np.array([zs_scores.get(c, 0.0) for c in CATEGORY_LABELS])
        zs_probs = zs_probs / zs_probs.sum()

        query_emb = self.sim_model.encode(
            text, convert_to_tensor=True, normalize_embeddings=True
        )
        sim_scores = {}
        for cat in CATEGORY_LABELS:
            sims = util.cos_sim(query_emb, self.ref_embeddings[cat])
            sim_scores[cat] = float(sims.max())

        sim_vals = np.array([sim_scores[c] for c in CATEGORY_LABELS])
        shifted = sim_vals - sim_vals.min() + 1e-9
        sim_probs = shifted / shifted.sum()

        ensemble_probs = 0.5 * zs_probs + 0.5 * sim_probs
        ensemble_probs = ensemble_probs / ensemble_probs.sum()

        best_idx = int(np.argmax(ensemble_probs))
        best_category = CATEGORY_LABELS[best_idx]
        confidences = {c: float(ensemble_probs[i]) for i, c in enumerate(CATEGORY_LABELS)}
        return best_category, confidences

    def get_sentiment_score(self, text):
        scores = self.vader.polarity_scores(text)
        return scores["compound"]

    def predict_priority(self, text, category, sentiment_score):
        cat_encoded = self.le_cat.transform([category])[0]
        text_len = len(text)
        word_count = len(text.split())
        abs_sentiment = abs(sentiment_score)

        X = np.array(
            [[sentiment_score, abs_sentiment, cat_encoded, text_len, word_count]]
        )
        pred = self.priority_model.predict(X)[0]
        return self.le_pri.inverse_transform([pred])[0]

    def process(self, complaint_id, text):
        category, cat_probs = self.predict_category(text)
        sentiment_score = self.get_sentiment_score(text)
        priority = self.predict_priority(text, category, sentiment_score)

        return {
            "complaint_id": complaint_id,
            "text": text,
            "Category": category,
            "Sentiment Score": round(sentiment_score, 4),
            "Priority": priority,
        }

    def process_dataframe(self, input_df):
        results = []
        for _, row in input_df.iterrows():
            result = self.process(row["complaint_id"], row["text"])
            results.append(result)
        return pd.DataFrame(results)

    def process_csv(self, input_csv, output_csv=None):
        input_df = pd.read_csv(input_csv)
        results_df = self.process_dataframe(input_df)
        if output_csv:
            results_df.to_csv(output_csv, index=False)
            print(f"Results saved to {output_csv}")
        return results_df


if __name__ == "__main__":
    classifier = ComplaintClassifier()

    test_cases = [
        (1, "Need bulk order details"),
        (2, "Box was broken"),
        (3, "Product stopped working"),
        (4, "Poor packaging quality"),
        (5, "Inquiry about pricing"),
        (6, "Damaged packaging"),
        (7, "Trade-related query"),
        (8, "Product malfunctioning"),
        (9, "Defective item received"),
    ]

    print(f"{'ID':<5} {'Text':<30} {'Category':<12} {'Sentiment':<12} {'Priority':<10}")
    print("-" * 72)
    for cid, text in test_cases:
        result = classifier.process(cid, text)
        print(
            f"{result['complaint_id']:<5} "
            f"{result['text']:<30} "
            f"{result['Category']:<12} "
            f"{result['Sentiment Score']:<12} "
            f"{result['Priority']:<10}"
        )