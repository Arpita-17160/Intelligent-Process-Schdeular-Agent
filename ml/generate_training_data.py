"""
generate_training_data.py
-------------------------
Creates the TRAINING DATA for the machine-learning agent.

Key idea: "best algorithm" depends on the GOAL.
    waiting  -> minimise average waiting time            (batch systems)
    response -> minimise average response time           (interactive systems)
    priority -> minimise priority-weighted waiting time  (important jobs first)

For every random workload and every goal we run all five algorithms,
see which one scores best, and save one row:

    workload shape (features) + goal  ->  winning algorithm (label)

A model can later learn this pattern from hundreds of examples.

Run from the project root with:
    python -m ml.generate_training_data
"""

import csv
import random

from src.process import Process
from src.agent import analyze_workload
from src.metrics import summarize
from src.algorithms.fcfs import fcfs
from src.algorithms.sjf import sjf
from src.algorithms.round_robin import round_robin
from src.algorithms.priority_scheduling import priority_scheduling
from src.algorithms.mlfq import mlfq

# The five competing algorithms (dict order is the final tie-breaker).
ALGORITHMS = {
    "FCFS": fcfs,
    "SJF": sjf,
    "Round Robin": lambda p: round_robin(p, time_quantum=2),
    "Priority (aging)": priority_scheduling,
    "MLFQ": mlfq,
}

GOALS = ["waiting", "response", "priority"]

FEATURE_NAMES = ["num_processes", "avg_burst_time", "burst_variance",
                 "priority_spread", "arrival_spread"]


def generate_workload(rng):
    """
    Builds ONE random workload. The 'style' is picked randomly first, so
    the dataset covers very different situations: tiny vs huge jobs,
    everyone arriving together vs spread out, equal vs very different
    priorities.
    """
    n = rng.randint(4, 10)
    burst_max = rng.choice([4, 8, 15, 30])
    arrival_window = rng.choice([0, 5, 15, 40])   # 0 = all arrive at once
    priority_levels = rng.choice([1, 3, 6])       # 1 = all same priority

    return [
        Process(
            f"P{i + 1}",
            arrival_time=rng.randint(0, arrival_window),
            burst_time=rng.randint(1, burst_max),
            priority=rng.randint(0, priority_levels - 1),
        )
        for i in range(n)
    ]


def priority_weighted_wait(processes):
    """
    Average waiting time where important processes count MORE.
    Lower priority number = more important = bigger weight.
    (If every priority is equal, this is just the normal average.)
    """
    worst = max(p.priority for p in processes)
    weights = [worst - p.priority + 1 for p in processes]
    total = sum(w * p.waiting_time for w, p in zip(weights, processes))
    return total / sum(weights)


def score(goal, scheduled_processes):
    """The number an algorithm is judged on for a given goal (lower = better)."""
    if goal == "waiting":
        return summarize(scheduled_processes)["avg_waiting_time"]
    if goal == "response":
        return summarize(scheduled_processes)["avg_response_time"]
    return round(priority_weighted_wait(scheduled_processes), 2)


def build_dataset(num_workloads=500, seed=7):
    rng = random.Random(seed)       # fixed seed -> same dataset every run
    rows = []
    for workload_id in range(num_workloads):
        processes = generate_workload(rng)
        features = analyze_workload(processes)

        # Run every algorithm once on this workload
        results = {name: fn(processes)[0] for name, fn in ALGORITHMS.items()}

        for goal in GOALS:
            scores = {name: score(goal, res) for name, res in results.items()}
            # Winner = lowest score. Ties: lower waiting time, then lower
            # response time, then whichever is listed first in ALGORITHMS.
            winner = min(ALGORITHMS, key=lambda n: (
                scores[n],
                summarize(results[n])["avg_waiting_time"],
                summarize(results[n])["avg_response_time"],
            ))

            row = {"workload_id": workload_id}
            row.update({name: features[name] for name in FEATURE_NAMES})
            row["goal"] = goal
            row["best_algorithm"] = winner
            for name in ALGORITHMS:
                row[f"score_{name}"] = scores[name]
            rows.append(row)
    return rows


def save_dataset(rows, filepath):
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = build_dataset(num_workloads=500)
    save_dataset(rows, "data/training_data.csv")
    print(f"Saved {len(rows)} labelled examples to data/training_data.csv\n")

    print("Who won overall:")
    counts = {}
    for r in rows:
        counts[r["best_algorithm"]] = counts.get(r["best_algorithm"], 0) + 1
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {name:<18}{count:>5}  ({count / len(rows) * 100:.0f}%)")

    print("\nWho won, per goal:")
    for goal in GOALS:
        sub = {}
        for r in rows:
            if r["goal"] == goal:
                sub[r["best_algorithm"]] = sub.get(r["best_algorithm"], 0) + 1
        text = ", ".join(f"{k}: {v}" for k, v in sorted(sub.items(), key=lambda x: -x[1]))
        print(f"  {goal:<9}{text}")