"""
metrics.py
----------
Calculates the standard OS scheduling performance metrics.

- Turnaround Time = Completion Time - Arrival Time
- Waiting Time = Turnaround Time - Burst Time
- Response Time = Start Time - Arrival Time

An algorithm is "better" if it produces LOWER average waiting time and
LOWER average turnaround time for a given workload.
"""


def compute_metrics(processes):
    """
    Given a list of Process objects that have already been scheduled
    (start_time and completion_time filled in), compute waiting_time,
    turnaround_time and response_time for each process.
    """
    for p in processes:
        p.turnaround_time = p.completion_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        p.response_time = p.start_time - p.arrival_time
    return processes


def summarize(processes):
    """
    Returns average metrics across all processes - used to compare
    algorithms against each other.
    """
    n = len(processes)
    avg_waiting = sum(p.waiting_time for p in processes) / n
    avg_turnaround = sum(p.turnaround_time for p in processes) / n
    avg_response = sum(p.response_time for p in processes) / n

    return {
        "avg_waiting_time": round(avg_waiting, 2),
        "avg_turnaround_time": round(avg_turnaround, 2),
        "avg_response_time": round(avg_response, 2),
    }


def print_process_table(processes, algorithm_name=""):
    """Pretty-prints a per-process breakdown to the terminal."""
    if algorithm_name:
        print(f"\n--- {algorithm_name} : Per-Process Metrics ---")
    header = f"{'PID':<6}{'Arrival':<10}{'Burst':<8}{'Start':<8}{'Complete':<10}{'Waiting':<10}{'Turnaround':<12}{'Response':<10}"
    print(header)
    print("-" * len(header))
    for p in sorted(processes, key=lambda x: x.pid):
        print(f"{p.pid:<6}{p.arrival_time:<10}{p.burst_time:<8}{p.start_time:<8}"
              f"{p.completion_time:<10}{p.waiting_time:<10}{p.turnaround_time:<12}{p.response_time:<10}")