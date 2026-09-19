"""
sjf.py
------
Shortest Job First (SJF) Scheduling - Non-Preemptive version.

Among all processes that have ARRIVED and are waiting, always run the
one with the smallest burst time next. Once started, runs to completion.

Weakness: a long process can "starve" if short processes keep arriving
and cutting in front of it.
"""

from src.process import clone_processes
from src.metrics import compute_metrics


def sjf(processes):
    """
    processes: list of Process objects (will NOT be mutated - we clone)
    Returns: (scheduled_processes, gantt_chart)
    """
    procs = clone_processes(processes)
    n = len(procs)
    completed = []
    ready_queue = []
    remaining = sorted(procs, key=lambda p: p.arrival_time)

    current_time = 0
    gantt_chart = []

    while len(completed) < n:
        # Move any processes that have now arrived into the ready queue
        while remaining and remaining[0].arrival_time <= current_time:
            ready_queue.append(remaining.pop(0))

        if not ready_queue:
            # CPU is idle - jump forward to the next process's arrival
            current_time = remaining[0].arrival_time
            continue

        # Pick the process with the smallest burst time from what's ready
        ready_queue.sort(key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        p = ready_queue.pop(0)

        p.start_time = current_time
        current_time += p.burst_time
        p.completion_time = current_time

        gantt_chart.append((p.pid, p.start_time, p.completion_time))
        completed.append(p)

    compute_metrics(completed)
    return completed, gantt_chart