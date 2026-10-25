"""
test_memory.py
--------------
Tests for First Fit, Best Fit and Worst Fit, using the classic textbook
example so every expected answer can be checked by hand.

Memory blocks [100, 500, 200, 300, 600] sit at addresses 0, 100, 600, 800, 1100.
Process requests: P1=212, P2=417, P3=112, P4=426.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.memory import allocate, compare_strategies, STRATEGIES

PARTITIONS = [100, 500, 200, 300, 600]
REQUESTS = [212, 417, 112, 426]


def start_of(result, process):
    return next(p["start"] for p in result["placements"] if p["process"] == process)


# ---------- each strategy picks the hole it should ----------

def test_first_fit_takes_the_first_hole_that_is_big_enough():
    result = allocate(PARTITIONS, REQUESTS, "First Fit")
    assert start_of(result, "P1") == 100     # 100 is too small, 500 is the first that fits


def test_best_fit_takes_the_smallest_hole_that_is_big_enough():
    result = allocate(PARTITIONS, REQUESTS, "Best Fit")
    assert start_of(result, "P1") == 800     # the 300 hole is the tightest fit for 212


def test_worst_fit_takes_the_largest_hole():
    result = allocate(PARTITIONS, REQUESTS, "Worst Fit")
    assert start_of(result, "P1") == 1100    # the 600 hole is the largest


# ---------- the textbook outcome ----------

def test_only_best_fit_places_all_four_processes():
    results = compare_strategies(PARTITIONS, REQUESTS)

    assert results["Best Fit"]["stats"]["placed"] == 4
    assert results["First Fit"]["stats"]["placed"] == 3
    assert results["Worst Fit"]["stats"]["placed"] == 3


def test_failure_with_enough_total_memory_is_reported_as_external_fragmentation():
    result = allocate(PARTITIONS, REQUESTS, "First Fit")
    p4 = result["placements"][3]

    assert p4["placed"] is False
    assert "external fragmentation" in p4["reason"]
    assert result["stats"]["total_free"] >= p4["size"]    # the memory existed, just in pieces


def test_failure_without_enough_total_memory_says_so():
    result = allocate([100], [150], "First Fit")
    assert result["placements"][0]["placed"] is False
    assert "not enough memory" in result["placements"][0]["reason"]


# ---------- splitting and bookkeeping ----------

def test_leftover_of_a_split_hole_stays_free():
    result = allocate(PARTITIONS, [212], "First Fit")
    leftover = next(s for s in result["memory_map"] if s["start"] == 312)

    assert leftover["owner"] is None
    assert leftover["size"] == 288            # 500 - 212


def test_memory_map_has_no_gaps_or_overlaps_and_adds_up():
    for strategy in STRATEGIES:
        result = allocate(PARTITIONS, REQUESTS, strategy)
        position = 0
        for segment in result["memory_map"]:
            assert segment["start"] == position       # next segment starts where the last ended
            position += segment["size"]
        assert position == sum(PARTITIONS)            # nothing created or lost


def test_used_plus_free_equals_total_memory():
    for strategy in STRATEGIES:
        stats = allocate(PARTITIONS, REQUESTS, strategy)["stats"]
        assert stats["used"] + stats["total_free"] == stats["total_memory"]


def test_a_process_exactly_the_size_of_a_hole_leaves_no_leftover():
    result = allocate([100, 200], [100], "First Fit")
    assert len(result["memory_map"]) == 2     # no new hole was created


# ---------- fragmentation figure ----------

def test_fragmentation_is_zero_when_all_free_memory_is_one_piece():
    assert allocate([300], [], "First Fit")["stats"]["external_fragmentation"] == 0.0


def test_fragmentation_when_free_memory_is_split_in_two_holes():
    # holes 100 and 200: largest is 200 of 300 free -> (1 - 200/300) = 33.3%
    assert allocate([100, 200], [], "First Fit")["stats"]["external_fragmentation"] == 33.3


# ---------- input validation ----------

def test_unknown_strategy_is_rejected():
    with pytest.raises(ValueError):
        allocate(PARTITIONS, REQUESTS, "Lucky Fit")


def test_non_positive_sizes_are_rejected():
    with pytest.raises(ValueError):
        allocate([100, 0], [10], "First Fit")
    with pytest.raises(ValueError):
        allocate([100], [-5], "First Fit")


def test_inputs_are_never_modified():
    partitions, requests = list(PARTITIONS), list(REQUESTS)
    allocate(partitions, requests, "Best Fit")
    assert partitions == PARTITIONS and requests == REQUESTS