"""
analytics.py
------------
Runs every scheduling algorithm on the same workload and produces a
clean, ranked comparison - this is the evidence base the scheduling
agent (see agent.py) uses to decide which algorithm to recommend.
"""

from src.metrics import summarize


def compare_algorithms(processes, algorithms):
    """
    algorithms: dict of {name: algo_fn} - e.g.
        {"FCFS": fcfs, "SJF": sjf, "Round Robin": lambda p: round_robin(p, 2)}

    Returns: list of dicts, one per algorithm, each containing the
    algorithm name and its summary stats, SORTED by avg_waiting_time
    (best/lowest first).
    """
    comparison = []
    for name, algo_fn in algorithms.items():
        result, gantt = algo_fn(processes)
        stats = summarize(result)
        stats["algorithm"] = name
        comparison.append(stats)

    comparison.sort(key=lambda s: s["avg_waiting_time"])
    return comparison


def print_comparison_table(comparison):
    """Pretty-prints the ranked comparison to the terminal."""
    print(f"\n{'=' * 70}\nAlgorithm Comparison (ranked by avg waiting time)\n{'=' * 70}")
    header = f"{'Rank':<6}{'Algorithm':<20}{'Avg Waiting':<15}{'Avg Turnaround':<18}{'Avg Response':<15}"
    print(header)
    print("-" * len(header))
    for i, stats in enumerate(comparison, start=1):
        print(f"{i:<6}{stats['algorithm']:<20}{stats['avg_waiting_time']:<15}"
              f"{stats['avg_turnaround_time']:<18}{stats['avg_response_time']:<15}")

    winner = comparison[0]
    print(f"\nBest performing algorithm for this workload: {winner['algorithm']} "
          f"(avg waiting time = {winner['avg_waiting_time']})")