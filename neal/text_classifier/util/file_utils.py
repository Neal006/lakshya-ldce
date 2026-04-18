import os
import json
import pickle
from typing import Any

import matplotlib.pyplot as plt

from util.config import GRAPH_OP_DIR
from util.logger import get_logger

logger = get_logger("file_utils")


def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Created directory: {path}")


def save_json(data: dict, path: str) -> None:
    """Save a dictionary as a pretty-printed JSON file."""
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved JSON → {path}")
    except Exception as e:
        logger.error(f"Failed to save JSON to {path}: {e}")
        raise


def load_json(path: str) -> dict:
    """Load a JSON file safely with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON ← {path}")
        return data
    except FileNotFoundError:
        logger.error(f"JSON file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise


def save_pickle(obj: Any, path: str) -> None:
    """Pickle dump an object to disk."""
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        logger.info(f"Saved pickle → {path}")
    except Exception as e:
        logger.error(f"Failed to save pickle to {path}: {e}")
        raise


def load_pickle(path: str) -> Any:
    """Load a pickled object with error handling."""
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        logger.debug(f"Loaded pickle ← {path}")
        return obj
    except FileNotFoundError:
        logger.error(f"Pickle file not found: {path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load pickle from {path}: {e}")
        raise


def save_figure(fig: plt.Figure, filename: str, dpi: int = 150) -> str:
    """
    Save a matplotlib figure to the graph_op/ directory.
    """
    try:
        ensure_dir(GRAPH_OP_DIR)
        filepath = os.path.join(GRAPH_OP_DIR, filename)
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info(f"Saved figure → {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save figure {filename}: {e}")
        raise
