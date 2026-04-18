import os

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from util.config import (
    TEXT_COL, SENTIMENT_COL, PRIORITY_COL, RESOLUTION_TIME_COL,
    MODELS_DIR,
    TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE, TFIDF_MIN_DF,
    TRADE_KEYWORDS, PACKAGING_KEYWORDS, PRODUCT_KEYWORDS,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_pickle, load_pickle

logger = get_logger("featureeng")


class FeatureEngineer:
    def __init__(self) -> None:
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=TFIDF_NGRAM_RANGE,
            max_features=TFIDF_MAX_FEATURES,
            sublinear_tf=True,
            min_df=TFIDF_MIN_DF,
        )
        self.scaler = StandardScaler()
        self.tfidf_path = os.path.join(MODELS_DIR, "tfidf.pkl")
        self.scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
        self.feature_names: list = []

    def _build_tfidf_features(self, texts: pd.Series, fit: bool = True) -> np.ndarray:
        """Block 1 — TF-IDF features (sparse → dense)."""
        if fit:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            save_pickle(self.tfidf_vectorizer, self.tfidf_path)
            logger.info(f"TF-IDF fitted. Vocabulary size: {len(self.tfidf_vectorizer.vocabulary_)}")
        else:
            tfidf_matrix = self.tfidf_vectorizer.transform(texts)

        tfidf_dense = tfidf_matrix.toarray()
        tfidf_names = [f"tfidf_{name}" for name in self.tfidf_vectorizer.get_feature_names_out()]
        return tfidf_dense, tfidf_names

    def _build_statistical_features(self, df: pd.DataFrame) -> tuple:
        """Block 2 — Statistical text features."""
        texts = df[TEXT_COL].astype(str)

        text_length = texts.str.len().values.reshape(-1, 1)
        word_count = texts.str.split().str.len().values.reshape(-1, 1)

        avg_word_length = np.array([
            np.mean([len(w) for w in text.split()]) if len(text.split()) > 0 else 0
            for text in texts
        ]).reshape(-1, 1)

        unique_word_ratio = np.array([
            len(set(text.split())) / max(len(text.split()), 1)
            for text in texts
        ]).reshape(-1, 1)

        has_digit = texts.str.contains(r"\d", regex=True).astype(int).values.reshape(-1, 1)

        # Capital ratio needs original text (pre-lowercase)
        if "text_original" in df.columns:
            orig_texts = df["text_original"].astype(str)
        else:
            orig_texts = texts
        capital_ratio = np.array([
            sum(1 for c in text if c.isupper()) / max(len(text), 1)
            for text in orig_texts
        ]).reshape(-1, 1)

        stat_features = np.hstack([
            text_length, word_count, avg_word_length,
            unique_word_ratio, has_digit, capital_ratio
        ])
        stat_names = [
            "text_length", "word_count", "avg_word_length",
            "unique_word_ratio", "has_digit", "capital_ratio"
        ]
        return stat_features, stat_names

    def _build_domain_features(self, df: pd.DataFrame) -> tuple:
        """Block 3 — Keyword/rule-based domain features."""
        texts_lower = df[TEXT_COL].astype(str).str.lower()

        def keyword_features(texts: pd.Series, keywords: list, prefix: str) -> tuple:
            is_match = texts.apply(lambda t: int(any(kw in t for kw in keywords))).values.reshape(-1, 1)
            kw_count = texts.apply(lambda t: sum(1 for kw in keywords if kw in t)).values.reshape(-1, 1)
            return np.hstack([is_match, kw_count]), [f"is_{prefix}_text", f"{prefix}_keyword_count"]

        trade_feat, trade_names = keyword_features(texts_lower, TRADE_KEYWORDS, "trade")
        pack_feat, pack_names = keyword_features(texts_lower, PACKAGING_KEYWORDS, "packaging")
        prod_feat, prod_names = keyword_features(texts_lower, PRODUCT_KEYWORDS, "product")

        domain_features = np.hstack([trade_feat, pack_feat, prod_feat])
        domain_names = trade_names + pack_names + prod_names
        return domain_features, domain_names

    def _build_metadata_features(self, df: pd.DataFrame, fit: bool = True) -> tuple:
        """Block 4 — Metadata features (sentiment, priority, resolution_time)."""
        # Sentiment (already numeric)
        sentiment = df[SENTIMENT_COL].values.reshape(-1, 1)

        # Priority encoding: Low=0, Medium=1, High=2
        priority_map = {"Low": 0, "Medium": 1, "High": 2}
        priority_encoded = df[PRIORITY_COL].map(priority_map).values.reshape(-1, 1)

        # Resolution time (already numeric)
        resolution_time = df[RESOLUTION_TIME_COL].values.reshape(-1, 1)

        meta_raw = np.hstack([sentiment, priority_encoded, resolution_time])

        # Normalize
        if fit:
            meta_scaled = self.scaler.fit_transform(meta_raw)
            save_pickle(self.scaler, self.scaler_path)
        else:
            meta_scaled = self.scaler.transform(meta_raw)

        meta_names = ["sentiment_scaled", "priority_encoded_scaled", "resolution_time_scaled"]
        return meta_scaled, meta_names

    def fit_transform(self, df: pd.DataFrame) -> tuple:
        """
        Build the complete feature matrix from training data.
        """
        ensure_dir(MODELS_DIR)
        logger.info("Building feature matrix (fit_transform)...")
        
        tfidf_feat, tfidf_names = self._build_tfidf_features(df[TEXT_COL], fit=True)
        stat_feat, stat_names = self._build_statistical_features(df)
        domain_feat, domain_names = self._build_domain_features(df)
        meta_feat, meta_names = self._build_metadata_features(df, fit=True)
        X = np.hstack([tfidf_feat, stat_feat, domain_feat, meta_feat])
        self.feature_names = tfidf_names + stat_names + domain_names + meta_names

        logger.info(f"Feature matrix shape: ({X.shape[0]}, {X.shape[1]})")
        logger.info(
            f"TFIDF: {len(tfidf_names)} cols | "
            f"Statistical: {len(stat_names)} | "
            f"Domain: {len(domain_names)} | "
            f"Metadata: {len(meta_names)}"
        )

        return X, self.feature_names

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform new data using fitted vectorizer and scaler (no refitting).
        """
        logger.info("Building feature matrix (transform)...")
        self.tfidf_vectorizer = load_pickle(self.tfidf_path)
        self.scaler = load_pickle(self.scaler_path)

        tfidf_feat, _ = self._build_tfidf_features(df[TEXT_COL], fit=False)
        stat_feat, _ = self._build_statistical_features(df)
        domain_feat, _ = self._build_domain_features(df)
        meta_feat, _ = self._build_metadata_features(df, fit=False)
        X = np.hstack([tfidf_feat, stat_feat, domain_feat, meta_feat])
        logger.info(f"Feature matrix shape: ({X.shape[0]}, {X.shape[1]})")

        return X

    def get_feature_names(self) -> list:
        return self.feature_names


if __name__ == "__main__":
    from util.config import DATA_PATH
    from src.preprocessor import TextPreprocessor

    df = pd.read_csv(DATA_PATH)
    preprocessor = TextPreprocessor()
    df_clean = preprocessor.fit_transform(df)

    fe = FeatureEngineer()
    X, names = fe.fit_transform(df_clean)
    print(f"\nFeature matrix: {X.shape}")
    print(f"Feature names ({len(names)}): {names[:10]}...")
