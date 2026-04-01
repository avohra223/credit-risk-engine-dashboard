"""
Risk-Weighted Assets (RWA) calculation using Basel III IRB formula.

Implements the Foundation IRB approach for corporate exposures.
"""
import logging

import numpy as np
import pandas as pd
from scipy.stats import norm

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def _maturity_adjustment(pd_values: np.ndarray) -> np.ndarray:
    """Compute maturity adjustment factor b(PD)."""
    a, b = config.MATURITY_ADJUSTMENT_B_COEFFS
    return (a - b * np.log(np.maximum(pd_values, 1e-10))) ** 2


def _asset_correlation(pd_values: np.ndarray) -> np.ndarray:
    """Basel II/III asset correlation for corporates."""
    k = config.CORRELATION_K
    exp_factor = (1 - np.exp(-k * pd_values)) / (1 - np.exp(-k))
    return config.CORRELATION_R_MIN * exp_factor + config.CORRELATION_R_MAX * (1 - exp_factor)


def compute_rwa(el_df: pd.DataFrame, maturity: float = 2.5) -> pd.DataFrame:
    """
    Compute RWA per facility using IRB formula.

    K = [LGD * N((1-R)^-0.5 * G(PD) + (R/(1-R))^0.5 * G(0.999)) - PD * LGD]
        * (1 - 1.5*b)^-1 * (1 + (M-2.5)*b) * 1.06

    RWA = K * 12.5 * EAD
    """
    pd_values = el_df["pd_score"].values
    lgd_values = np.maximum(el_df["lgd"].values, config.LGD_FLOOR)
    ead_values = el_df["ead"].values

    # Asset correlation
    R = _asset_correlation(pd_values)

    # Maturity adjustment
    b = _maturity_adjustment(pd_values)
    maturity_factor = (1 + (maturity - 2.5) * b) / (1 - 1.5 * b)

    # Capital requirement K
    z_999 = norm.ppf(config.CONFIDENCE_LEVEL_IRB)
    conditional_pd = norm.cdf(
        (norm.ppf(pd_values) + np.sqrt(R) * z_999) / np.sqrt(1 - R)
    )

    K = (lgd_values * conditional_pd - pd_values * lgd_values) * maturity_factor * config.SCALING_FACTOR
    K = np.maximum(K, 0.0)

    # RWA = K * 12.5 * EAD
    rwa = K * 12.5 * ead_values

    result = el_df.copy()
    result["capital_requirement_K"] = np.round(K, 6)
    result["rwa"] = np.round(rwa, 2)
    result["rwa_density"] = np.where(
        ead_values > 0, np.round(rwa / ead_values, 4), 0.0
    )

    total_rwa = result["rwa"].sum()
    total_ead = result["ead"].sum()
    avg_density = total_rwa / total_ead if total_ead > 0 else 0

    logger.info(
        "RWA: EUR %.0fM (density: %.1f%%), Total EAD: EUR %.0fM",
        total_rwa, avg_density * 100, total_ead,
    )

    return result
