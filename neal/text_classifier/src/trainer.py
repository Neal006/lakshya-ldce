import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, f1_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from util.config import MODELS_DIR, RANDOM_STATE
from util.logger import get_logger
from util.file_utils import ensure_dir, save_pickle

logger = get_logger("trainer")


class ModelTrainer:

    def __init__(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> None:
        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
        self.model_registry = self.get_model_registry()
        self.results: dict = {}
        self.trained_models: dict = {}

    def get_model_registry(self) -> dict:
        """Return a dictionary of model name → unfitted model instance."""
        return {
            "LogisticRegression": LogisticRegression(
                max_iter=1000,
                random_state=RANDOM_STATE,
                multi_class="multinomial",
                n_jobs=-1,
            ),
            "RandomForest": RandomForestClassifier(
                n_estimators=200,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
            "XGBoost": XGBClassifier(
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=RANDOM_STATE,
                n_jobs=-1,
                verbosity=0,
            ),
            "LightGBM": LGBMClassifier(
                random_state=RANDOM_STATE,
                n_jobs=-1,
                verbose=-1,
            ),
            "SVM": SVC(
                kernel="rbf",
                probability=True,
                random_state=RANDOM_STATE,
            ),
        }

    def train_all(self) -> dict:
        """
        Train all models and evaluate on the validation set.
        """
        logger.info("BASELINE MODEL TRAINING")

        for name, model in self.model_registry.items():
            logger.info(f"\nTraining {name}...")
            start = time.perf_counter()

            try:
                model.fit(self.X_train, self.y_train)
                elapsed = time.perf_counter() - start

                y_pred = model.predict(self.X_val)
                val_acc = accuracy_score(self.y_val, y_pred)
                val_f1 = f1_score(self.y_val, y_pred, average="macro")

                self.results[name] = {
                    "val_accuracy": round(val_acc, 4),
                    "val_f1_macro": round(val_f1, 4),
                    "training_time": round(elapsed, 2),
                }
                self.trained_models[name] = model

                logger.info(
                    f"  {name}: Acc={val_acc:.4f} | F1={val_f1:.4f} | Time={elapsed:.2f}s"
                )
            except Exception as e:
                logger.error(f"  {name} FAILED: {e}")
                self.results[name] = {
                    "val_accuracy": 0.0,
                    "val_f1_macro": 0.0,
                    "training_time": 0.0,
                    "error": str(e),
                }

        self.results = dict(
            sorted(self.results.items(), key=lambda x: x[1]["val_f1_macro"], reverse=True)
        )

        self._print_leaderboard()

        return self.results

    def _print_leaderboard(self) -> None:
        header = (
            "│ Model              │ Val Acc  │ F1 Macro │ Time (s) │\n"
            )
        print(header)
        logger.info(header)

        for name, res in self.results.items():
            row = (
                f"│ {name:<18} │ {res['val_accuracy']:.4f}   │ {res['val_f1_macro']:.4f}   │ "
                f"{res['training_time']:>6.1f}s  │"
            )
            print(row)
            logger.info(row)

    def get_best_model(self) -> tuple:
        """
        Return the best model by validation F1 macro score.
        """
        if not self.results:
            raise RuntimeError("No models trained yet. Call train_all() first.")

        best_name = list(self.results.keys())[0]  # Already sorted
        best_model = self.trained_models[best_name]
        logger.info(
            f"Best model: {best_name} "
            f"(F1={self.results[best_name]['val_f1_macro']:.4f})"
        )
        return best_name, best_model

    def save_model(self, model: object, name: str) -> None:
        """Save a trained model to the models/ directory."""
        ensure_dir(MODELS_DIR)
        path = f"{MODELS_DIR}/{name}_base.pkl"
        save_pickle(model, path)
        logger.info(f"Model saved → {path}")


if __name__ == "__main__":
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    X, y = make_classification(n_samples=1000, n_features=20, n_classes=3,
                                n_informative=15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    trainer = ModelTrainer(X_train, y_train, X_val, y_val)
    results = trainer.train_all()
    best_name, best_model = trainer.get_best_model()
    print(f"\nBest: {best_name}")
