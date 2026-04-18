import os

import numpy as np
from sklearn.decomposition import PCA

from util.config import (
    MODELS_DIR, EMBEDDING_MODEL_NAME, EMBEDDING_DIM,
    PCA_COMPONENTS, EMBEDDING_BATCH_SIZE, RANDOM_STATE,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_pickle, load_pickle

logger = get_logger("nlp")


class NLPLayer:
    """
    Sentence embedding layer using sentence-transformers.
    Provides 384-dimensional embeddings from 'all-MiniLM-L6-v2',
    with optional PCA reduction to 50 dimensions for tree models.
    """

    def __init__(self) -> None:
        self.model = None
        self.pca = None
        self.cache_path = os.path.join(MODELS_DIR, "embeddings_cache.npy")
        self.pca_path = os.path.join(MODELS_DIR, "pca.pkl")
        self._load_model()

    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
            self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info(f"Embedding model loaded. Dim: {EMBEDDING_DIM}")
        except ImportError:
            logger.error(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )
            raise

    def get_embeddings(self, texts: list, use_cache: bool = True) -> np.ndarray:
        """
        Generate sentence embeddings for a list of texts.
        """
        ensure_dir(MODELS_DIR)

        # Check cache
        if use_cache and os.path.exists(self.cache_path):
            cached = np.load(self.cache_path)
            if cached.shape[0] == len(texts):
                logger.info(f"Loaded cached embeddings: {cached.shape}")
                return cached
            else:
                logger.info("Cache size mismatch, recomputing embeddings...")

        logger.info(f"Computing embeddings for {len(texts)} texts...")

        try:
            from tqdm import tqdm

            # Batch encoding for memory efficiency
            all_embeddings = []
            for i in tqdm(range(0, len(texts), EMBEDDING_BATCH_SIZE),
                          desc="Encoding", unit="batch"):
                batch = texts[i: i + EMBEDDING_BATCH_SIZE]
                batch_embeddings = self.model.encode(
                    batch, show_progress_bar=False, convert_to_numpy=True
                )
                all_embeddings.append(batch_embeddings)

            embeddings = np.vstack(all_embeddings)
        except ImportError:
            embeddings = self.model.encode(
                texts, show_progress_bar=True,
                batch_size=EMBEDDING_BATCH_SIZE,
                convert_to_numpy=True,
            )

        # Save cache
        np.save(self.cache_path, embeddings)
        logger.info(f"Embeddings shape: {embeddings.shape}")

        return embeddings

    def get_embedding_features(
        self, texts: list, fit: bool = True, use_cache: bool = True
    ) -> np.ndarray:
        """
        Get PCA-reduced embedding features (384 → 50 dims).
        """
        embeddings = self.get_embeddings(texts, use_cache=use_cache)

        if fit:
            logger.info(f"Fitting PCA: {EMBEDDING_DIM} → {PCA_COMPONENTS} dims...")
            self.pca = PCA(n_components=PCA_COMPONENTS, random_state=RANDOM_STATE)
            reduced = self.pca.fit_transform(embeddings)
            save_pickle(self.pca, self.pca_path)
            explained = sum(self.pca.explained_variance_ratio_) * 100
            logger.info(f"PCA variance explained: {explained:.1f}%")
        else:
            self.pca = load_pickle(self.pca_path)
            reduced = self.pca.transform(embeddings)

        logger.info(f"PCA-reduced embeddings shape: {reduced.shape}")
        return reduced


if __name__ == "__main__":
    from util.config import DATA_PATH, TEXT_COL
    import pandas as pd

    df = pd.read_csv(DATA_PATH)
    texts = df[TEXT_COL].astype(str).tolist()[:100]

    nlp_layer = NLPLayer()
    embeds = nlp_layer.get_embedding_features(texts, fit=True)
    print(f"\nEmbedding features shape: {embeds.shape}")
