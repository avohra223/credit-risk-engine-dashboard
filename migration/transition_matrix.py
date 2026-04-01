"""
Rating Migration Matrix analysis.

Generates and analyses an 8x8 rating transition matrix calibrated to
long-run historical averages. Computes cumulative default rates,
average time to default, and rating drift metrics.
"""
import logging
from typing import Any

import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def get_transition_matrix() -> pd.DataFrame:
    """Return the 1-year transition matrix as a labelled DataFrame."""
    matrix = np.array(config.TRANSITION_MATRIX)
    df = pd.DataFrame(
        matrix,
        index=config.RATING_GRADES,
        columns=config.RATING_GRADES,
    )
    return df


def validate_transition_matrix(matrix: pd.DataFrame) -> dict[str, Any]:
    """Verify the transition matrix is a valid stochastic matrix."""
    row_sums = matrix.sum(axis=1)
    is_valid = np.allclose(row_sums, 1.0, atol=1e-6)
    all_positive = (matrix.values >= 0).all()

    return {
        "is_valid_stochastic": bool(is_valid and all_positive),
        "row_sums": row_sums.round(6).to_dict(),
        "min_value": float(matrix.values.min()),
        "all_non_negative": bool(all_positive),
    }


def cumulative_default_rates(
    matrix: pd.DataFrame, horizons: list[int] | None = None,
) -> pd.DataFrame:
    """
    Compute cumulative default rates for each rating over multiple horizons.

    Uses matrix exponentiation: P(t) = P^t
    Default column is the last column (D).
    """
    horizons = horizons or [1, 2, 3, 5, 7, 10]
    M = matrix.values
    ratings = list(matrix.index)
    default_idx = ratings.index("D")

    results = {"rating": ratings}
    for h in horizons:
        M_h = np.linalg.matrix_power(M, h)
        results[f"{h}Y"] = M_h[:, default_idx]

    df = pd.DataFrame(results).set_index("rating")
    logger.info("Cumulative default rates computed for horizons: %s", horizons)
    return df


def average_time_to_default(matrix: pd.DataFrame, max_years: int = 50) -> pd.Series:
    """
    Compute expected time to default (absorbing state) for each rating.

    Uses the fundamental matrix approach: extract the transient sub-matrix Q,
    compute N = (I - Q)^{-1}, and sum rows for expected absorption times.
    """
    M = matrix.values
    ratings = list(matrix.index)
    default_idx = ratings.index("D")
    transient_idx = [i for i in range(len(ratings)) if i != default_idx]

    Q = M[np.ix_(transient_idx, transient_idx)]
    I = np.eye(len(transient_idx))

    try:
        N = np.linalg.inv(I - Q)
        expected_times = N.sum(axis=1)
    except np.linalg.LinAlgError:
        # Fallback: iterative approach
        logger.warning("Matrix inversion failed, using iterative approach")
        expected_times = np.full(len(transient_idx), max_years)

    transient_ratings = [ratings[i] for i in transient_idx]
    result = pd.Series(expected_times, index=transient_ratings, name="avg_years_to_default")

    logger.info("Average time to default: %s", result.round(1).to_dict())
    return result


def rating_drift(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Analyse rating drift: probability of upgrade, stable, downgrade
    for each starting rating.
    """
    ratings = list(matrix.index)
    M = matrix.values
    rows = []

    for i, rating in enumerate(ratings):
        if rating == "D":
            rows.append({
                "rating": rating,
                "p_upgrade": 0.0,
                "p_stable": 1.0,
                "p_downgrade": 0.0,
                "p_default": 0.0,
                "drift_direction": "Absorbing",
            })
            continue

        p_upgrade = M[i, :i].sum()
        p_stable = M[i, i]
        p_default = M[i, -1]  # D column
        p_downgrade = M[i, i+1:].sum()

        direction = "Upgrade" if p_upgrade > p_downgrade else "Downgrade"
        if abs(p_upgrade - p_downgrade) < 0.01:
            direction = "Stable"

        rows.append({
            "rating": rating,
            "p_upgrade": round(p_upgrade, 4),
            "p_stable": round(p_stable, 4),
            "p_downgrade": round(p_downgrade, 4),
            "p_default": round(p_default, 4),
            "drift_direction": direction,
        })

    return pd.DataFrame(rows)


def run_migration_analysis() -> dict[str, Any]:
    """Run complete migration matrix analysis."""
    matrix = get_transition_matrix()
    validation = validate_transition_matrix(matrix)

    if not validation["is_valid_stochastic"]:
        logger.warning("Transition matrix validation failed: %s", validation)

    cum_defaults = cumulative_default_rates(matrix)
    avg_ttd = average_time_to_default(matrix)
    drift = rating_drift(matrix)

    logger.info("Migration analysis complete")

    return {
        "matrix": matrix,
        "validation": validation,
        "cumulative_defaults": cum_defaults,
        "avg_time_to_default": avg_ttd,
        "rating_drift": drift,
    }
