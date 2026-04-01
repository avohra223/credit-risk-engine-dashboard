"""
Credit Value at Risk (VaR) via Monte Carlo simulation.

Uses a single-factor Gaussian copula model (Basel II approach) with
asset correlation parameterised as per the IRB formula.
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


def _asset_correlation(pd_values: np.ndarray) -> np.ndarray:
    """
    Basel II single-factor asset correlation.
    R = 0.12 * (1 - exp(-50*PD)) / (1 - exp(-50)) + 0.24 * (1 - (1 - exp(-50*PD)) / (1 - exp(-50)))
    """
    exp_factor = (1 - np.exp(-config.CORRELATION_K * pd_values)) / (1 - np.exp(-config.CORRELATION_K))
    r = config.CORRELATION_R_MIN * exp_factor + config.CORRELATION_R_MAX * (1 - exp_factor)
    return r


def run_monte_carlo(
    el_df: pd.DataFrame,
    n_simulations: int | None = None,
    seed: int | None = None,
) -> dict:
    """
    Run Monte Carlo simulation for portfolio credit losses.

    Uses single-factor Gaussian copula:
    - Common systematic factor Z ~ N(0,1)
    - Idiosyncratic factor eps_i ~ N(0,1)
    - Asset value: A_i = sqrt(R_i) * Z + sqrt(1 - R_i) * eps_i
    - Default if A_i < Phi^{-1}(PD_i)

    Returns dict with loss distribution, VaR, and ES statistics.
    """
    n_simulations = n_simulations or config.MONTE_CARLO_SIMULATIONS
    seed = seed or config.RANDOM_SEED
    rng = np.random.default_rng(seed + 100)

    pd_values = el_df["pd_score"].values
    lgd_values = el_df["lgd"].values
    ead_values = el_df["ead"].values
    n_facilities = len(el_df)

    # Asset correlations
    correlations = _asset_correlation(pd_values)

    # Default thresholds
    default_thresholds = norm.ppf(pd_values)

    # Simulate
    logger.info("Running %d Monte Carlo simulations for %d facilities", n_simulations, n_facilities)

    portfolio_losses = np.zeros(n_simulations)

    for sim in range(n_simulations):
        # Systematic factor
        z = rng.standard_normal()

        # Idiosyncratic factors
        eps = rng.standard_normal(n_facilities)

        # Asset values
        asset_values = np.sqrt(correlations) * z + np.sqrt(1 - correlations) * eps

        # Default indicators
        defaults = (asset_values < default_thresholds).astype(float)

        # Portfolio loss
        portfolio_losses[sim] = np.sum(defaults * lgd_values * ead_values)

    # Compute statistics
    expected_loss = np.mean(portfolio_losses)
    var_results = {}
    for cl in config.VAR_CONFIDENCE_LEVELS:
        var_results[f"var_{cl}"] = float(np.percentile(portfolio_losses, cl * 100))

    es_99 = float(np.mean(portfolio_losses[portfolio_losses >= var_results.get("var_0.99", var_results.get("var_0.999", 0))]))

    total_ead = ead_values.sum()

    results = {
        "n_simulations": n_simulations,
        "n_facilities": n_facilities,
        "loss_distribution": portfolio_losses,
        "expected_loss_mc": round(expected_loss, 2),
        "expected_loss_analytical": round(float(np.sum(pd_values * lgd_values * ead_values)), 2),
        "var_95": round(var_results.get("var_0.95", 0), 2),
        "var_999": round(var_results.get("var_0.999", 0), 2),
        "total_ead": round(total_ead, 2),
        "var_95_pct": round(var_results.get("var_0.95", 0) / total_ead * 100, 4) if total_ead > 0 else 0,
        "var_999_pct": round(var_results.get("var_0.999", 0) / total_ead * 100, 4) if total_ead > 0 else 0,
        "mean_correlation": round(float(np.mean(correlations)), 4),
    }

    logger.info(
        "Monte Carlo complete — EL: EUR %.0fM, VaR(95%%): EUR %.0fM, VaR(99.9%%): EUR %.0fM",
        results["expected_loss_mc"], results["var_95"], results["var_999"],
    )

    return results
