"""
fcfs.py
-------
First Come First Serve (FCFS) Scheduling.

Processes are executed strictly in the order they arrive. Non-preemptive:
once a process starts, it runs to completion before the next one starts.

Weakness (the "Convoy Effect"): if a long process arrives first, every
short process behind it has to wait for the whole long burst to finish.
"""

from src.process import clone_processes
from src.metrics import compute_metrics


def fcfs(processes):
    """
    processes: list of Process objects (will NOT be mutated - we clone)
    Returns: (scheduled_processes, gantt_chart)
        gantt_chart -> list of (pid, start_time, end_time) tuples, in
                       execution order
    """
    procs = clone_processes(processes)

    # Step 1: sort by arrival time (ties broken by pid for determinism)
    procs.sort(key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    gantt_chart = []

    for p in procs:
        # If the CPU is idle waiting for this process to arrive, jump forward
        if current_time < p.arrival_time:
            current_time = p.arrival_time

        p.start_time = current_time
        current_time += p.burst_time
        p.completion_time = current_time

        gantt_chart.append((p.pid, p.start_time, p.completion_time))

    compute_metrics(procs)
    return procs, gantt_chart