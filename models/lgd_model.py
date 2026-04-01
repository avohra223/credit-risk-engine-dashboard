"""
Loss Given Default (LGD) Model — Beta Regression Approach.

Estimates recovery rates by collateral type, seniority, and sector.
Applies downturn adjustment per regulatory requirements.
"""
import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


class LGDModel:
    """LGD estimation using collateral-based approach with beta-distributed outputs."""

    def __init__(self) -> None:
        self.results: pd.DataFrame | None = None
        self.summary_stats: dict = {}

    def estimate(self, db_path: Path | None = None) -> pd.DataFrame:
        """Estimate LGD for all facilities in the portfolio."""
        db_path = db_path or config.DB_PATH
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql(
            """
            SELECT f.facility_id, f.obligor_id, f.facility_type, f.commitment_amount,
                   f.drawn_amount, f.seniority, f.collateral_type, f.collateral_value,
                   o.sector, o.country, o.internal_rating
            FROM facilities f
            JOIN obligors o ON f.obligor_id = o.obligor_id
            """,
            conn,
        )
        conn.close()

        rng = np.random.default_rng(config.RANDOM_SEED + 1)

        lgd_values = []
        ci_lower = []
        ci_upper = []

        for _, row in df.iterrows():
            # Base LGD from seniority
            base_lgd = config.SENIORITY_LGD_BASE[row["seniority"]]

            # Collateral benefit
            haircut = config.COLLATERAL_HAIRCUTS[row["collateral_type"]]
            if row["commitment_amount"] > 0 and row["collateral_value"] > 0:
                collateral_coverage = (
                    row["collateral_value"] * (1 - haircut) / row["commitment_amount"]
                )
                collateral_benefit = min(collateral_coverage, 1.0) * 0.5
            else:
                collateral_benefit = 0.0

            # Adjusted LGD
            point_lgd = max(base_lgd - collateral_benefit, 0.05)

            # Sector adjustment: riskier sectors have slightly higher LGD
            sector_adj = config.SECTOR_UNEMPLOYMENT_SENSITIVITY.get(row["sector"], 1.0)
            point_lgd *= (0.85 + 0.15 * sector_adj)

            # Add noise via beta distribution for confidence intervals
            # Parameterise beta with mean = point_lgd, concentration ~ 20
            point_lgd = np.clip(point_lgd, 0.01, 0.99)
            alpha = point_lgd * 20
            beta_param = (1 - point_lgd) * 20
            sample = rng.beta(alpha, beta_param, size=1000)

            lgd_values.append(round(float(np.mean(sample)), 6))
            ci_lower.append(round(float(np.percentile(sample, 2.5)), 6))
            ci_upper.append(round(float(np.percentile(sample, 97.5)), 6))

        df["lgd"] = lgd_values
        df["lgd_ci_lower"] = ci_lower
        df["lgd_ci_upper"] = ci_upper

        # Downturn LGD
        df["lgd_downturn"] = np.clip(
            df["lgd"] * config.DOWNTURN_LGD_MULTIPLIER, 0.0, 1.0
        ).round(6)

        self.results = df
        self._compute_summary(df)

        logger.info(
            "LGD estimated for %d facilities — mean LGD: %.2f%%, mean downturn LGD: %.2f%%",
            len(df), df["lgd"].mean() * 100, df["lgd_downturn"].mean() * 100,
        )
        return df

    def _compute_summary(self, df: pd.DataFrame) -> None:
        """Compute summary statistics by collateral type and seniority."""
        self.summary_stats = {
            "by_collateral": (
                df.groupby("collateral_type")["lgd"]
                .agg(["mean", "std", "min", "max", "count"])
                .round(4)
                .to_dict()
            ),
            "by_seniority": (
                df.groupby("seniority")["lgd"]
                .agg(["mean", "std", "min", "max", "count"])
                .round(4)
                .to_dict()
            ),
            "overall_mean": round(df["lgd"].mean(), 4),
            "overall_std": round(df["lgd"].std(), 4),
            "downturn_mean": round(df["lgd_downturn"].mean(), 4),
        }
