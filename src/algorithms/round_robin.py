"""
round_robin.py
--------------
Round Robin (RR) Scheduling - Preemptive.

Each process gets a fixed slice of CPU time (the "time quantum"). If it
doesn't finish within that slice, it's paused and sent to the back of
the ready queue, and the next process gets a turn. This repeats until
every process is done.

Preemptive: unlike FCFS/SJF, a running process CAN be interrupted mid-way.

Tradeoff: too large a quantum behaves like FCFS. Too small a quantum
wastes time on context-switching overhead instead of real work.
"""

from src.process import clone_processes
from src.metrics import compute_metrics


def round_robin(processes, time_quantum=2):
    """
    processes: list of Process objects (will NOT be mutated - we clone)
    time_quantum: max CPU time given to a process per turn
    Returns: (scheduled_processes, gantt_chart)
    """
    procs = clone_processes(processes)
    n = len(procs)
    remaining = sorted(procs, key=lambda p: p.arrival_time)
    ready_queue = []
    completed = []
    gantt_chart = []
    current_time = 0

    # Start the queue with whichever process(es) have arrived at time 0
    while remaining and remaining[0].arrival_time <= current_time:
        ready_queue.append(remaining.pop(0))

    while len(completed) < n:
        if not ready_queue:
            # CPU idle - jump forward to next arrival
            current_time = remaining[0].arrival_time
            while remaining and remaining[0].arrival_time <= current_time:
                ready_queue.append(remaining.pop(0))
            continue

        p = ready_queue.pop(0)

        # First time this process ever gets the CPU
        if p.start_time is None:
            p.start_time = current_time

        # Run it for min(time_quantum, what it still needs)
        run_time = min(time_quantum, p.remaining_time)
        gantt_chart.append((p.pid, current_time, current_time + run_time))
        current_time += run_time
        p.remaining_time -= run_time

        # Any new processes that arrived DURING this slice join the queue
        while remaining and remaining[0].arrival_time <= current_time:
            ready_queue.append(remaining.pop(0))

        if p.remaining_time > 0:
            # Not done yet - goes to the back of the line
            ready_queue.append(p)
        else:
            # Finished
            p.completion_time = current_time
            completed.append(p)

    compute_metrics(completed)
    return completed, gantt_chart