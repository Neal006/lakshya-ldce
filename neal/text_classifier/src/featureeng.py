"""
Feature Engineer — Builds the ML feature matrix from preprocessed text.

Feature Blocks:
    Block 1: TF-IDF (learned from data — no static mapping)
    Block 2: Statistical text features (class-agnostic)
    Block 3: NLP linguistic features (class-agnostic — NO static keyword mapping)
    Block 4: Metadata (sentiment only)

IMPORTANT: No block uses hand-coded class-specific keywords.
All features are class-agnostic — the MODEL must learn the patterns.
"""

import os

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from util.config import (
    TEXT_COL, SENTIMENT_COL,
    MODELS_DIR,
    TFIDF_MAX_FEATURES, TFIDF_NGRAM_RANGE, TFIDF_MIN_DF,
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
        """
        Block 1 — TF-IDF features (learned from training data).
        The vectorizer learns which words are important from the data itself.
        No static keyword lists are used.
        """
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
        """Block 2 — Statistical text features (class-agnostic)."""
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

    def _build_linguistic_features(self, df: pd.DataFrame) -> tuple:
        """
        Block 3 — NLP linguistic features (class-agnostic).

        These features capture textual properties WITHOUT using any
        hand-coded class-specific keyword lists.
        The model must learn which patterns correlate with which class.
        """
        texts = df[TEXT_COL].astype(str)

        # POS tag distribution (noun/verb/adj ratios) — requires spaCy
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

            # Process unique texts only for efficiency
            unique_texts = texts.unique().tolist()
            pos_cache = {}
            for text in unique_texts:
                doc = nlp(text)
                total = max(len(doc), 1)
                noun_count = sum(1 for t in doc if t.pos_ in ("NOUN", "PROPN"))
                verb_count = sum(1 for t in doc if t.pos_ == "VERB")
                adj_count = sum(1 for t in doc if t.pos_ == "ADJ")
                adv_count = sum(1 for t in doc if t.pos_ == "ADV")
                pos_cache[text] = {
                    "noun_ratio": noun_count / total,
                    "verb_ratio": verb_count / total,
                    "adj_ratio": adj_count / total,
                    "adv_ratio": adv_count / total,
                    "noun_count": noun_count,
                    "verb_count": verb_count,
                }

            noun_ratio = texts.map(lambda t: pos_cache[t]["noun_ratio"]).values.reshape(-1, 1)
            verb_ratio = texts.map(lambda t: pos_cache[t]["verb_ratio"]).values.reshape(-1, 1)
            adj_ratio = texts.map(lambda t: pos_cache[t]["adj_ratio"]).values.reshape(-1, 1)
            adv_ratio = texts.map(lambda t: pos_cache[t]["adv_ratio"]).values.reshape(-1, 1)
            noun_count = texts.map(lambda t: pos_cache[t]["noun_count"]).values.reshape(-1, 1)
            verb_count = texts.map(lambda t: pos_cache[t]["verb_count"]).values.reshape(-1, 1)

            pos_features = np.hstack([
                noun_ratio, verb_ratio, adj_ratio, adv_ratio, noun_count, verb_count
            ])
            pos_names = [
                "noun_ratio", "verb_ratio", "adj_ratio", "adv_ratio",
                "noun_count", "verb_count"
            ]
        except Exception as e:
            logger.warning(f"POS tagging failed, using zeros: {e}")
            pos_features = np.zeros((len(df), 6))
            pos_names = [
                "noun_ratio", "verb_ratio", "adj_ratio", "adv_ratio",
                "noun_count", "verb_count"
            ]

        # Character-level features (class-agnostic)
        vowel_ratio = np.array([
            sum(1 for c in text.lower() if c in "aeiou") / max(len(text), 1)
            for text in texts
        ]).reshape(-1, 1)

        consonant_ratio = np.array([
            sum(1 for c in text.lower() if c.isalpha() and c not in "aeiou") / max(len(text), 1)
            for text in texts
        ]).reshape(-1, 1)

        space_ratio = np.array([
            text.count(" ") / max(len(text), 1)
            for text in texts
        ]).reshape(-1, 1)

        # Lexical diversity
        char_diversity = np.array([
            len(set(text.lower())) / max(len(text), 1)
            for text in texts
        ]).reshape(-1, 1)

        # Sentiment via TextBlob (class-agnostic — computed from text itself)
        try:
            from textblob import TextBlob
            unique_texts = texts.unique().tolist()
            tb_cache = {}
            for text in unique_texts:
                blob = TextBlob(text)
                tb_cache[text] = {
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity,
                }

            polarity = texts.map(lambda t: tb_cache[t]["polarity"]).values.reshape(-1, 1)
            subjectivity = texts.map(lambda t: tb_cache[t]["subjectivity"]).values.reshape(-1, 1)
        except Exception:
            polarity = np.zeros((len(df), 1))
            subjectivity = np.zeros((len(df), 1))

        char_features = np.hstack([
            vowel_ratio, consonant_ratio, space_ratio,
            char_diversity, polarity, subjectivity
        ])
        char_names = [
            "vowel_ratio", "consonant_ratio", "space_ratio",
            "char_diversity", "textblob_polarity", "textblob_subjectivity"
        ]

        all_features = np.hstack([pos_features, char_features])
        all_names = pos_names + char_names

        return all_features, all_names

    def _build_metadata_features(self, df: pd.DataFrame, fit: bool = True) -> tuple:
        """Block 4 — Metadata features (sentiment only; priority/resolution_time excluded)."""
        # Sentiment (already numeric, derived from text content)
        sentiment = df[SENTIMENT_COL].values.reshape(-1, 1)

        # Normalize
        if fit:
            meta_scaled = self.scaler.fit_transform(sentiment)
            save_pickle(self.scaler, self.scaler_path)
        else:
            meta_scaled = self.scaler.transform(sentiment)

        meta_names = ["sentiment_scaled"]
        return meta_scaled, meta_names

    def fit_transform(self, df: pd.DataFrame) -> tuple:
        """
        Build the complete feature matrix from training data.
        All features are class-agnostic — no static keyword mapping.
        """
        ensure_dir(MODELS_DIR)
        logger.info("Building feature matrix (fit_transform)...")

        tfidf_feat, tfidf_names = self._build_tfidf_features(df[TEXT_COL], fit=True)
        stat_feat, stat_names = self._build_statistical_features(df)
        ling_feat, ling_names = self._build_linguistic_features(df)
        meta_feat, meta_names = self._build_metadata_features(df, fit=True)
        X = np.hstack([tfidf_feat, stat_feat, ling_feat, meta_feat])
        self.feature_names = tfidf_names + stat_names + ling_names + meta_names

        logger.info(f"Feature matrix shape: ({X.shape[0]}, {X.shape[1]})")
        logger.info(
            f"TFIDF: {len(tfidf_names)} cols | "
            f"Statistical: {len(stat_names)} | "
            f"Linguistic: {len(ling_names)} | "
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
        ling_feat, _ = self._build_linguistic_features(df)
        meta_feat, _ = self._build_metadata_features(df, fit=False)
        X = np.hstack([tfidf_feat, stat_feat, ling_feat, meta_feat])
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
