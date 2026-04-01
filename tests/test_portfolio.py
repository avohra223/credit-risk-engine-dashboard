"""Tests for portfolio analytics calculations."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.pd_model import PDModel
from models.lgd_model import LGDModel
from models.ead_model import EADModel
from portfolio.expected_loss import compute_expected_loss
from portfolio.credit_var import run_monte_carlo
from portfolio.concentration import herfindahl_index
from portfolio.rwa import compute_rwa
from models.validation import el_identity_check
import pandas as pd


@pytest.fixture(scope="module")
def el_df():
    pd_results = PDModel().train()
    lgd_results = LGDModel().estimate()
    ead_results = EADModel().estimate()
    return compute_expected_loss(pd_results, lgd_results, ead_results)


def test_el_identity(el_df):
    """EL must equal PD * LGD * EAD for every facility."""
    result = el_identity_check(
        el_df["pd_score"].values,
        el_df["lgd"].values,
        el_df["ead"].values,
        el_df["el"].values,
    )
    assert result["passes"], f"EL identity failed: max diff = {result['max_absolute_difference']}"


def test_el_positive(el_df):
    """All EL values should be non-negative."""
    assert (el_df["el"] >= 0).all()


def test_var_exceeds_el(el_df):
    """VaR should exceed expected loss."""
    var_results = run_monte_carlo(el_df, n_simulations=2000)
    assert var_results["var_95"] > var_results["expected_loss_analytical"]


def test_rwa_positive(el_df):
    rwa_df = compute_rwa(el_df)
    assert (rwa_df["rwa"] >= 0).all()


def test_herfindahl_index():
    """HHI of equal exposures should equal 1/n."""
    exposures = pd.Series([100, 100, 100, 100])
    hhi = herfindahl_index(exposures)
    assert abs(hhi - 0.25) < 0.001


def test_herfindahl_concentrated():
    """HHI of a single exposure should be 1.0."""
    exposures = pd.Series([1000])
    hhi = herfindahl_index(exposures)
    assert abs(hhi - 1.0) < 0.001
