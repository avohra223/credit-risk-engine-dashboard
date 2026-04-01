"""
Model validation utilities for PD, LGD, and EAD models.

Provides discriminatory power metrics, calibration tests, and
visualisation helpers for model governance reporting.
"""
import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    mean_absolute_error,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def gini_coefficient(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Gini coefficient (2 * AUC - 1)."""
    auc = roc_auc_score(y_true, y_pred)
    return 2 * auc - 1


def ks_statistic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Kolmogorov-Smirnov statistic: max separation between default/non-default CDFs."""
    defaults = y_pred[y_true == 1]
    non_defaults = y_pred[y_true == 0]
    if len(defaults) == 0 or len(non_defaults) == 0:
        return 0.0
    stat, _ = stats.ks_2samp(defaults, non_defaults)
    return float(stat)


def hosmer_lemeshow_test(
    y_true: np.ndarray, y_pred: np.ndarray, n_groups: int = 10
) -> dict[str, float]:
    """
    Hosmer-Lemeshow goodness-of-fit test.
    Returns chi-squared statistic and p-value.
    """
    df = pd.DataFrame({"actual": y_true, "predicted": y_pred})
    df["group"] = pd.qcut(df["predicted"], n_groups, duplicates="drop")

    grouped = df.groupby("group", observed=True).agg(
        obs_default=("actual", "sum"),
        obs_count=("actual", "count"),
        pred_default=("predicted", "sum"),
    )

    grouped["exp_default"] = grouped["pred_default"]
    grouped["exp_non_default"] = grouped["obs_count"] - grouped["exp_default"]
    grouped["obs_non_default"] = grouped["obs_count"] - grouped["obs_default"]

    # Chi-squared
    chi2 = 0.0
    for _, row in grouped.iterrows():
        if row["exp_default"] > 0:
            chi2 += (row["obs_default"] - row["exp_default"]) ** 2 / row["exp_default"]
        if row["exp_non_default"] > 0:
            chi2 += (row["obs_non_default"] - row["exp_non_default"]) ** 2 / row["exp_non_default"]

    dof = max(len(grouped) - 2, 1)
    p_value = 1 - stats.chi2.cdf(chi2, dof)

    return {"chi2": round(chi2, 4), "p_value": round(p_value, 4), "dof": dof}


def pd_validation_report(
    y_true: np.ndarray, y_pred: np.ndarray
) -> dict[str, Any]:
    """Comprehensive PD model validation metrics."""
    return {
        "auc": round(roc_auc_score(y_true, y_pred), 4),
        "gini": round(gini_coefficient(y_true, y_pred), 4),
        "ks_statistic": round(ks_statistic(y_true, y_pred), 4),
        "brier_score": round(brier_score_loss(y_true, y_pred), 6),
        "log_loss": round(log_loss(y_true, y_pred), 6),
        "hosmer_lemeshow": hosmer_lemeshow_test(y_true, y_pred),
        "default_rate": round(float(np.mean(y_true)), 4),
        "mean_predicted_pd": round(float(np.mean(y_pred)), 4),
    }


def lgd_validation_report(
    actual_lgd: np.ndarray, predicted_lgd: np.ndarray
) -> dict[str, float]:
    """LGD model validation metrics."""
    return {
        "mae": round(mean_absolute_error(actual_lgd, predicted_lgd), 4),
        "mean_actual": round(float(np.mean(actual_lgd)), 4),
        "mean_predicted": round(float(np.mean(predicted_lgd)), 4),
        "std_actual": round(float(np.std(actual_lgd)), 4),
        "std_predicted": round(float(np.std(predicted_lgd)), 4),
        "correlation": round(float(np.corrcoef(actual_lgd, predicted_lgd)[0, 1]), 4),
    }


def el_identity_check(
    pd_values: np.ndarray,
    lgd_values: np.ndarray,
    ead_values: np.ndarray,
    el_values: np.ndarray,
    tolerance: float = 0.01,
) -> dict[str, Any]:
    """Verify EL = PD * LGD * EAD identity holds for all facilities."""
    expected_el = pd_values * lgd_values * ead_values
    diff = np.abs(el_values - expected_el)
    max_diff = float(np.max(diff))
    passes = max_diff < tolerance

    return {
        "passes": passes,
        "max_absolute_difference": round(max_diff, 6),
        "mean_absolute_difference": round(float(np.mean(diff)), 6),
        "n_facilities": len(pd_values),
    }
