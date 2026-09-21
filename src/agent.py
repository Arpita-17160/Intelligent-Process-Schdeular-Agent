"""
agent.py
--------
A rule-based "intelligent" scheduling agent.

Instead of a human manually running every algorithm and reading a
comparison table, this agent inspects the WORKLOAD's characteristics
(how much burst times vary, how spread out priorities are, how bursty
the arrivals are) and recommends which scheduling algorithm is likely
to perform best - similar to how a systems engineer would reason about
it, just automated.

This is "rule-based" (if/else logic) rather than machine-learned - a
natural, simpler first version. A future upgrade (see README roadmap)
would replace this with a model trained on many simulated workloads.
"""

import statistics


def analyze_workload(processes):
    """
    Extracts simple descriptive statistics from a workload that
    characterize its "shape" - this is what the agent reasons about.
    """
    burst_times = [p.burst_time for p in processes]
    priorities = [p.priority for p in processes]
    arrival_times = [p.arrival_time for p in processes]

    burst_variance = statistics.pvariance(burst_times) if len(burst_times) > 1 else 0
    priority_spread = max(priorities) - min(priorities) if priorities else 0
    arrival_spread = max(arrival_times) - min(arrival_times) if arrival_times else 0

    return {
        "num_processes": len(processes),
        "avg_burst_time": round(statistics.mean(burst_times), 2),
        "burst_variance": round(burst_variance, 2),
        "priority_spread": priority_spread,
        "arrival_spread": arrival_spread,
    }


def recommend_algorithm(processes):
    """
    Applies simple, explainable rules to pick the algorithm most likely
    to perform well for this specific workload's shape.

    Returns: (recommended_algorithm_name, reasoning_explanation, workload_stats)
    """
    stats = analyze_workload(processes)

    # Rule 1: If priorities vary a lot, priority-driven scheduling
    # matters most - the workload is clearly signaling "some jobs are
    # much more important than others."
    if stats["priority_spread"] >= 3:
        return (
            "Priority (aging)",
            f"Priority spread is high ({stats['priority_spread']}), meaning some "
            f"processes are far more important than others. Priority scheduling "
            f"(with aging to prevent starvation) respects that.",
            stats
        )

    # Rule 2: If burst times vary a lot, SJF minimizes average waiting
    # time - this is SJF's core theoretical strength.
    if stats["burst_variance"] > 3:
        return (
            "SJF",
            f"Burst time variance is high ({stats['burst_variance']}), meaning job "
            f"sizes differ a lot. SJF minimizes average waiting time in exactly "
            f"this situation by running shorter jobs first.",
            stats
        )

    # Rule 3: If processes arrive close together with similar burst
    # times, this looks like an interactive/uniform workload - Round
    # Robin's fairness matters more than raw efficiency here.
    if stats["arrival_spread"] <= stats["num_processes"] * 2:
        return (
            "Round Robin",
            f"Processes arrive close together with fairly uniform burst times "
            f"(variance={stats['burst_variance']}). Round Robin gives every "
            f"process fair, regular access to the CPU in this situation.",
            stats
        )

    # Default fallback: FCFS is simple and predictable when nothing
    # else strongly stands out.
    return (
        "FCFS",
        "No strong workload signal favored another algorithm. FCFS is simple "
        "and predictable as a safe default.",
        stats
    )