"""
mlfq.py
-------
Multilevel Feedback Queue (MLFQ) Scheduling - Preemptive.

Multiple queues exist, each with its own priority level and time
quantum. A new process always enters the TOP queue (highest priority,
shortest quantum). If it finishes within its quantum, it's done. If
not, it gets DEMOTED to the next queue down (lower priority, longer
quantum).

Why this matters: unlike SJF or Priority scheduling, MLFQ does NOT
need to know anything about a process in advance. Short jobs naturally
finish quickly in the top queue. Long, CPU-heavy jobs sink to lower
queues automatically, based on their observed behavior - this is much
closer to how real operating systems actually schedule processes.
"""

from src.process import clone_processes
from src.metrics import compute_metrics


def mlfq(processes, quantums=(2, 4, 8)):
    """
    processes: list of Process objects (will NOT be mutated - we clone)
    quantums: time quantum for each queue level, top queue first.
              The LAST queue is treated as FCFS (no further demotion).
    Returns: (scheduled_processes, gantt_chart)
    """
    procs = clone_processes(processes)
    n = len(procs)
    remaining = sorted(procs, key=lambda p: p.arrival_time)

    num_levels = len(quantums)
    queues = [[] for _ in range(num_levels)]   # queues[0] = top/highest priority
    completed = []
    gantt_chart = []
    current_time = 0

    def admit_arrivals(up_to_time):
        while remaining and remaining[0].arrival_time <= up_to_time:
            p = remaining.pop(0)
            queues[0].append(p)   # every new process starts at the TOP queue

    admit_arrivals(current_time)

    while len(completed) < n:
        # Find the highest-priority non-empty queue
        level = next((i for i, q in enumerate(queues) if q), None)

        if level is None:
            # Everything is empty - jump forward to next arrival
            current_time = remaining[0].arrival_time
            admit_arrivals(current_time)
            continue

        p = queues[level].pop(0)
        if p.start_time is None:
            p.start_time = current_time

        quantum = quantums[level]
        run_time = min(quantum, p.remaining_time)

        gantt_chart.append((f"{p.pid}(Q{level})", current_time, current_time + run_time))
        current_time += run_time
        p.remaining_time -= run_time

        admit_arrivals(current_time)

        if p.remaining_time > 0:
            # Didn't finish - demote to the next queue down (unless already at the bottom)
            next_level = min(level + 1, num_levels - 1)
            queues[next_level].append(p)
        else:
            p.completion_time = current_time
            completed.append(p)

    compute_metrics(completed)
    return completed, gantt_chart
