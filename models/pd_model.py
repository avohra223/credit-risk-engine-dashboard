"""
Probability of Default (PD) Model — Logistic Regression.

Predicts 1-year probability of default using obligor financial ratios
and rating information. Outputs PD scores, model coefficients, and
a scorecard mapping PD bands to internal rating grades.
"""
import logging
import pickle
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

FEATURES = [
    "leverage_ratio",
    "interest_coverage",
    "current_ratio",
    "debt_to_ebitda",
    "sector_risk_score",
    "rating_notch",
]

# Sector risk scores: higher = riskier
SECTOR_RISK_SCORES = {
    "Energy": 5,
    "TMT": 4,
    "Healthcare": 3,
    "Industrials": 6,
    "Real Estate": 7,
    "Financial Institutions": 5,
    "Infrastructure": 4,
    "Consumer": 6,
}


def _prepare_data(db_path: Path) -> pd.DataFrame:
    """Load obligor data and engineer features for PD modelling."""
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql("SELECT * FROM obligors", conn)
    conn.close()

    # Feature engineering
    df["sector_risk_score"] = df["sector"].map(SECTOR_RISK_SCORES)
    df["rating_notch"] = df["internal_rating"].map(config.RATING_NOTCH)

    # Target: default indicator based on rating
    # Use rating-implied PD as a proxy probability, then sample binary outcomes
    df["pd_implied"] = df["internal_rating"].map(config.RATING_PD_MAP)
    rng = np.random.default_rng(config.RANDOM_SEED)
    df["default_flag"] = (rng.random(len(df)) < df["pd_implied"]).astype(int)

    # Ensure at least some defaults for model training
    # Force CCC-rated obligors to have higher default rate
    ccc_mask = df["internal_rating"] == "CCC"
    df.loc[ccc_mask, "default_flag"] = (rng.random(ccc_mask.sum()) < 0.15).astype(int)

    # Ensure minimum defaults for model stability
    if df["default_flag"].sum() < 5:
        worst = df.nsmallest(8, "interest_coverage").index
        df.loc[worst[:5], "default_flag"] = 1

    logger.info(
        "PD dataset: %d obligors, %d defaults (%.1f%%)",
        len(df), df["default_flag"].sum(),
        100 * df["default_flag"].mean(),
    )
    return df


class PDModel:
    """Logistic regression PD model with scorecard mapping."""

    def __init__(self) -> None:
        self.model: LogisticRegression | None = None
        self.scaler: StandardScaler | None = None
        self.coefficients: dict[str, float] = {}
        self.auc: float = 0.0
        self.gini: float = 0.0
        self.ks_statistic: float = 0.0
        self.roc_curve: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None
        self.scorecard: pd.DataFrame | None = None

    def train(self, db_path: Path | None = None) -> pd.DataFrame:
        """Train the PD model and return obligor-level PD scores."""
        db_path = db_path or config.DB_PATH
        df = _prepare_data(db_path)

        X = df[FEATURES].copy()
        y = df["default_flag"]

        # Standardise features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Logistic regression with class weighting for imbalanced data
        self.model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=config.RANDOM_SEED,
            C=1.0,
        )
        self.model.fit(X_scaled, y)

        # Store coefficients
        self.coefficients = dict(zip(FEATURES, self.model.coef_[0]))
        logger.info("PD model coefficients: %s", self.coefficients)

        # Predicted PDs
        pd_scores = self.model.predict_proba(X_scaled)[:, 1]

        # Override with rating-implied PD floors/caps for realism
        # Blend: 60% model, 40% rating-implied to ensure realistic range
        pd_implied = df["pd_implied"].values
        pd_blended = 0.6 * pd_scores + 0.4 * pd_implied
        pd_blended = np.clip(pd_blended, 0.0001, 0.9999)

        df["pd_score"] = pd_blended

        # Validation metrics
        self._compute_metrics(y, pd_blended)

        # Scorecard
        self.scorecard = self._build_scorecard(df)

        logger.info("PD model trained — AUC: %.4f, Gini: %.4f", self.auc, self.gini)
        return df[["obligor_id", "obligor_name", "internal_rating", "pd_score", "default_flag"]]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict PD for new obligor features."""
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained. Call train() first.")
        X_scaled = self.scaler.transform(X[FEATURES])
        return self.model.predict_proba(X_scaled)[:, 1]

    def _compute_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> None:
        """Compute AUC, Gini, and KS statistic."""
        self.auc = roc_auc_score(y_true, y_pred)
        self.gini = 2 * self.auc - 1

        # ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_pred)
        self.roc_curve = (fpr, tpr, thresholds)

        # KS statistic
        self.ks_statistic = np.max(tpr - fpr)

    def _build_scorecard(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map PD bands to internal rating grades."""
        bins = [0, 0.0003, 0.0008, 0.002, 0.005, 0.015, 0.06, 0.20, 1.0]
        labels = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

        scorecard_rows = []
        for i, label in enumerate(labels):
            mask = (df["pd_score"] >= bins[i]) & (df["pd_score"] < bins[i + 1])
            count = mask.sum()
            avg_pd = df.loc[mask, "pd_score"].mean() if count > 0 else (bins[i] + bins[i + 1]) / 2
            scorecard_rows.append({
                "rating_grade": label,
                "pd_lower": bins[i],
                "pd_upper": bins[i + 1],
                "avg_pd": avg_pd,
                "count": count,
            })

        scorecard = pd.DataFrame(scorecard_rows)
        logger.info("Scorecard:\n%s", scorecard.to_string(index=False))
        return scorecard

    def save(self, path: Path | None = None) -> None:
        """Persist model to disk."""
        path = path or config.PD_MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)
        logger.info("PD model saved to %s", path)

    def load(self, path: Path | None = None) -> None:
        """Load model from disk."""
        path = path or config.PD_MODEL_PATH
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        logger.info("PD model loaded from %s", path)

    def get_metrics(self) -> dict[str, Any]:
        """Return model performance metrics."""
        return {
            "auc": self.auc,
            "gini": self.gini,
            "ks_statistic": self.ks_statistic,
            "coefficients": self.coefficients,
        }
