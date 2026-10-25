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
from src.analytics import compare_algorithms, print_comparison_table
from src.agent import analyze_workload
from src.ml_agent import recommend_algorithm_ml
from ml.generate_training_data import ALGORITHMS, GOALS, score
from src.algorithms.mlfq import mlfq
from src.predictor import assign_predictions, mean_absolute_error

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
    assign_predictions(processes)
    print("Workload:")
    for p in processes:
        print(f"  {p}")
    print("\nBurst-time predictions (exponential averaging):")
    for p in processes:
        print(f"  {p.pid}: actual={p.burst_time}  predicted={p.predicted_burst}")
    print(f"  Average prediction error: {mean_absolute_error(processes)}")

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
    results["MLFQ"] = run_algorithm("MLFQ (Multilevel Feedback Queue)", mlfq, processes)

    algorithms = {
        "FCFS": fcfs,
        "SJF": sjf,
        "SJF (predicted)": lambda p: sjf(p, use_prediction=True),
        "Round Robin": lambda p: round_robin(p, time_quantum=2),
        "Priority (aging)": priority_scheduling,
        "MLFQ": mlfq,
    }
    
    comparison = compare_algorithms(processes, algorithms)
    print_comparison_table(comparison)

    print(f"\n{'=' * 70}\nML Agent Recommendations (one per goal)\n{'=' * 70}")
    print(f"Workload characteristics: {analyze_workload(processes)}")

    # Run the five competing algorithms once; the GOAL decides how we score them
    scheduled = {name: fn(processes)[0] for name, fn in ALGORITHMS.items()}

    for goal in GOALS:
        pick, path, _ = recommend_algorithm_ml(processes, goal)
        scores = {name: score(goal, res) for name, res in scheduled.items()}
        best = min(scores.values())
        verdict = "✓ optimal" if scores[pick] - best < 1e-9 else f"✗ best possible was {best}"

        print(f"\nGoal: {goal}")
        print(f"  Agent picks: {pick} (score {scores[pick]})  {verdict}")
        print("  Scores (lower is better): " + " | ".join(f"{n} {s}" for n, s in scores.items()))
        print(f"  Why: {path}")


if __name__ == "__main__":
    main()