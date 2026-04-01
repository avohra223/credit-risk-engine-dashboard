"""
Exposure at Default (EAD) Model — Credit Conversion Factor Approach.

For drawn facilities: EAD = current drawn amount.
For undrawn commitments: EAD = drawn + CCF * undrawn.
"""
import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


class EADModel:
    """EAD estimation using regulatory CCF approach."""

    def __init__(self) -> None:
        self.results: pd.DataFrame | None = None
        self.summary_stats: dict = {}

    def estimate(self, db_path: Path | None = None) -> pd.DataFrame:
        """Compute EAD for all facilities."""
        db_path = db_path or config.DB_PATH
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql(
            """
            SELECT f.facility_id, f.obligor_id, f.facility_type,
                   f.commitment_amount, f.drawn_amount, f.undrawn_amount,
                   o.internal_rating, o.sector
            FROM facilities f
            JOIN obligors o ON f.obligor_id = o.obligor_id
            """,
            conn,
        )
        conn.close()

        # Apply CCF
        df["ccf"] = df["facility_type"].map(config.CREDIT_CONVERSION_FACTORS)

        # EAD = drawn + CCF * undrawn
        df["contingent_exposure"] = (df["ccf"] * df["undrawn_amount"]).round(2)
        df["ead"] = (df["drawn_amount"] + df["contingent_exposure"]).round(2)

        self.results = df
        self._compute_summary(df)

        total_ead = df["ead"].sum()
        total_drawn = df["drawn_amount"].sum()
        total_contingent = df["contingent_exposure"].sum()

        logger.info(
            "EAD estimated for %d facilities — Total EAD: EUR %.0fM "
            "(Drawn: EUR %.0fM + Contingent: EUR %.0fM)",
            len(df), total_ead, total_drawn, total_contingent,
        )
        return df

    def _compute_summary(self, df: pd.DataFrame) -> None:
        """Summary statistics for EAD."""
        self.summary_stats = {
            "total_ead": round(df["ead"].sum(), 2),
            "total_drawn": round(df["drawn_amount"].sum(), 2),
            "total_contingent": round(df["contingent_exposure"].sum(), 2),
            "by_facility_type": (
                df.groupby("facility_type")
                .agg(
                    count=("ead", "count"),
                    total_ead=("ead", "sum"),
                    avg_ead=("ead", "mean"),
                    total_drawn=("drawn_amount", "sum"),
                    total_contingent=("contingent_exposure", "sum"),
                )
                .round(2)
                .to_dict()
            ),
        }
