"""
priority_scheduling.py
-----------------------
Priority Scheduling with Aging - Non-Preemptive.

Among all processes that have ARRIVED and are waiting, always run the
one with the highest priority (lower number = higher priority in our
convention) next. Once started, runs to completion.

Problem: STARVATION - a low-priority process can wait forever if
higher-priority processes keep arriving ahead of it.

Fix: AGING - the longer a process waits, the more we artificially
reduce its priority number (i.e. boost its urgency), so eventually
every process is guaranteed to run.
"""

from src.process import clone_processes
from src.metrics import compute_metrics


def priority_scheduling(processes, aging_interval=4, aging_boost=1):
    """
    processes: list of Process objects (will NOT be mutated - we clone)
    aging_interval: every X time units a process waits, boost its priority
    aging_boost: how much to reduce the priority number (increase urgency)
                 each time aging kicks in
    Returns: (scheduled_processes, gantt_chart)
    """
    procs = clone_processes(processes)
    n = len(procs)
    completed = []
    ready_queue = []
    remaining = sorted(procs, key=lambda p: p.arrival_time)

    # Track each waiting process's "effective priority" separately from
    # its original priority, and when it last got aged.
    effective_priority = {}
    last_aged_time = {}

    current_time = 0
    gantt_chart = []

    while len(completed) < n:
        while remaining and remaining[0].arrival_time <= current_time:
            p = remaining.pop(0)
            ready_queue.append(p)
            effective_priority[p.pid] = p.priority
            last_aged_time[p.pid] = current_time

        if not ready_queue:
            current_time = remaining[0].arrival_time
            continue

        # Apply aging: for every process waiting, check how long it's
        # been sitting in the queue and boost its urgency accordingly.
        for p in ready_queue:
            waited = current_time - last_aged_time[p.pid]
            boosts = waited // aging_interval
            if boosts > 0:
                effective_priority[p.pid] -= boosts * aging_boost
                last_aged_time[p.pid] = current_time

        # Pick the process with the best (lowest) effective priority
        ready_queue.sort(key=lambda p: (effective_priority[p.pid], p.arrival_time, p.pid))
        p = ready_queue.pop(0)

        p.start_time = current_time
        current_time += p.burst_time
        p.completion_time = current_time

        gantt_chart.append((p.pid, p.start_time, p.completion_time))
        completed.append(p)

    compute_metrics(completed)
    return completed, gantt_chart