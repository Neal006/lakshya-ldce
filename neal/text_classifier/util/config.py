import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "data.csv")
TARGET_COL = "category"
TEXT_COL = "text"
SENTIMENT_COL = "sentiment"
PRIORITY_COL = "priority"
RESOLUTION_TIME_COL = "resolution_time"

GRAPH_OP_DIR = os.path.join(PROJECT_ROOT, "graph_op")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

RANDOM_STATE = 42
TEST_SIZE = 0.2       # 20% held out for final evaluation
VAL_SIZE = 0.1        # 10% of train+val used for validation
N_OPTUNA_TRIALS = 50

LABEL_CLASSES = ["Trade", "Packaging", "Product"]

LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(RESULTS_DIR, "run.log")
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 3

TFIDF_MAX_FEATURES = 500
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
PCA_COMPONENTS = 50
EMBEDDING_BATCH_SIZE = 64

# NOTE: Static keyword lists (TRADE_KEYWORDS, etc.) intentionally removed.
# The old approach was static rule-based mapping, which violates competition rules.
# All classification is now done via ML-learned TF-IDF + embedding features.

KFOLD_SPLITS = 5
