"""
io_utils.py
-----------
Handles reading a workload of processes from a CSV file, and writing
scheduling results back out to CSV.

Why CSV: it's the simplest, most universal format for tabular data -
readable in Excel, Google Sheets, pandas, or any text editor. This lets
you (or anyone else) define a workload without touching Python code.
"""

import csv
from src.process import Process


def load_workload_from_csv(filepath):
    """
    Reads a CSV file with columns: pid, arrival_time, burst_time, priority
    Returns a list of Process objects.
    """
    processes = []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            processes.append(Process(
                pid=row["pid"],
                arrival_time=int(row["arrival_time"]),
                burst_time=int(row["burst_time"]),
                priority=int(row.get("priority", 0) or 0)
            ))
    return processes


def save_results_to_csv(processes, filepath, algorithm_name=""):
    """
    Writes scheduled process results (with computed metrics) to a CSV
    file - useful for keeping a record of a run, or analyzing results
    later in Excel/pandas.
    """
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "algorithm", "pid", "arrival_time", "burst_time", "priority",
            "start_time", "completion_time", "waiting_time",
            "turnaround_time", "response_time"
        ])
        for p in sorted(processes, key=lambda x: x.pid):
            writer.writerow([
                algorithm_name, p.pid, p.arrival_time, p.burst_time, p.priority,
                p.start_time, p.completion_time, p.waiting_time,
                p.turnaround_time, p.response_time
            ])