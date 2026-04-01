"""
Stress testing engine.

Applies macroeconomic shocks to PD, LGD, and EAD parameters and
re-computes portfolio losses under each scenario.

Transmission mechanism:
- GDP shock -> PD multiplier
- Unemployment shock -> sector-specific PD adjustment
- Rate shock -> interest coverage degradation -> PD re-estimation
- Collateral value shock -> LGD increase
"""
import logging
from typing import Any

import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from portfolio.credit_var import run_monte_carlo

logger = logging.getLogger(__name__)


def _apply_pd_stress(
    el_df: pd.DataFrame, scenario: dict[str, Any]
) -> pd.DataFrame:
    """Apply PD stress via multiplier and sector-unemployment sensitivity."""
    df = el_df.copy()

    # Base PD multiplier from GDP/macro scenario
    base_multiplier = scenario["pd_multiplier"]

    # Sector-specific unemployment adjustment
    unemployment_delta = scenario["unemployment"] - config.BASELINE_UNEMPLOYMENT
    sector_adj = df["sector"].map(config.SECTOR_UNEMPLOYMENT_SENSITIVITY)
    unemployment_multiplier = 1.0 + sector_adj * unemployment_delta * 2.0

    # Rate shock -> ICR degradation (approximate)
    # Higher rates increase interest expense, lowering ICR
    rate_bps = scenario["rate_change_bps"]
    rate_impact = 1.0 + (rate_bps / 10_000) * 3.0  # ~3x leverage on rate sensitivity

    # Combined PD stress
    df["pd_stressed"] = np.clip(
        df["pd_score"] * base_multiplier * unemployment_multiplier * rate_impact,
        0.0001,
        0.9999,
    )

    return df


def _apply_lgd_stress(
    df: pd.DataFrame, scenario: dict[str, Any]
) -> pd.DataFrame:
    """Apply collateral value shock to LGD."""
    collateral_shock = scenario["collateral_shock"]

    # LGD increases when collateral values drop
    # Use downturn LGD as starting point for adverse scenarios
    if collateral_shock < 0:
        # Reduce collateral benefit -> increase LGD
        lgd_uplift = abs(collateral_shock)
        df["lgd_stressed"] = np.clip(
            df["lgd_downturn"] + lgd_uplift * (1 - df["lgd_downturn"]) * 0.3,
            0.05,
            0.99,
        )
    else:
        df["lgd_stressed"] = df["lgd"]

    return df


def run_stress_test(
    el_df: pd.DataFrame,
    scenario_key: str,
    n_simulations: int | None = None,
) -> dict[str, Any]:
    """
    Run a single stress scenario on the portfolio.

    Returns stressed EL, stressed VaR, and capital impact.
    """
    scenario = config.STRESS_SCENARIOS[scenario_key]
    logger.info("Running stress test: %s", scenario["name"])

    df = _apply_pd_stress(el_df, scenario)
    df = _apply_lgd_stress(df, scenario)

    # Stressed EL
    df["el_stressed"] = (df["pd_stressed"] * df["lgd_stressed"] * df["ead"]).round(4)

    total_el_base = el_df["el"].sum()
    total_el_stressed = df["el_stressed"].sum()
    total_ead = df["ead"].sum()

    # Stressed VaR (Monte Carlo) — replace base PD/LGD with stressed values
    stressed_mc_df = df.drop(columns=["pd_score", "lgd"], errors="ignore").rename(
        columns={"pd_stressed": "pd_score", "lgd_stressed": "lgd"}
    )
    var_results = run_monte_carlo(
        stressed_mc_df,
        n_simulations=n_simulations or config.MONTE_CARLO_SIMULATIONS,
        seed=config.RANDOM_SEED + hash(scenario_key) % 1000,
    )

    # Capital impact
    capital_base = total_el_base  # Simplified: capital ~ EL
    capital_stressed = total_el_stressed

    results = {
        "scenario": scenario["name"],
        "scenario_key": scenario_key,
        "parameters": scenario,
        "stressed_data": df,
        "total_el_baseline": round(total_el_base, 2),
        "total_el_stressed": round(total_el_stressed, 2),
        "el_increase_pct": round((total_el_stressed / total_el_base - 1) * 100, 1) if total_el_base > 0 else 0,
        "el_stressed_bps": round(total_el_stressed / total_ead * 10_000, 1) if total_ead > 0 else 0,
        "var_95_stressed": var_results["var_95"],
        "var_999_stressed": var_results["var_999"],
        "loss_distribution": var_results["loss_distribution"],
        "avg_pd_stressed": round(float(df["pd_stressed"].mean()), 6),
        "avg_lgd_stressed": round(float(df["lgd_stressed"].mean()), 4),
    }

    logger.info(
        "Stress %s — EL: EUR %.0fM -> EUR %.0fM (+%.0f%%), "
        "VaR(99.9%%): EUR %.0fM",
        scenario["name"], total_el_base, total_el_stressed,
        results["el_increase_pct"], results["var_999_stressed"],
    )

    return results


def run_all_scenarios(
    el_df: pd.DataFrame, n_simulations: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Run all three stress scenarios and return comparison."""
    results = {}
    for key in config.STRESS_SCENARIOS:
        results[key] = run_stress_test(el_df, key, n_simulations)

    # Build comparison table
    comparison = pd.DataFrame([
        {
            "Scenario": r["scenario"],
            "EL (EUR M)": r["total_el_stressed"],
            "EL (bps)": r["el_stressed_bps"],
            "EL Change (%)": r["el_increase_pct"],
            "VaR 95% (EUR M)": r["var_95_stressed"],
            "VaR 99.9% (EUR M)": r["var_999_stressed"],
            "Avg PD": r["avg_pd_stressed"],
            "Avg LGD": r["avg_lgd_stressed"],
        }
        for r in results.values()
    ])

    results["_comparison"] = comparison
    logger.info("All stress scenarios complete:\n%s", comparison.to_string(index=False))

    return results
