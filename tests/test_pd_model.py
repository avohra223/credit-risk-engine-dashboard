"""Tests for the Probability of Default model."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.pd_model import PDModel


@pytest.fixture(scope="module")
def pd_model():
    model = PDModel()
    model.train()
    return model


def test_auc_above_threshold(pd_model):
    assert pd_model.auc > 0.70, f"AUC too low: {pd_model.auc}"


def test_gini_positive(pd_model):
    assert pd_model.gini > 0, f"Gini should be positive: {pd_model.gini}"


def test_pd_range(pd_model):
    """PD scores should be between 0 and 1."""
    results = pd_model.train()
    assert results["pd_score"].min() >= 0
    assert results["pd_score"].max() <= 1


def test_scorecard_monotonic(pd_model):
    """Average PD should increase across scorecard grades."""
    sc = pd_model.scorecard
    avg_pds = sc["avg_pd"].values
    for i in range(1, len(avg_pds)):
        assert avg_pds[i] >= avg_pds[i - 1] * 0.5, \
            f"Scorecard not monotonic at row {i}: {avg_pds[i]} < {avg_pds[i-1]}"


def test_model_saves_and_loads(pd_model, tmp_path):
    path = tmp_path / "test_pd.pkl"
    pd_model.save(path)
    new_model = PDModel()
    new_model.load(path)
    assert new_model.model is not None
    assert new_model.scaler is not None
