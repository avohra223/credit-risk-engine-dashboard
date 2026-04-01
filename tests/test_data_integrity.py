"""Tests for data integrity of the generated portfolio."""
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


@pytest.fixture(scope="module")
def db():
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_obligor_count(db):
    count = db.execute("SELECT COUNT(*) FROM obligors").fetchone()[0]
    assert count == config.N_OBLIGORS


def test_facility_count_range(db):
    count = db.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
    assert 350 <= count <= 500, f"Expected ~400 facilities, got {count}"


def test_no_orphan_facilities(db):
    orphans = db.execute(
        "SELECT COUNT(*) FROM facilities f "
        "LEFT JOIN obligors o ON f.obligor_id = o.obligor_id "
        "WHERE o.obligor_id IS NULL"
    ).fetchone()[0]
    assert orphans == 0


def test_drawn_leq_commitment(db):
    violations = db.execute(
        "SELECT COUNT(*) FROM facilities WHERE drawn_amount > commitment_amount * 1.01"
    ).fetchone()[0]
    assert violations == 0


def test_positive_assets(db):
    bad = db.execute("SELECT COUNT(*) FROM obligors WHERE total_assets <= 0").fetchone()[0]
    assert bad == 0


def test_valid_ratings(db):
    valid = set(config.RATING_GRADES)
    rows = db.execute("SELECT DISTINCT internal_rating FROM obligors").fetchall()
    for row in rows:
        assert row[0] in valid, f"Invalid rating: {row[0]}"


def test_valid_sectors(db):
    valid = set(config.SECTORS)
    rows = db.execute("SELECT DISTINCT sector FROM obligors").fetchall()
    for row in rows:
        assert row[0] in valid, f"Invalid sector: {row[0]}"


def test_leverage_ratio_computed_correctly(db):
    """Spot-check that leverage_ratio = total_debt / total_assets."""
    rows = db.execute(
        "SELECT total_debt, total_assets, leverage_ratio FROM obligors LIMIT 20"
    ).fetchall()
    for row in rows:
        expected = row[0] / row[1]
        assert abs(row[2] - expected) < 0.01, f"Leverage mismatch: {row[2]} vs {expected}"
