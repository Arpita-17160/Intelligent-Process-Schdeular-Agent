"""
test_algorithms.py
-------------------
Basic unit tests for the scheduling algorithms.

Run with:  pytest
(from the project root, with the venv activated)
"""

import sys
import os

# Make sure "src" is importable when running pytest from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.process import Process
from src.algorithms.fcfs import fcfs
from src.algorithms.sjf import sjf


def make_sample_processes():
    return [
        Process("P1", arrival_time=0, burst_time=5),
        Process("P2", arrival_time=1, burst_time=3),
        Process("P3", arrival_time=2, burst_time=8),
        Process("P4", arrival_time=3, burst_time=6),
    ]


def test_fcfs_runs_in_arrival_order():
    processes = make_sample_processes()
    result, gantt = fcfs(processes)

    execution_order = [pid for pid, start, end in gantt]
    assert execution_order == ["P1", "P2", "P3", "P4"]

    p1 = next(p for p in result if p.pid == "P1")
    assert p1.start_time == 0
    assert p1.completion_time == 5
    assert p1.waiting_time == 0


def test_sjf_picks_shortest_job_among_arrived():
    processes = make_sample_processes()
    result, gantt = sjf(processes)

    assert gantt[0][0] == "P1"
    assert gantt[1][0] == "P2"


def test_all_processes_complete_and_waiting_time_non_negative():
    processes = make_sample_processes()
    for algo in (fcfs, sjf):
        result, gantt = algo(processes)
        assert len(result) == len(processes)
        for p in result:
            assert p.waiting_time >= 0
            assert p.completion_time > p.arrival_time


def test_sjf_gives_lower_or_equal_avg_waiting_time_than_fcfs():
    from src.metrics import summarize

    processes = make_sample_processes()
    fcfs_result, _ = fcfs(processes)
    sjf_result, _ = sjf(processes)

    fcfs_avg = summarize(fcfs_result)["avg_waiting_time"]
    sjf_avg = summarize(sjf_result)["avg_waiting_time"]

    assert sjf_avg <= fcfs_avg