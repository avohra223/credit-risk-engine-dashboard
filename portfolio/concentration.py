"""
Concentration risk analysis.

Computes Herfindahl-Hirschman Index (HHI), single-name concentration,
and top-N exposure metrics.
"""
import logging

import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def herfindahl_index(exposures: pd.Series) -> float:
    """Compute HHI from a series of exposures."""
    total = exposures.sum()
    if total == 0:
        return 0.0
    shares = exposures / total
    return float((shares ** 2).sum())


def concentration_analysis(el_df: pd.DataFrame) -> dict:
    """
    Full concentration risk analysis.

    Returns HHI by sector and obligor, top-N exposures,
    and single-name limit breaches.
    """
    total_ead = el_df["ead"].sum()

    # ── Sector HHI ─────────────────────────────────────────────────────
    sector_ead = el_df.groupby("sector")["ead"].sum()
    hhi_sector = herfindahl_index(sector_ead)

    # ── Obligor HHI ────────────────────────────────────────────────────
    obligor_ead = el_df.groupby("obligor_id")["ead"].sum()
    hhi_obligor = herfindahl_index(obligor_ead)

    # ── Top 10 obligors ────────────────────────────────────────────────
    top_10 = (
        el_df.groupby("obligor_id")
        .agg(total_ead=("ead", "sum"), sector=("sector", "first"))
        .nlargest(10, "total_ead")
    )
    top_10["pct_of_portfolio"] = (top_10["total_ead"] / total_ead * 100).round(2)

    # ── Single-name breaches ───────────────────────────────────────────
    obligor_shares = obligor_ead / total_ead
    breaches = obligor_shares[obligor_shares > config.SINGLE_NAME_LIMIT]

    # ── Top 10 concentration ratio ─────────────────────────────────────
    top_10_share = top_10["total_ead"].sum() / total_ead if total_ead > 0 else 0

    results = {
        "hhi_sector": round(hhi_sector, 6),
        "hhi_obligor": round(hhi_obligor, 6),
        "hhi_sector_classification": _classify_hhi(hhi_sector),
        "top_10_obligors": top_10.reset_index(),
        "top_10_concentration_ratio": round(top_10_share, 4),
        "single_name_breaches": len(breaches),
        "breach_details": breaches.reset_index() if len(breaches) > 0 else pd.DataFrame(),
        "sector_exposure": sector_ead.sort_values(ascending=False).reset_index(),
        "total_ead": round(total_ead, 2),
    }

    logger.info(
        "Concentration — Sector HHI: %.4f (%s), Obligor HHI: %.6f, "
        "Top-10 share: %.1f%%, Single-name breaches: %d",
        hhi_sector, results["hhi_sector_classification"],
        hhi_obligor, top_10_share * 100, len(breaches),
    )

    return results


def _classify_hhi(hhi: float) -> str:
    """Classify HHI into risk buckets."""
    if hhi < config.HHI_THRESHOLD_MODERATE:
        return "Low"
    elif hhi < config.HHI_THRESHOLD_HIGH:
        return "Moderate"
    else:
        return "High"
