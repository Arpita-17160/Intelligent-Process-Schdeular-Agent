"""
test_deadlock.py
----------------
Tests for the Banker's Algorithm and deadlock detection, using the
classic textbook example (5 processes, 3 resource types) so every
expected answer can be checked by hand.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.deadlock import calculate_need, is_safe, request_resources, detect_deadlock

AVAILABLE = [3, 3, 2]
MAX_DEMAND = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
ALLOCATION = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]


# ---------- need & safety ----------

def test_need_is_max_minus_allocation():
    assert calculate_need(MAX_DEMAND, ALLOCATION) == [
        [7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1],
    ]


def test_textbook_state_is_safe_with_known_sequence():
    safe, sequence = is_safe(AVAILABLE, MAX_DEMAND, ALLOCATION)
    assert safe is True
    assert sequence == ["P1", "P3", "P4", "P0", "P2"]


def test_state_with_no_free_resources_is_unsafe():
    # Nothing is free and every process still needs something -> nobody can finish
    safe, sequence = is_safe([0, 0, 0], MAX_DEMAND, ALLOCATION)
    assert safe is False
    assert sequence == []


def test_safe_sequence_includes_every_process_exactly_once():
    safe, sequence = is_safe(AVAILABLE, MAX_DEMAND, ALLOCATION)
    assert sorted(sequence) == ["P0", "P1", "P2", "P3", "P4"]


# ---------- banker's request algorithm ----------

def test_safe_request_is_granted_and_state_updates():
    result = request_resources(1, [1, 0, 2], AVAILABLE, MAX_DEMAND, ALLOCATION)

    assert result["granted"] is True
    assert result["available"] == [2, 3, 0]            # 3,3,2 minus 1,0,2
    assert result["allocation"][1] == [3, 0, 2]        # P1 now holds 2,0,0 + 1,0,2
    assert result["safe_sequence"] == ["P1", "P3", "P4", "P0", "P2"]


def test_request_larger_than_available_must_wait():
    # After P1's request is granted only (2, 3, 0) is free, so P4 asking
    # for (3, 3, 0) wants more A than exists right now.
    after_p1 = request_resources(1, [1, 0, 2], AVAILABLE, MAX_DEMAND, ALLOCATION)
    result = request_resources(4, [3, 3, 0], after_p1["available"], MAX_DEMAND, after_p1["allocation"])

    assert result["granted"] is False
    assert "not enough resources" in result["reason"]


def test_request_that_fits_but_is_unsafe_gives_the_unsafe_reason():
    # In the STARTING state (3, 3, 0) does fit, but granting it is unsafe.
    result = request_resources(4, [3, 3, 0], AVAILABLE, MAX_DEMAND, ALLOCATION)

    assert result["granted"] is False
    assert "UNSAFE" in result["reason"]


def test_request_that_would_make_system_unsafe_is_refused():
    # First grant P1's request, then P0 asks for (0,2,0): fits in what is free,
    # but granting it would leave no safe order -> must be refused.
    after_p1 = request_resources(1, [1, 0, 2], AVAILABLE, MAX_DEMAND, ALLOCATION)
    result = request_resources(0, [0, 2, 0], after_p1["available"], MAX_DEMAND, after_p1["allocation"])

    assert result["granted"] is False
    assert "UNSAFE" in result["reason"]


def test_request_above_declared_maximum_is_an_error():
    # P1's need is [1, 2, 2]; asking for 5 units of A breaks its own declared maximum
    with pytest.raises(ValueError):
        request_resources(1, [5, 0, 0], AVAILABLE, MAX_DEMAND, ALLOCATION)


def test_refused_request_leaves_the_system_unchanged():
    result = request_resources(4, [3, 3, 0], AVAILABLE, MAX_DEMAND, ALLOCATION)

    assert result["available"] == AVAILABLE
    assert result["allocation"] == ALLOCATION


def test_inputs_are_never_modified():
    available = list(AVAILABLE)
    allocation = [list(row) for row in ALLOCATION]
    request_resources(1, [1, 0, 2], available, MAX_DEMAND, allocation)

    assert available == AVAILABLE
    assert allocation == ALLOCATION


# ---------- detection ----------

def test_circular_wait_is_detected():
    # P0 holds R0 and wants R1; P1 holds R1 and wants R0; nothing is free
    deadlocked = detect_deadlock([0, 0], [[1, 0], [0, 1]], [[0, 1], [1, 0]])
    assert deadlocked == ["P0", "P1"]


def test_no_deadlock_when_a_waiting_process_can_proceed():
    # One spare R1 lets P0 finish, which frees R0 for P1
    deadlocked = detect_deadlock([0, 1], [[1, 0], [0, 1]], [[0, 1], [1, 0]])
    assert deadlocked == []


def test_process_holding_nothing_is_never_deadlocked():
    # P2 holds nothing and wants R0 - it is waiting, but cannot be part of a deadlock cycle
    allocation = [[1, 0], [0, 1], [0, 0]]
    request = [[0, 1], [1, 0], [1, 0]]
    deadlocked = detect_deadlock([0, 0], allocation, request)
    assert deadlocked == ["P0", "P1"]


# ---------- input validation ----------

def test_mismatched_table_sizes_are_rejected():
    with pytest.raises(ValueError):
        is_safe([3, 3], MAX_DEMAND, ALLOCATION)      # 2 resources vs 3 columns


def test_process_holding_more_than_its_maximum_is_rejected():
    with pytest.raises(ValueError):
        calculate_need([[1, 1]], [[2, 0]])