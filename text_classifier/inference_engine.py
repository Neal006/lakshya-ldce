"""
inference_engine.py — High-performance ONNX+CUDA inference engine.

Replaces the vanilla PyTorch pipeline from nlp.py with ONNX Runtime
GPU-accelerated inference for maximum speed.

Usage:
    engine = InferenceEngine()
    result = engine.predict(complaint_id=1, text="Box was broken")
"""

import os
import time
import logging
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "data.csv"
MODELS_DIR = BASE_DIR / "models"
CATEGORY_LABELS = ["Trade", "Product", "Packaging"]

# NLI label mapping for zero-shot classification
# DistilBERT-MNLI outputs: [contradiction, entailment, neutral]
_NLI_ENTAILMENT_IDX = 1  # entailment position in output logits


def _softmax(x: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def _create_ort_session(onnx_path: str) -> ort.InferenceSession:
    """Create an ONNX Runtime session with optimal provider selection."""
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.intra_op_num_threads = 4
    sess_options.inter_op_num_threads = 2

    # Try GPU providers first, fall back to CPU
    available = ort.get_available_providers()
    providers = []
    if "CUDAExecutionProvider" in available:
        providers.append(("CUDAExecutionProvider", {
            "device_id": 0,
            "arena_extend_strategy": "kSameAsRequested",
            "cudnn_conv_algo_search": "EXHAUSTIVE",
        }))
    providers.append("CPUExecutionProvider")

    session = ort.InferenceSession(
        onnx_path,
        sess_options=sess_options,
        providers=providers,
    )

    active = session.get_providers()
    logger.info(f"ONNX session created for {Path(onnx_path).name} — Providers: {active}")
    return session


class InferenceEngine:
    """
    High-performance complaint classifier using ONNX Runtime.

    Pipeline:
        text → [DistilBERT-MNLI (zero-shot)] + [MiniLM-L6 (similarity)]
             → ensemble → category
        text → [VADER] → sentiment score
        features → [DecisionTree] → priority
    """

    def __init__(self):
        start = time.time()
        logger.info("Initializing InferenceEngine...")

        # ─── Load ONNX sessions ─────────────────────────────────
        self._load_zeroshot_model()
        self._load_embedding_model()

        # ─── VADER (lightweight, CPU-only) ──────────────────────
        self.vader = SentimentIntensityAnalyzer()

        # ─── Priority model (trained from data) ────────────────
        self._train_priority_model()

        # ─── Pre-compute reference embeddings ──────────────────
        self._build_reference_embeddings()

        elapsed = time.time() - start
        logger.info(f"InferenceEngine ready in {elapsed:.1f}s")

    # ─── Model Loading ──────────────────────────────────────────

    def _load_zeroshot_model(self):
        """Load DistilBERT-MNLI ONNX model for zero-shot classification."""
        model_dir = MODELS_DIR / "distilbert_mnli"

        # Find the best ONNX file
        optimized = model_dir / "model_optimized.onnx"
        base = model_dir / "model.onnx"
        onnx_path = str(optimized if optimized.exists() else base)

        logger.info(f"Loading zero-shot model: {onnx_path}")
        self.zs_tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.zs_session = _create_ort_session(onnx_path)

        # Get the model's label mapping
        # DistilBERT-MNLI: 0=contradiction, 1=entailment, 2=neutral
        self._nli_labels = ["contradiction", "entailment", "neutral"]

    def _load_embedding_model(self):
        """Load MiniLM-L6-v2 ONNX model for semantic similarity."""
        model_dir = MODELS_DIR / "minilm_l6"

        optimized = model_dir / "model_optimized.onnx"
        base = model_dir / "model.onnx"
        onnx_path = str(optimized if optimized.exists() else base)

        logger.info(f"Loading embedding model: {onnx_path}")
        self.emb_tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.emb_session = _create_ort_session(onnx_path)

    # ─── Priority Model ─────────────────────────────────────────

    def _train_priority_model(self):
        """Train the DecisionTree priority model from data (same as nlp.py)."""
        logger.info("Training priority model from data...")
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].str.strip()

        self.le_cat = LabelEncoder()
        self.le_pri = LabelEncoder()

        vader_scores = df["text"].apply(
            lambda x: self.vader.polarity_scores(x)["compound"]
        )

        df["_vader"] = vader_scores
        df["_cat_enc"] = self.le_cat.fit_transform(df["category"])
        df["_pri_enc"] = self.le_pri.fit_transform(df["priority"])
        df["_text_len"] = df["text"].str.len()
        df["_word_count"] = df["text"].str.split().str.len()
        df["_abs_sentiment"] = df["_vader"].abs()

        X = df[["_vader", "_abs_sentiment", "_cat_enc", "_text_len", "_word_count"]].values
        y = df["_pri_enc"].values

        self.priority_model = DecisionTreeClassifier(max_depth=6, random_state=42)
        self.priority_model.fit(X, y)

    # ─── Reference Embeddings ────────────────────────────────────

    def _build_reference_embeddings(self):
        """Pre-compute and cache reference embeddings for each category."""
        logger.info("Building reference embeddings...")
        df = pd.read_csv(DATA_PATH)
        df.columns = df.columns.str.strip()
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].str.strip()

        self.ref_map = {}
        self.ref_embeddings = {}

        for cat in CATEGORY_LABELS:
            texts = df[df["category"] == cat]["text"].unique().tolist()
            self.ref_map[cat] = texts
            # Encode all reference texts for this category
            embeddings = np.array([self._encode_text(t) for t in texts])
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-9)
            self.ref_embeddings[cat] = embeddings

    # ─── Core Inference Methods ──────────────────────────────────

    def _encode_text(self, text: str) -> np.ndarray:
        """Encode text to a 384-dim embedding using MiniLM-L6 ONNX."""
        inputs = self.emb_tokenizer(
            text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=128,
        )

        outputs = self.emb_session.run(
            None,
            {
                "input_ids": inputs["input_ids"].astype(np.int64),
                "attention_mask": inputs["attention_mask"].astype(np.int64),
            },
        )

        # Mean pooling over token embeddings (masked)
        hidden_state = outputs[0]  # (1, seq_len, 384)
        mask = inputs["attention_mask"].astype(np.float32)
        mask_expanded = np.expand_dims(mask, -1)  # (1, seq_len, 1)
        sum_embeddings = np.sum(hidden_state * mask_expanded, axis=1)
        sum_mask = np.sum(mask_expanded, axis=1).clip(min=1e-9)
        embedding = (sum_embeddings / sum_mask)[0]  # (384,)

        return embedding

    def _zeroshot_classify(self, text: str) -> dict[str, float]:
        """
        Zero-shot classification via NLI.

        For each candidate label, construct a premise-hypothesis pair
        and get the entailment score. This is the same logic as HuggingFace's
        zero-shot-classification pipeline but without the Python overhead.
        """
        scores = {}

        for label in CATEGORY_LABELS:
            hypothesis = f"This text is about {label}."

            inputs = self.zs_tokenizer(
                text,
                hypothesis,
                return_tensors="np",
                truncation=True,
                max_length=256,
            )

            outputs = self.zs_session.run(
                None,
                {
                    "input_ids": inputs["input_ids"].astype(np.int64),
                    "attention_mask": inputs["attention_mask"].astype(np.int64),
                },
            )

            logits = outputs[0][0]  # (3,) — [contradiction, entailment, neutral]
            # We want the entailment score for each label
            scores[label] = float(logits[_NLI_ENTAILMENT_IDX])

        # Softmax across all labels' entailment scores
        score_array = np.array([scores[c] for c in CATEGORY_LABELS])
        probs = _softmax(score_array)

        return {c: float(probs[i]) for i, c in enumerate(CATEGORY_LABELS)}

    def _similarity_classify(self, text: str) -> dict[str, float]:
        """Classify via cosine similarity to reference embeddings."""
        query_emb = self._encode_text(text)
        query_emb = query_emb / (np.linalg.norm(query_emb) + 1e-9)

        sim_scores = {}
        for cat in CATEGORY_LABELS:
            # Cosine similarity = dot product (both are L2-normalized)
            sims = self.ref_embeddings[cat] @ query_emb
            sim_scores[cat] = float(np.max(sims))

        # Normalize to probability distribution
        vals = np.array([sim_scores[c] for c in CATEGORY_LABELS])
        shifted = vals - vals.min() + 1e-9
        probs = shifted / shifted.sum()

        return {c: float(probs[i]) for i, c in enumerate(CATEGORY_LABELS)}

    # ─── Public Prediction API ───────────────────────────────────

    def predict(self, complaint_id: int | str, text: str) -> dict:
        """
        Full prediction pipeline for a single complaint.

        Returns:
            {
                "complaint_id": ...,
                "text": ...,
                "category": "Trade" | "Product" | "Packaging",
                "sentiment_score": float,
                "priority": "High" | "Medium" | "Low",
                "latency_ms": float
            }
        """
        start = time.perf_counter()

        # Step 1: Category — Ensemble of zero-shot + similarity
        zs_scores = self._zeroshot_classify(text)
        sim_scores = self._similarity_classify(text)

        ensemble_probs = {}
        for cat in CATEGORY_LABELS:
            ensemble_probs[cat] = 0.5 * zs_scores[cat] + 0.5 * sim_scores[cat]

        # Renormalize
        total = sum(ensemble_probs.values())
        for cat in CATEGORY_LABELS:
            ensemble_probs[cat] /= total

        category = max(ensemble_probs, key=ensemble_probs.get)

        # Step 2: Sentiment
        sentiment_score = self.vader.polarity_scores(text)["compound"]

        # Step 3: Priority
        cat_encoded = self.le_cat.transform([category])[0]
        text_len = len(text)
        word_count = len(text.split())
        abs_sentiment = abs(sentiment_score)

        X = np.array([[sentiment_score, abs_sentiment, cat_encoded, text_len, word_count]])
        pred = self.priority_model.predict(X)[0]
        priority = self.le_pri.inverse_transform([pred])[0]

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "complaint_id": complaint_id,
            "text": text,
            "category": category,
            "sentiment_score": round(float(sentiment_score), 4),
            "priority": priority,
            "latency_ms": round(latency_ms, 2),
        }


# ─── Quick self-test ─────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    engine = InferenceEngine()

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

    print(f"\n{'ID':<5} {'Text':<30} {'Category':<12} {'Sentiment':<12} {'Priority':<10} {'Latency':<10}")
    print("-" * 82)

    latencies = []
    for cid, text in test_cases:
        result = engine.predict(cid, text)
        latencies.append(result["latency_ms"])
        print(
            f"{result['complaint_id']:<5} "
            f"{result['text']:<30} "
            f"{result['category']:<12} "
            f"{result['sentiment_score']:<12} "
            f"{result['priority']:<10} "
            f"{result['latency_ms']:<10.2f}ms"
        )

    print(f"\nAverage latency: {np.mean(latencies):.2f}ms")
    print(f"P50 latency:     {np.percentile(latencies, 50):.2f}ms")
    print(f"P95 latency:     {np.percentile(latencies, 95):.2f}ms")
