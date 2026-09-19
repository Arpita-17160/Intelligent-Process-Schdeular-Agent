"""
process.py
-----------
Represents a Process Control Block (PCB).

In a real Operating System, the OS maintains a PCB for every process it
manages. It stores everything the OS needs to know to schedule and run
that process: its identity, how much CPU time it needs, when it arrived,
its priority, and bookkeeping fields the scheduler fills in as it runs.
"""


class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        # --- Fields set when the process is created ---
        self.pid = pid                      # Process ID (e.g. "P1")
        self.arrival_time = arrival_time    # When the process enters the ready queue
        self.burst_time = burst_time        # Total CPU time this process needs
        self.priority = priority            # Lower number = higher priority

        # --- Fields the scheduler fills in during/after simulation ---
        self.remaining_time = burst_time
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None

    def __repr__(self):
        return (f"Process({self.pid}, arrival={self.arrival_time}, "
                f"burst={self.burst_time}, priority={self.priority})")


def clone_processes(processes):
    """
    Returns a fresh copy of a list of Process objects.
    We need this because each algorithm MUTATES process fields
    (completion_time, etc). If we ran FCFS then SJF on the same
    objects, SJF would inherit leftover state from FCFS.
    """
    return [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in processes]