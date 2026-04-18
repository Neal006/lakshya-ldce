import os

import numpy as np
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import matplotlib
matplotlib.use("Agg")

from util.config import (
    MODELS_DIR, RESULTS_DIR, GRAPH_OP_DIR,
    N_OPTUNA_TRIALS, RANDOM_STATE,
)
from util.logger import get_logger
from util.file_utils import ensure_dir, save_pickle, save_json, save_figure

logger = get_logger("optuna_tuner")

optuna.logging.set_verbosity(optuna.logging.WARNING)


class OptunaTuner:
    """
    Hyperparameter tuning using Optuna TPE sampler.
    Supports search spaces for: LogisticRegression, RandomForest,
    XGBoost, LightGBM, and SVM.
    """

    def __init__(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        model_name: str,
        n_trials: int = N_OPTUNA_TRIALS,
    ) -> None:
        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
        self.model_name = model_name
        self.n_trials = n_trials
        self.study = None
        self.best_model = None
        self.best_params = None

    def get_search_space(self, trial: optuna.Trial, model_name: str) -> dict:
        """Define the hyperparameter search space for a given model."""

        if model_name == "XGBoost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "gamma": trial.suggest_float("gamma", 0.0, 1.0),
            }

        elif model_name == "LightGBM":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "num_leaves": trial.suggest_int("num_leaves", 20, 150),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 50),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            }

        elif model_name == "RandomForest":
            max_depth_choice = trial.suggest_categorical("max_depth_type", ["int", "none"])
            max_depth = trial.suggest_int("max_depth", 5, 30) if max_depth_choice == "int" else None
            return {
                "n_estimators": trial.suggest_int("n_estimators", 100, 800),
                "max_depth": max_depth,
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2"]),
            }

        elif model_name == "LogisticRegression":
            return {
                "C": trial.suggest_float("C", 0.001, 100, log=True),
                "solver": trial.suggest_categorical("solver", ["lbfgs", "saga", "newton-cg"]),
                "max_iter": trial.suggest_int("max_iter", 500, 3000),
            }

        elif model_name == "SVM":
            return {
                "C": trial.suggest_float("C", 0.01, 100, log=True),
                "gamma": trial.suggest_categorical("gamma", ["scale", "auto"]),
                "kernel": trial.suggest_categorical("kernel", ["rbf", "linear", "poly"]),
            }

        else:
            raise ValueError(f"Unknown model: {model_name}")

    def _build_model(self, params: dict) -> object:
        """Instantiate a model with given parameters."""
        if self.model_name == "XGBoost":
            return XGBClassifier(
                **params, use_label_encoder=False,
                eval_metric="mlogloss", random_state=RANDOM_STATE,
                n_jobs=-1, verbosity=0,
            )
        elif self.model_name == "LightGBM":
            return LGBMClassifier(
                **params, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1,
            )
        elif self.model_name == "RandomForest":
            return RandomForestClassifier(
                **params, random_state=RANDOM_STATE, n_jobs=-1,
            )
        elif self.model_name == "LogisticRegression":
            return LogisticRegression(
                **params, random_state=RANDOM_STATE, multi_class="multinomial", n_jobs=-1,
            )
        elif self.model_name == "SVM":
            return SVC(
                **params, probability=True, random_state=RANDOM_STATE,
            )
        else:
            raise ValueError(f"Unknown model: {self.model_name}")

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna objective function — returns val F1 macro score."""
        params = self.get_search_space(trial, self.model_name)
        model = self._build_model(params)

        try:
            model.fit(self.X_train, self.y_train)
            y_pred = model.predict(self.X_val)
            score = f1_score(self.y_val, y_pred, average="macro")
            return score
        except Exception as e:
            logger.warning(f"Trial {trial.number} failed: {e}")
            return 0.0

    def tune(self) -> tuple:
        """
        Run Optuna hyperparameter tuning.
        """
        logger.info("=" * 60)
        logger.info(f"OPTUNA TUNING — {self.model_name} ({self.n_trials} trials)")
        logger.info("=" * 60)

        ensure_dir(RESULTS_DIR)
        ensure_dir(GRAPH_OP_DIR)
        ensure_dir(MODELS_DIR)

        self.study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=RANDOM_STATE),
            pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5),
        )

        self.study.optimize(
            self.objective,
            n_trials=self.n_trials,
            show_progress_bar=True,
        )

        self.best_params = self.study.best_params
        best_score = self.study.best_value

        if self.model_name == "RandomForest" and "max_depth_type" in self.best_params:
            if self.best_params["max_depth_type"] == "none":
                self.best_params["max_depth"] = None
            del self.best_params["max_depth_type"]

        logger.info(f"Best score: {best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")

        save_json(
            {"model": self.model_name, "best_score": best_score, "best_params": self.best_params},
            os.path.join(RESULTS_DIR, "best_params.json"),
        )

        logger.info("Refitting best model on train+val combined data...")
        X_combined = np.vstack([self.X_train, self.X_val])
        y_combined = np.concatenate([self.y_train, self.y_val])

        self.best_model = self._build_model(self.best_params)
        self.best_model.fit(X_combined, y_combined)

        model_path = os.path.join(MODELS_DIR, f"{self.model_name}_tuned.pkl")
        save_pickle(self.best_model, model_path)

        self._save_optuna_plots()

        return self.best_model, self.best_params, best_score

    def _save_optuna_plots(self) -> None:
        """Save Optuna visualization plots."""
        import matplotlib.pyplot as plt

        try:
            fig = optuna.visualization.matplotlib.plot_param_importances(self.study)
            fig_obj = plt.gcf()
            fig_obj.set_size_inches(10, 6)
            fig_obj.suptitle(f"Parameter Importance — {self.model_name}", fontsize=14, fontweight="bold")
            save_figure(fig_obj, "optuna_param_importance.png")
        except Exception as e:
            logger.warning(f"Could not generate param importance plot: {e}")

        try:
            fig = optuna.visualization.matplotlib.plot_optimization_history(self.study)
            fig_obj = plt.gcf()
            fig_obj.set_size_inches(10, 6)
            fig_obj.suptitle(f"Optimization History — {self.model_name}", fontsize=14, fontweight="bold")
            save_figure(fig_obj, "optuna_optimization_history.png")
        except Exception as e:
            logger.warning(f"Could not generate optimization history plot: {e}")


if __name__ == "__main__":
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split

    X, y = make_classification(n_samples=500, n_features=20, n_classes=3,
                                n_informative=15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    tuner = OptunaTuner(X_train, y_train, X_val, y_val, "XGBoost", n_trials=10)
    best_model, best_params, best_score = tuner.tune()
    print(f"\nBest score: {best_score:.4f}")
    print(f"Best params: {best_params}")
