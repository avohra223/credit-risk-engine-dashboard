"""
Expected Loss (EL) calculation module.

EL = PD x LGD x EAD, aggregated at facility, obligor, sector, rating,
and geographic level.
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_expected_loss(
    pd_results: pd.DataFrame,
    lgd_results: pd.DataFrame,
    ead_results: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute facility-level Expected Loss and return enriched DataFrame.

    Merges PD (obligor-level), LGD (facility-level), and EAD (facility-level)
    into a single facility-level table with EL = PD * LGD * EAD.
    """
    # Merge PD onto facilities via obligor_id
    merged = ead_results.merge(
        pd_results[["obligor_id", "pd_score", "internal_rating"]],
        on="obligor_id",
        how="left",
        suffixes=("", "_pd"),
    )

    # Merge LGD
    merged = merged.merge(
        lgd_results[["facility_id", "lgd", "lgd_downturn", "seniority", "collateral_type"]],
        on="facility_id",
        how="left",
    )

    # Use internal_rating from pd_results if not already present
    if "internal_rating_pd" in merged.columns:
        merged["internal_rating"] = merged["internal_rating"].fillna(merged["internal_rating_pd"])
        merged.drop(columns=["internal_rating_pd"], inplace=True)

    # Compute EL
    merged["el"] = (merged["pd_score"] * merged["lgd"] * merged["ead"]).round(4)
    merged["el_downturn"] = (merged["pd_score"] * merged["lgd_downturn"] * merged["ead"]).round(4)

    total_el = merged["el"].sum()
    total_ead = merged["ead"].sum()
    el_bps = (total_el / total_ead * 10_000) if total_ead > 0 else 0

    logger.info(
        "Expected Loss: EUR %.1fM (%.0f bps of total EAD EUR %.0fM)",
        total_el, el_bps, total_ead,
    )

    return merged


def aggregate_el(el_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Aggregate EL by sector, rating, and country."""
    aggregations = {}

    for group_col, name in [
        ("sector", "by_sector"),
        ("internal_rating", "by_rating"),
    ]:
        if group_col in el_df.columns:
            agg = (
                el_df.groupby(group_col)
                .agg(
                    n_facilities=("facility_id", "count"),
                    total_ead=("ead", "sum"),
                    total_el=("el", "sum"),
                    avg_pd=("pd_score", "mean"),
                    avg_lgd=("lgd", "mean"),
                )
                .round(4)
            )
            agg["el_bps"] = ((agg["total_el"] / agg["total_ead"]) * 10_000).round(1)
            aggregations[name] = agg

    logger.info("EL aggregated by %d dimensions", len(aggregations))
    return aggregations
