"""
Synthetic portfolio generator for Credit Risk Engine.

Generates 250 obligors and ~400 facilities with realistic financial profiles
calibrated to a European CIB lending book. Data is loaded into a SQLite database.
"""
import logging
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logger = logging.getLogger(__name__)

# ── Fictional company name generator ───────────────────────────────────────

_PREFIXES = [
    "Aurion", "Vectis", "Nexora", "Caldera", "Terravolt", "Zephyra", "Stratos",
    "Primatech", "Solera", "Kordex", "Heliox", "Crestline", "Meridia", "Axona",
    "Boreal", "Cintra", "Delphos", "Equinor", "Fidelis", "Genova", "Halcyon",
    "Ionics", "Jorvex", "Kaelen", "Luminos", "Montara", "Novalis", "Orinex",
    "Palladian", "Quantex", "Rivero", "Sylvane", "Tiberion", "Unova", "Valcrest",
    "Wyndham", "Xenara", "Ysolde", "Zentara", "Altheus", "Brantex", "Corvinus",
    "Domaris", "Elantra", "Florex", "Greystone", "Helicon", "Iveron", "Javara",
]

_SUFFIXES = [
    "Industries", "Capital", "Group", "Holdings", "Partners", "Energy", "Finance",
    "Technologies", "Infrastructure", "Solutions", "Corp", "Ventures", "Systems",
    "Resources", "Dynamics", "Global", "International", "Services", "Management",
    "Enterprises",
]


def _generate_name(rng: np.random.Generator, used: set) -> str:
    """Generate a unique fictional company name."""
    for _ in range(500):
        name = f"{rng.choice(_PREFIXES)} {rng.choice(_SUFFIXES)}"
        if name not in used:
            used.add(name)
            return name
    return f"Company-{uuid.uuid4().hex[:8]}"


# ── Obligor generation ─────────────────────────────────────────────────────

def _assign_segments(n: int, rng: np.random.Generator) -> np.ndarray:
    """Assign obligor segments according to portfolio composition targets."""
    segments = []
    for seg, pct in config.PORTFOLIO_COMPOSITION.items():
        segments.extend([seg] * int(round(n * pct)))
    # Fill any rounding gap
    while len(segments) < n:
        segments.append(rng.choice(list(config.PORTFOLIO_COMPOSITION.keys())))
    rng.shuffle(segments)
    return np.array(segments[:n])


def _assign_ratings(segment: str, rng: np.random.Generator) -> str:
    """Assign an internal rating consistent with the obligor segment."""
    if segment == "large_corporate":
        return rng.choice(
            ["AAA", "AA", "A", "BBB", "BB"],
            p=[0.03, 0.10, 0.30, 0.40, 0.17],
        )
    elif segment == "leveraged_finance":
        return rng.choice(
            ["BBB", "BB", "B", "CCC"],
            p=[0.10, 0.40, 0.40, 0.10],
        )
    elif segment == "project_finance":
        return rng.choice(
            ["A", "BBB", "BB", "B"],
            p=[0.10, 0.40, 0.35, 0.15],
        )
    else:  # structured_finance
        return rng.choice(
            ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"],
            p=[0.15, 0.20, 0.20, 0.20, 0.15, 0.08, 0.02],
        )


def _generate_financials(
    segment: str, rating: str, rng: np.random.Generator
) -> dict:
    """Generate realistic financial statement data for an obligor."""
    rating_quality = config.RATING_NOTCH[rating]

    if segment == "large_corporate":
        total_assets = rng.uniform(2_000, 50_000)  # EUR millions
        if rating_quality <= 3:  # IG
            leverage = rng.uniform(0.15, 0.40)
            icr = rng.uniform(4.0, 15.0)
        else:
            leverage = rng.uniform(0.30, 0.55)
            icr = rng.uniform(2.0, 5.0)
    elif segment == "leveraged_finance":
        total_assets = rng.uniform(500, 5_000)
        leverage = rng.uniform(0.50, 0.80)
        icr = rng.uniform(1.2, 3.5)
    elif segment == "project_finance":
        total_assets = rng.uniform(300, 8_000)
        leverage = rng.uniform(0.55, 0.85)
        icr = rng.uniform(1.2, 2.8)
    else:  # structured_finance
        total_assets = rng.uniform(200, 10_000)
        if rating_quality <= 3:
            leverage = rng.uniform(0.10, 0.40)
            icr = rng.uniform(3.0, 10.0)
        else:
            leverage = rng.uniform(0.40, 0.75)
            icr = rng.uniform(1.5, 4.0)

    # Distressed names (CCC): force poor ratios
    if rating == "CCC":
        leverage = rng.uniform(0.70, 0.95)
        icr = rng.uniform(0.5, 1.2)

    total_debt = total_assets * leverage
    ebitda_margin = rng.uniform(0.08, 0.25)
    annual_revenue = total_assets * rng.uniform(0.4, 1.2)
    ebitda = annual_revenue * ebitda_margin
    if ebitda <= 0:
        ebitda = total_assets * 0.02

    interest_expense = max(ebitda / icr, total_debt * 0.01)
    debt_to_ebitda = total_debt / max(ebitda, 1.0)

    current_ratio = rng.uniform(0.8, 2.5) if rating != "CCC" else rng.uniform(0.4, 0.9)
    current_liabilities = total_assets * rng.uniform(0.08, 0.25)
    current_assets = current_liabilities * current_ratio

    return {
        "annual_revenue": round(annual_revenue, 2),
        "total_assets": round(total_assets, 2),
        "total_debt": round(total_debt, 2),
        "ebitda": round(ebitda, 2),
        "interest_expense": round(interest_expense, 2),
        "current_assets": round(current_assets, 2),
        "current_liabilities": round(current_liabilities, 2),
        "leverage_ratio": round(leverage, 6),
        "interest_coverage": round(ebitda / interest_expense, 6),
        "current_ratio": round(current_ratio, 6),
        "debt_to_ebitda": round(debt_to_ebitda, 6),
    }


def generate_obligors(rng: np.random.Generator) -> pd.DataFrame:
    """Generate the full obligor table."""
    n = config.N_OBLIGORS
    segments = _assign_segments(n, rng)

    countries_list = list(config.COUNTRIES.keys())
    countries_probs = list(config.COUNTRIES.values())
    sectors = config.SECTORS

    used_names: set = set()
    rows = []

    for i in range(n):
        seg = segments[i]
        rating = _assign_ratings(seg, rng)
        fins = _generate_financials(seg, rating, rng)

        rows.append({
            "obligor_id": f"OBL-{i+1:04d}",
            "obligor_name": _generate_name(rng, used_names),
            "segment": seg,
            "sector": rng.choice(sectors),
            "country": rng.choice(countries_list, p=countries_probs),
            "internal_rating": rating,
            **fins,
        })

    df = pd.DataFrame(rows)
    logger.info("Generated %d obligors across %d segments", len(df), df["segment"].nunique())
    return df


# ── Facility generation ────────────────────────────────────────────────────

def _facility_type_for_segment(segment: str, rng: np.random.Generator) -> str:
    """Assign a realistic facility type based on segment."""
    if segment == "large_corporate":
        return rng.choice(
            ["term_loan", "revolver", "bond", "guarantee"],
            p=[0.35, 0.30, 0.25, 0.10],
        )
    elif segment == "leveraged_finance":
        return rng.choice(
            ["term_loan", "revolver", "bond"],
            p=[0.50, 0.30, 0.20],
        )
    elif segment == "project_finance":
        return rng.choice(
            ["term_loan", "guarantee", "revolver"],
            p=[0.60, 0.25, 0.15],
        )
    else:
        return rng.choice(
            ["structured_note", "bond", "term_loan", "trade_finance"],
            p=[0.40, 0.30, 0.20, 0.10],
        )


def _seniority_for_segment(segment: str, rating: str, rng: np.random.Generator) -> str:
    """Assign seniority consistent with segment and rating."""
    if segment == "leveraged_finance":
        return rng.choice(
            ["senior_secured", "senior_unsecured", "subordinated"],
            p=[0.50, 0.30, 0.20],
        )
    elif segment == "structured_finance":
        quality = config.RATING_NOTCH[rating]
        if quality <= 3:
            return rng.choice(["senior_secured", "senior_unsecured"], p=[0.7, 0.3])
        else:
            return rng.choice(
                ["senior_unsecured", "subordinated"], p=[0.6, 0.4]
            )
    else:
        return rng.choice(
            ["senior_secured", "senior_unsecured", "subordinated"],
            p=[0.60, 0.30, 0.10],
        )


def _collateral_for_seniority(
    seniority: str, sector: str, rng: np.random.Generator
) -> tuple[str, float, float]:
    """Return (collateral_type, collateral_value_ratio, _) based on seniority/sector."""
    if seniority == "subordinated":
        return "unsecured", 0.0, 0.0

    if seniority == "senior_unsecured":
        # Some may have partial collateral
        if rng.random() < 0.3:
            ctype = rng.choice(["financial_assets", "equipment"])
            return ctype, rng.uniform(0.1, 0.4), 0.0
        return "unsecured", 0.0, 0.0

    # senior_secured
    if sector in ("Real Estate", "Infrastructure"):
        return "real_estate", rng.uniform(0.8, 1.5), 0.0
    elif sector in ("Industrials", "Energy"):
        return rng.choice(["equipment", "real_estate"]), rng.uniform(0.5, 1.2), 0.0
    elif sector == "Financial Institutions":
        return "financial_assets", rng.uniform(0.9, 1.8), 0.0
    else:
        return rng.choice(["equipment", "financial_assets", "real_estate"]), rng.uniform(0.5, 1.3), 0.0


def generate_facilities(obligors: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Generate facilities linked to obligors, targeting ~400 total."""
    target = config.TARGET_FACILITIES
    avg_per_obligor = target / len(obligors)

    rows = []
    fac_counter = 0
    today = date(2026, 3, 27)
    governing_laws = {
        "France": "French", "Germany": "German", "United Kingdom": "English",
        "Netherlands": "Dutch", "Spain": "Spanish", "Italy": "Italian", "Other": "English",
    }

    for _, ob in obligors.iterrows():
        # Number of facilities per obligor: 1-3 typically
        n_fac = max(1, int(rng.poisson(avg_per_obligor)))
        n_fac = min(n_fac, 4)

        for _ in range(n_fac):
            fac_counter += 1
            ftype = _facility_type_for_segment(ob["segment"], rng)
            seniority = _seniority_for_segment(ob["segment"], ob["internal_rating"], rng)

            # Commitment sizing: fraction of total debt
            size_frac = rng.uniform(0.1, 0.6)
            commitment = max(round(ob["total_debt"] * size_frac, 2), 1.0)

            # Drawn/undrawn split
            if ftype in ("term_loan", "bond", "structured_note"):
                drawn_pct = rng.uniform(0.85, 1.0)
            elif ftype == "revolver":
                drawn_pct = rng.uniform(0.10, 0.70)
            elif ftype == "guarantee":
                drawn_pct = 0.0  # off-balance sheet
            else:  # trade_finance
                drawn_pct = rng.uniform(0.30, 0.80)

            drawn = round(commitment * drawn_pct, 2)
            undrawn = round(commitment - drawn, 2)

            # Collateral
            coll_type, coll_ratio, _ = _collateral_for_seniority(seniority, ob["sector"], rng)
            coll_value = round(commitment * coll_ratio, 2)

            # Dates
            orig_years_ago = rng.uniform(0.5, 7.0)
            orig_date = today - timedelta(days=int(orig_years_ago * 365))
            mat_years = rng.uniform(1.0, 10.0)
            mat_date = orig_date + timedelta(days=int(mat_years * 365))

            # Interest rate
            base_rate = 0.03 + config.RATING_NOTCH[ob["internal_rating"]] * 0.005
            spread = rng.uniform(-0.005, 0.015)
            rate = round(max(base_rate + spread, 0.01), 6)

            # Cross-border: ~15% have different governing law
            if rng.random() < 0.15:
                gov_law = rng.choice(["English", "French", "German", "New York"])
            else:
                gov_law = governing_laws.get(ob["country"], "English")

            rows.append({
                "facility_id": f"FAC-{fac_counter:05d}",
                "obligor_id": ob["obligor_id"],
                "facility_type": ftype,
                "commitment_amount": commitment,
                "drawn_amount": drawn,
                "undrawn_amount": undrawn,
                "maturity_date": mat_date.isoformat(),
                "seniority": seniority,
                "collateral_type": coll_type,
                "collateral_value": coll_value,
                "interest_rate": rate,
                "origination_date": orig_date.isoformat(),
                "governing_law": gov_law,
            })

    df = pd.DataFrame(rows)
    logger.info("Generated %d facilities for %d obligors", len(df), len(obligors))
    return df


# ── Database loading ───────────────────────────────────────────────────────

def load_to_database(
    obligors: pd.DataFrame, facilities: pd.DataFrame, db_path: Path
) -> None:
    """Load obligor and facility data into SQLite database."""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS facilities")
    cursor.execute("DROP TABLE IF EXISTS obligors")

    # Create schema
    cursor.executescript(schema_sql)

    # Insert obligors
    obligors.to_sql("obligors", conn, if_exists="append", index=False)

    # Insert facilities
    facilities.to_sql("facilities", conn, if_exists="append", index=False)

    conn.commit()

    # Verify
    ob_count = cursor.execute("SELECT COUNT(*) FROM obligors").fetchone()[0]
    fac_count = cursor.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
    logger.info("Database loaded: %d obligors, %d facilities", ob_count, fac_count)

    conn.close()


# ── Main entry point ───────────────────────────────────────────────────────

def generate(seed: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate portfolio data and load into database. Returns (obligors, facilities)."""
    seed = seed or config.RANDOM_SEED
    rng = np.random.default_rng(seed)

    logger.info("Generating synthetic portfolio (seed=%d)", seed)
    obligors = generate_obligors(rng)
    facilities = generate_facilities(obligors, rng)

    # Ensure output directory exists
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    load_to_database(obligors, facilities, config.DB_PATH)

    return obligors, facilities


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
    )
    generate()
