"""
test_ml.py
----------
Tests for the goal scoring, the training-data generator and the ML agent.

These tests check OUR logic (scoring maths, feature building, input
validation) rather than the exact answers of the trained model, so they
keep passing even if you retrain the model.
"""

import sys
import os
import random

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.process import Process
from src.ml_agent import recommend_algorithm_ml, _feature_row, GOAL_LOOKUP
from ml.generate_training_data import (
    ALGORITHMS, GOALS, FEATURE_NAMES,
    generate_workload, priority_weighted_wait, build_dataset,
)


def sample_processes():
    return [
        Process("P1", 0, 5, 2),
        Process("P2", 1, 3, 1),
        Process("P3", 2, 8, 3),
        Process("P4", 3, 6, 2),
    ]


# ---------- goal scoring ----------

def test_priority_weighted_wait_gives_important_processes_more_weight():
    # priority 0 = most important -> weight 2; priority 1 -> weight 1
    # (2*10 + 1*2) / (2 + 1) = 7.33  (NOT the plain average of 6)
    important = Process("A", 0, 5, priority=0)
    important.waiting_time = 10
    normal = Process("B", 0, 5, priority=1)
    normal.waiting_time = 2

    assert priority_weighted_wait([important, normal]) == pytest.approx(22 / 3)


def test_priority_weighted_wait_equals_plain_average_when_priorities_equal():
    a = Process("A", 0, 5, priority=1)
    a.waiting_time = 10
    b = Process("B", 0, 5, priority=1)
    b.waiting_time = 2

    assert priority_weighted_wait([a, b]) == pytest.approx(6.0)


# ---------- training-data generator ----------

def test_generate_workload_is_reproducible_with_same_seed():
    first = generate_workload(random.Random(1))
    second = generate_workload(random.Random(1))
    assert [repr(p) for p in first] == [repr(p) for p in second]


def test_generated_workloads_are_valid():
    rng = random.Random(3)
    for _ in range(50):
        for p in generate_workload(rng):
            assert p.burst_time >= 1
            assert p.arrival_time >= 0
            assert p.priority >= 0


def test_build_dataset_has_one_row_per_workload_per_goal():
    rows = build_dataset(num_workloads=5, seed=1)

    assert len(rows) == 5 * len(GOALS)
    for row in rows:
        assert row["best_algorithm"] in ALGORITHMS
        assert row["goal"] in GOALS
        for name in FEATURE_NAMES:
            assert name in row


# ---------- ML agent ----------

def test_feature_row_has_exactly_one_goal_column_switched_on():
    stats = {name: 1 for name in FEATURE_NAMES}
    columns = FEATURE_NAMES + [f"goal_{g}" for g in GOALS]

    row = _feature_row(stats, "response", columns)

    assert list(row.columns) == columns            # same order as training
    assert row["goal_response"].iloc[0] == 1
    assert row["goal_waiting"].iloc[0] == 0
    assert row["goal_priority"].iloc[0] == 0


def test_agent_recommends_a_known_algorithm_for_every_goal():
    for goal in GOALS:
        algorithm, explanation, stats = recommend_algorithm_ml(sample_processes(), goal)
        assert algorithm in ALGORITHMS
        assert isinstance(explanation, str) and explanation != ""
        assert stats["num_processes"] == 4


def test_agent_is_deterministic():
    first = recommend_algorithm_ml(sample_processes(), "response")
    second = recommend_algorithm_ml(sample_processes(), "response")
    assert first == second


def test_agent_rejects_unknown_goal():
    with pytest.raises(ValueError):
        recommend_algorithm_ml(sample_processes(), "waitting")   # typo on purpose


def test_goal_lookup_covers_every_goal_with_a_known_algorithm():
    assert set(GOAL_LOOKUP) == set(GOALS)
    for algorithm in GOAL_LOOKUP.values():
        assert algorithm in ALGORITHMS