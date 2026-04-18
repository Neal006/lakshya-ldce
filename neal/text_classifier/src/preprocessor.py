"""
Text Preprocessor for the Text Classification Pipeline.

Handles all text cleaning, normalization, lemmatization, stopword removal,
and label encoding in a consistent, reproducible pipeline.
"""

import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from util.config import (
    TEXT_COL, TARGET_COL, MODELS_DIR, RANDOM_STATE,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_pickle, load_pickle

logger = get_logger("preprocessor")


class TextPreprocessor:
    """
    Production-grade text preprocessing pipeline.
    """

    def __init__(self) -> None:
        self.nlp = None
        self.label_encoder = LabelEncoder()
        self.encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")
        self._load_spacy()

    def _load_spacy(self) -> None:
        """Load spaCy model, auto-install if missing."""
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            except OSError:
                logger.warning("spaCy model 'en_core_web_sm' not found. Installing...")
                subprocess.check_call(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"]
                )
                self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            logger.info("spaCy model loaded successfully.")
        except ImportError:
            logger.error("spaCy is not installed. Run: pip install spacy")
            raise

    def _clean_text(self, text: str) -> str:
        """Apply rule-based cleaning to a single text string."""
        text = text.lower()
        text = text.strip()
        text = re.sub(r"[^a-zA-Z\s]", "", text)
        # Remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _spell_correct(self, text: str) -> str:
        """Apply spell correction for short texts (< 30 chars)."""
        if len(text) < 30:
            try:
                from textblob import TextBlob
                corrected = str(TextBlob(text).correct())
                return corrected
            except Exception as e:
                logger.debug(f"Spell correction failed for '{text}': {e}")
                return text
        return text

    def _lemmatize_and_remove_stopwords(self, text: str) -> str:
        """Lemmatize text and remove stopwords using spaCy."""
        doc = self.nlp(text)
        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_space and len(token.text) > 1
        ]
        return " ".join(tokens)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Full preprocessing pipeline for training data.
        """
        logger.info(f"Preprocessing started. Shape before: {df.shape}")
        df = df.copy()

        null_count = df[TEXT_COL].isnull().sum()
        if null_count > 0:
            logger.warning(f"Found {null_count} null values in '{TEXT_COL}'. Filling with 'unknown'.")
            df[TEXT_COL] = df[TEXT_COL].fillna("unknown")

        df["text_original"] = df[TEXT_COL].copy()

        logger.info("Applying text cleaning (lowercase, strip, remove special chars)...")
        df[TEXT_COL] = df[TEXT_COL].astype(str).apply(self._clean_text)

        # Step 6: Spell correction (optimized: process unique texts only)
        logger.info("Applying spell correction (texts < 30 chars)...")
        unique_texts = df[TEXT_COL].unique()
        spell_cache = {t: self._spell_correct(t) for t in unique_texts}
        df[TEXT_COL] = df[TEXT_COL].map(spell_cache)
        logger.info(f"Spell-corrected {len(unique_texts)} unique texts")

        # Steps 7-8: Lemmatization + stopword removal (optimized: unique texts only)
        logger.info("Applying lemmatization and stopword removal...")
        unique_after_spell = df[TEXT_COL].unique()
        lemma_cache = {t: self._lemmatize_and_remove_stopwords(t) for t in unique_after_spell}
        df[TEXT_COL] = df[TEXT_COL].map(lemma_cache)
        logger.info(f"Lemmatized {len(unique_after_spell)} unique texts")

        logger.info("Encoding target labels...")
        ensure_dir(MODELS_DIR)
        df["label"] = self.label_encoder.fit_transform(df[TARGET_COL])
        save_pickle(self.label_encoder, self.encoder_path)
        logger.info(f"Label mapping: {dict(zip(self.label_encoder.classes_, self.label_encoder.transform(self.label_encoder.classes_)))}")

        null_after = df[TEXT_COL].isnull().sum()
        empty_after = (df[TEXT_COL].str.strip() == "").sum()
        logger.info(f"Preprocessing complete. Shape after: {df.shape}")
        logger.info(f"Nulls remaining: {null_after} | Empty strings: {empty_after}")

        return df

    def transform(self, texts: list) -> list:
        """
        Apply the same preprocessing pipeline to new unseen texts (no fitting).
        """
        processed = []
        for text in texts:
            if text is None or (isinstance(text, float) and np.isnan(text)):
                text = "unknown"
            text = str(text)
            text = self._clean_text(text)
            text = self._spell_correct(text)
            text = self._lemmatize_and_remove_stopwords(text)
            processed.append(text)
        return processed

    def get_label_encoder(self) -> LabelEncoder:
        """Return the fitted label encoder."""
        return self.label_encoder

    def load_label_encoder(self) -> LabelEncoder:
        """Load the saved label encoder from disk."""
        self.label_encoder = load_pickle(self.encoder_path)
        return self.label_encoder


if __name__ == "__main__":
    from util.config import DATA_PATH

    df = pd.read_csv(DATA_PATH)
    preprocessor = TextPreprocessor()
    df_clean = preprocessor.fit_transform(df)
    print(f"\nPreprocessed sample:\n{df_clean[[TEXT_COL, TARGET_COL, 'label']].head(10)}")
    print(f"\nUnique processed texts: {df_clean[TEXT_COL].nunique()}")
