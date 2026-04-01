"""
Macroeconomic scenario definitions for EBA-style stress testing.

Three scenarios: Baseline, Adverse, Severely Adverse.
"""
import logging
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)


def get_scenarios() -> dict[str, dict[str, Any]]:
    """Return all stress test scenarios from config."""
    return config.STRESS_SCENARIOS


def describe_scenarios() -> str:
    """Return a formatted description of all scenarios."""
    lines = []
    for key, scen in config.STRESS_SCENARIOS.items():
        lines.append(f"\n{'='*60}")
        lines.append(f"Scenario: {scen['name']}")
        lines.append(f"{'='*60}")
        lines.append(f"  GDP Growth:          {scen['gdp_growth']:+.1%}")
        lines.append(f"  Unemployment:        {scen['unemployment']:.1%}")
        lines.append(f"  Rate Change:         {scen['rate_change_bps']:+d} bps")
        lines.append(f"  PD Multiplier:       {scen['pd_multiplier']:.1f}x")
        lines.append(f"  Collateral Shock:    {scen['collateral_shock']:+.0%}")
    return "\n".join(lines)
