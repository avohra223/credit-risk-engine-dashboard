"""
Credit Risk Engine — Master Orchestrator.

Runs the complete pipeline end-to-end:
1. Generate synthetic portfolio data
2. Train PD, LGD, and EAD models
3. Compute portfolio analytics (EL, VaR, concentration, RWA)
4. Run migration matrix analysis
5. Execute stress testing scenarios
6. Generate output reports
"""
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from data.generate_portfolio import generate
from models.pd_model import PDModel
from models.lgd_model import LGDModel
from models.ead_model import EADModel
from models.validation import pd_validation_report, el_identity_check
from portfolio.expected_loss import compute_expected_loss, aggregate_el
from portfolio.credit_var import run_monte_carlo
from portfolio.concentration import concentration_analysis
from portfolio.rwa import compute_rwa
from migration.transition_matrix import run_migration_analysis
from stress.stress_engine import run_all_scenarios

import numpy as np


def setup_logging() -> logging.Logger:
    """Configure structured logging."""
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("main")


def main() -> None:
    """Execute the full credit risk pipeline."""
    logger = setup_logging()
    start = time.time()

    logger.info("=" * 70)
    logger.info("CREDIT RISK ENGINE — Pipeline Start")
    logger.info("=" * 70)

    # Ensure output directories exist
    config.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: Data Generation ───────────────────────────────────────
    logger.info("Phase 1: Generating synthetic portfolio data...")
    t0 = time.time()
    obligors, facilities = generate()
    logger.info("Phase 1 complete (%.1fs) — %d obligors, %d facilities",
                time.time() - t0, len(obligors), len(facilities))

    # ── Phase 2: Model Training ────────────────────────────────────────
    logger.info("Phase 2: Training risk models...")
    t0 = time.time()

    pd_model = PDModel()
    pd_results = pd_model.train()
    pd_model.save()

    lgd_model = LGDModel()
    lgd_results = lgd_model.estimate()

    ead_model = EADModel()
    ead_results = ead_model.estimate()

    # Validate PD model
    val = pd_validation_report(
        pd_results["default_flag"].values, pd_results["pd_score"].values
    )
    logger.info("PD validation — AUC: %.4f, Gini: %.4f, KS: %.4f",
                val["auc"], val["gini"], val["ks_statistic"])

    logger.info("Phase 2 complete (%.1fs)", time.time() - t0)

    # ── Phase 3: Portfolio Analytics ───────────────────────────────────
    logger.info("Phase 3: Computing portfolio analytics...")
    t0 = time.time()

    el_df = compute_expected_loss(pd_results, lgd_results, ead_results)
    el_agg = aggregate_el(el_df)

    # EL identity check
    identity = el_identity_check(
        el_df["pd_score"].values,
        el_df["lgd"].values,
        el_df["ead"].values,
        el_df["el"].values,
    )
    logger.info("EL identity check: %s (max diff: %.6f)",
                "PASS" if identity["passes"] else "FAIL",
                identity["max_absolute_difference"])

    # Monte Carlo VaR
    var_results = run_monte_carlo(el_df)
    logger.info("VaR(95%%): EUR %.0fM, VaR(99.9%%): EUR %.0fM",
                var_results["var_95"], var_results["var_999"])

    # Concentration
    conc = concentration_analysis(el_df)

    # RWA
    rwa_df = compute_rwa(el_df)

    logger.info("Phase 3 complete (%.1fs)", time.time() - t0)

    # ── Phase 4: Migration Analysis ────────────────────────────────────
    logger.info("Phase 4: Running migration matrix analysis...")
    t0 = time.time()
    migration = run_migration_analysis()
    logger.info("Migration matrix valid: %s", migration["validation"]["is_valid_stochastic"])
    logger.info("Phase 4 complete (%.1fs)", time.time() - t0)

    # ── Phase 5: Stress Testing ────────────────────────────────────────
    logger.info("Phase 5: Running stress test scenarios...")
    t0 = time.time()
    stress_results = run_all_scenarios(el_df)
    logger.info("Phase 5 complete (%.1fs)", time.time() - t0)

    # ── Summary ────────────────────────────────────────────────────────
    elapsed = time.time() - start
    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETE — Total runtime: %.1fs", elapsed)
    logger.info("=" * 70)
    logger.info("Portfolio: %d obligors, %d facilities", len(obligors), len(facilities))
    logger.info("Total EAD: EUR {:,.0f}M".format(el_df["ead"].sum()))
    logger.info("Expected Loss: EUR {:,.0f}M ({:.0f} bps)".format(
        el_df["el"].sum(),
        el_df["el"].sum() / el_df["ead"].sum() * 10_000,
    ))
    logger.info("VaR (99.9%%): EUR {:,.0f}M".format(var_results["var_999"]))
    logger.info("Total RWA: EUR {:,.0f}M".format(rwa_df["rwa"].sum()))
    logger.info("Stress (Severe) EL: EUR {:,.0f}M (+{:.0f}%%)".format(
        stress_results["severely_adverse"]["total_el_stressed"],
        stress_results["severely_adverse"]["el_increase_pct"],
    ))
    logger.info("=" * 70)
    logger.info("Launch dashboard: streamlit run dashboard/app.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
