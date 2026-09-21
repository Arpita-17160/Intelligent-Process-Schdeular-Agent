"""
main.py
-------
CLI entry point. Right now (Phase 1) it runs FCFS and SJF on a sample
workload and prints the results, including a Gantt chart for each.
"""

from src.process import Process
from src.algorithms.fcfs import fcfs
from src.algorithms.sjf import sjf
from src.metrics import print_process_table, summarize
from src.gantt import render_gantt_chart
from src.algorithms.round_robin import round_robin
from src.algorithms.priority_scheduling import priority_scheduling
from src.io_utils import load_workload_from_csv, save_results_to_csv

def get_sample_workload():
    """A small hardcoded workload to demonstrate the simulator."""
    return [
        Process("P1", arrival_time=0, burst_time=5, priority=2),
        Process("P2", arrival_time=1, burst_time=3, priority=1),
        Process("P3", arrival_time=2, burst_time=8, priority=3),
        Process("P4", arrival_time=3, burst_time=6, priority=2),
    ]


def run_algorithm(name, algo_fn, processes):
    result, gantt = algo_fn(processes)
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    render_gantt_chart(gantt)
    print_process_table(result, algorithm_name=name)
    stats = summarize(result)
    print(f"\nAverages -> Waiting: {stats['avg_waiting_time']}  "
          f"Turnaround: {stats['avg_turnaround_time']}  "
          f"Response: {stats['avg_response_time']}")
    save_results_to_csv(result, f"data/results_{name.split()[0]}.csv", algorithm_name=name)
    return stats


def main():
    processes = load_workload_from_csv("data/sample_workload.csv")
    print("Workload:")
    for p in processes:
        print(f"  {p}")

    results = {}
    results["FCFS"] = run_algorithm("FCFS (First Come First Serve)", fcfs, processes)
    results["SJF"] = run_algorithm("SJF (Shortest Job First)", sjf, processes)
    results["Round Robin"] = run_algorithm(
    "Round Robin (quantum=2)",
    lambda procs: round_robin(procs, time_quantum=2),
    processes
    )
    results["Priority (aging)"] = run_algorithm(
    "Priority Scheduling (with aging)",
    priority_scheduling,
    processes
    )
    print(f"\n{'=' * 60}\nComparison Summary\n{'=' * 60}")
    for algo_name, stats in results.items():
        print(f"{algo_name:<10} avg_waiting={stats['avg_waiting_time']:<8} "
              f"avg_turnaround={stats['avg_turnaround_time']}")


if __name__ == "__main__":
    main()