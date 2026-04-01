"""
Central configuration for Credit Risk Engine.
All model parameters, paths, and constants are defined here.
"""
import os
from pathlib import Path

# ── Project Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORTS_DIR = OUTPUT_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = DATA_DIR / "credit_risk.db"
PD_MODEL_PATH = MODELS_DIR / "pd_model.pkl"
LGD_MODEL_PATH = MODELS_DIR / "lgd_model.pkl"

# ── Portfolio Generation ───────────────────────────────────────────────────
RANDOM_SEED = 42
N_OBLIGORS = 250
TARGET_FACILITIES = 400

PORTFOLIO_COMPOSITION = {
    "large_corporate": 0.40,
    "leveraged_finance": 0.25,
    "project_finance": 0.20,
    "structured_finance": 0.15,
}

SECTORS = [
    "Energy", "TMT", "Healthcare", "Industrials",
    "Real Estate", "Financial Institutions", "Infrastructure", "Consumer",
]

COUNTRIES = {
    "France": 0.30,
    "Germany": 0.20,
    "United Kingdom": 0.15,
    "Netherlands": 0.10,
    "Spain": 0.10,
    "Italy": 0.10,
    "Other": 0.05,
}

RATING_GRADES = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

# Rating-to-numeric mapping for modelling
RATING_NOTCH = {
    "AAA": 1, "AA": 2, "A": 3, "BBB": 4,
    "BB": 5, "B": 6, "CCC": 7, "D": 8,
}

# Approximate long-run 1Y PD by rating (basis points)
RATING_PD_MAP = {
    "AAA": 0.0001,
    "AA": 0.0005,
    "A": 0.0010,
    "BBB": 0.0025,
    "BB": 0.0100,
    "B": 0.0400,
    "CCC": 0.1500,
    "D": 1.0000,
}

FACILITY_TYPES = ["term_loan", "revolver", "guarantee", "trade_finance", "bond", "structured_note"]
SENIORITY_LEVELS = ["senior_secured", "senior_unsecured", "subordinated"]
COLLATERAL_TYPES = ["real_estate", "equipment", "financial_assets", "unsecured"]

# ── LGD Model ─────────────────────────────────────────────────────────────
COLLATERAL_HAIRCUTS = {
    "real_estate": 0.30,
    "equipment": 0.50,
    "financial_assets": 0.15,
    "unsecured": 1.00,
}

SENIORITY_LGD_BASE = {
    "senior_secured": 0.25,
    "senior_unsecured": 0.45,
    "subordinated": 0.70,
}

DOWNTURN_LGD_MULTIPLIER = 1.25

# ── EAD Model ─────────────────────────────────────────────────────────────
CREDIT_CONVERSION_FACTORS = {
    "term_loan": 1.00,
    "revolver": 0.75,
    "guarantee": 0.50,
    "trade_finance": 0.20,
    "bond": 1.00,
    "structured_note": 1.00,
}

# ── Portfolio Analytics ────────────────────────────────────────────────────
MONTE_CARLO_SIMULATIONS = 10_000
VAR_CONFIDENCE_LEVELS = [0.95, 0.999]

# Basel II single-factor correlation formula bounds
CORRELATION_R_MIN = 0.12
CORRELATION_R_MAX = 0.24
CORRELATION_K = 50.0

# Concentration limits
SINGLE_NAME_LIMIT = 0.05  # 5% of total portfolio
HHI_THRESHOLD_MODERATE = 0.10
HHI_THRESHOLD_HIGH = 0.18

# ── RWA (IRB Formula) ─────────────────────────────────────────────────────
LGD_FLOOR = 0.10
MATURITY_ADJUSTMENT_B_COEFFS = (0.11852, 0.05478)  # b(PD) = (0.11852 - 0.05478 * ln(PD))^2
CONFIDENCE_LEVEL_IRB = 0.999
SCALING_FACTOR = 1.06  # Basel III 1.06x scaling factor

# ── Stress Testing ────────────────────────────────────────────────────────
STRESS_SCENARIOS = {
    "baseline": {
        "name": "Baseline",
        "gdp_growth": 0.018,
        "unemployment": 0.065,
        "rate_change_bps": 0,
        "pd_multiplier": 1.0,
        "collateral_shock": 0.0,
    },
    "adverse": {
        "name": "Adverse",
        "gdp_growth": -0.012,
        "unemployment": 0.090,
        "rate_change_bps": 200,
        "pd_multiplier": 1.8,
        "collateral_shock": -0.15,
    },
    "severely_adverse": {
        "name": "Severely Adverse",
        "gdp_growth": -0.035,
        "unemployment": 0.120,
        "rate_change_bps": 400,
        "pd_multiplier": 3.0,
        "collateral_shock": -0.30,
    },
}

# Sector sensitivity to unemployment (multiplier per 1pp increase)
SECTOR_UNEMPLOYMENT_SENSITIVITY = {
    "Energy": 0.8,
    "TMT": 0.6,
    "Healthcare": 0.4,
    "Industrials": 1.2,
    "Real Estate": 1.5,
    "Financial Institutions": 1.0,
    "Infrastructure": 0.7,
    "Consumer": 1.4,
}

BASELINE_UNEMPLOYMENT = 0.065

# ── Migration Matrix ──────────────────────────────────────────────────────
# Approximate Moody's/S&P long-run average 1Y transition probabilities (8x8)
# Rows: from rating, Columns: to rating (AAA, AA, A, BBB, BB, B, CCC, D)
TRANSITION_MATRIX = [
    # AAA
    [0.8695, 0.1055, 0.0200, 0.0040, 0.0005, 0.0003, 0.0001, 0.0001],
    # AA
    [0.0100, 0.8680, 0.1000, 0.0150, 0.0040, 0.0015, 0.0010, 0.0005],
    # A
    [0.0005, 0.0250, 0.8750, 0.0780, 0.0130, 0.0050, 0.0020, 0.0015],
    # BBB
    [0.0002, 0.0030, 0.0400, 0.8500, 0.0800, 0.0180, 0.0060, 0.0028],
    # BB
    [0.0001, 0.0005, 0.0050, 0.0550, 0.8000, 0.1050, 0.0250, 0.0094],
    # B
    [0.0001, 0.0002, 0.0020, 0.0080, 0.0650, 0.7950, 0.0900, 0.0397],
    # CCC
    [0.0000, 0.0001, 0.0005, 0.0030, 0.0150, 0.1000, 0.6500, 0.2314],
    # D (absorbing state)
    [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000],
]

# ── Dashboard ──────────────────────────────────────────────────────────────
BRAND_RED = "#E4002B"
BRAND_DARK_GREY = "#333333"
BRAND_LIGHT_GREY = "#F5F5F5"
CHART_PALETTE = [
    "#E4002B", "#1A1A2E", "#16213E", "#0F3460",
    "#533483", "#E94560", "#2C3E50", "#E67E22",
]

# ── Logging ────────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"
