
"""
main.py
-------
CLI entry point for the OS Process Scheduling Simulator.

Features:
1. CPU scheduling algorithms
2. Burst-time prediction and algorithm comparison
3. ML-based algorithm recommendation
4. Banker's algorithm and deadlock detection
5. First Fit, Best Fit, and Worst Fit memory allocation
"""

from src.process import Process
from src.algorithms.fcfs import fcfs
from src.algorithms.sjf import sjf
from src.algorithms.round_robin import round_robin
from src.algorithms.priority_scheduling import priority_scheduling
from src.algorithms.mlfq import mlfq

from src.metrics import print_process_table, summarize
from src.gantt import render_gantt_chart
from src.io_utils import load_workload_from_csv, save_results_to_csv
from src.analytics import compare_algorithms, print_comparison_table
from src.agent import analyze_workload
from src.ml_agent import recommend_algorithm_ml
from ml.generate_training_data import ALGORITHMS, GOALS, score
from src.predictor import assign_predictions, mean_absolute_error


# ==========================================================
# SAMPLE WORKLOAD
# ==========================================================

def get_sample_workload():
    return [
        Process("P1", arrival_time=0, burst_time=5, priority=2),
        Process("P2", arrival_time=1, burst_time=3, priority=1),
        Process("P3", arrival_time=2, burst_time=8, priority=3),
        Process("P4", arrival_time=3, burst_time=6, priority=2),
    ]


# ==========================================================
# CPU SCHEDULING
# ==========================================================

def run_algorithm(name, algo_fn, processes):
    result, gantt = algo_fn(processes)

    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    render_gantt_chart(gantt)
    print_process_table(result, algorithm_name=name)

    stats = summarize(result)

    print(
        f"\nAverages -> Waiting: {stats['avg_waiting_time']}  "
        f"Turnaround: {stats['avg_turnaround_time']}  "
        f"Response: {stats['avg_response_time']}"
    )

    save_results_to_csv(
        result,
        f"data/results_{name.split()[0]}.csv",
        algorithm_name=name
    )

    return stats


def run_cpu_and_ml():
    print("\n" + "=" * 70)
    print("CPU SCHEDULING AND ML ANALYSIS")
    print("=" * 70)

    processes = load_workload_from_csv("data/sample_workload.csv")
    assign_predictions(processes)

    print("\nWorkload:")
    for process in processes:
        print(f"  {process}")

    print("\nBurst-time predictions (exponential averaging):")
    for process in processes:
        print(
            f"  {process.pid}: actual={process.burst_time}  "
            f"predicted={process.predicted_burst}"
        )

    print(f"  Average prediction error: {mean_absolute_error(processes)}")

    results = {}

    results["FCFS"] = run_algorithm(
        "FCFS (First Come First Serve)", fcfs, processes
    )

    results["SJF"] = run_algorithm(
        "SJF (Shortest Job First)", sjf, processes
    )

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

    results["MLFQ"] = run_algorithm(
        "MLFQ (Multilevel Feedback Queue)", mlfq, processes
    )

    algorithms = {
        "FCFS": fcfs,
        "SJF": sjf,
        "SJF (predicted)": lambda p: sjf(p, use_prediction=True),
        "Round Robin": lambda p: round_robin(p, time_quantum=2),
        "Priority (aging)": priority_scheduling,
        "MLFQ": mlfq,
    }

    comparison = compare_algorithms(processes, algorithms)
    print("\nAlgorithm comparison:")
    print_comparison_table(comparison)

    print(f"\n{'=' * 70}")
    print("ML AGENT RECOMMENDATIONS")
    print("=" * 70)

    print(f"Workload characteristics: {analyze_workload(processes)}")

    scheduled = {
        name: fn(processes)[0]
        for name, fn in ALGORITHMS.items()
    }

    for goal in GOALS:
        pick, explanation, _ = recommend_algorithm_ml(processes, goal)

        scores = {
            name: score(goal, result)
            for name, result in scheduled.items()
        }

        best = min(scores.values())
        verdict = (
            "Optimal among evaluated algorithms"
            if scores[pick] - best < 1e-9
            else f"Best score among candidates: {best}"
        )

        print(f"\nGoal: {goal}")
        print(f"  Recommended algorithm: {pick}")
        print(f"  Score: {scores[pick]}")
        print(f"  Result: {verdict}")
        print("  Scores: " + " | ".join(
            f"{name}: {value}" for name, value in scores.items()
        ))
        print(f"  Explanation: {explanation}")


# ==========================================================
# DEADLOCK MANAGEMENT: BANKER'S ALGORITHM
# ==========================================================

def check_safe_state(available, allocation, maximum):
    """
    Check whether all processes can finish in some safe sequence.

    available: currently available resources
    allocation: resources currently held by each process
    maximum: maximum resource demand of each process
    """
    process_count = len(allocation)

    if len(maximum) != process_count:
        raise ValueError("Allocation and maximum matrices must match.")

    if any(len(row) != len(available) for row in allocation + maximum):
        raise ValueError("Resource matrix dimensions do not match.")

    if any(
        maximum[i][j] < allocation[i][j]
        for i in range(process_count)
        for j in range(len(available))
    ):
        raise ValueError("Maximum demand cannot be less than allocation.")

    need = [
        [
            maximum[i][j] - allocation[i][j]
            for j in range(len(available))
        ]
        for i in range(process_count)
    ]

    work = available[:]
    finished = [False] * process_count
    sequence = []

    while len(sequence) < process_count:
        found = False

        for i in range(process_count):
            if not finished[i] and all(
                need[i][j] <= work[j]
                for j in range(len(work))
            ):
                for j in range(len(work)):
                    work[j] += allocation[i][j]

                finished[i] = True
                sequence.append(f"P{i}")
                found = True

        if not found:
            break

    return all(finished), sequence, need


def run_bankers_demo():
    print("\n" + "=" * 70)
    print("DEADLOCK MANAGEMENT: BANKER'S ALGORITHM")
    print("=" * 70)

    # Classic safe-state example with three resource types.
    available = [3, 3, 2]

    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2],
    ]

    maximum = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3],
    ]

    safe, sequence, need = check_safe_state(
        available, allocation, maximum
    )

    print(f"Available resources (A, B, C): {available}")

    print("\nRemaining resource need:")
    for i, row in enumerate(need):
        print(f"  P{i}: {row}")

    if safe:
        print("\nResult: SAFE STATE")
        print("Safe sequence: " + " -> ".join(sequence))
        print("Every process can finish in this order.")
    else:
        print("\nResult: UNSAFE STATE")
        print("No safe sequence exists for this resource state.")


# ==========================================================
# DEADLOCK DETECTION
# ==========================================================

def detect_deadlock(available, allocation, request):
    """
    Detect processes that cannot finish with current resources.

    request[i] represents the resources process i is currently
    waiting for.
    """
    if len(allocation) != len(request):
        raise ValueError("Allocation and request matrices must match.")

    if any(
        len(row) != len(available)
        for row in allocation + request
    ):
        raise ValueError("Resource matrix dimensions do not match.")

    work = available[:]

    # A process holding no resources may be considered finished.
    finished = [
        all(value == 0 for value in row)
        for row in allocation
    ]

    for i in range(len(allocation)):
        if finished[i]:
            print(f"P{i} holds no resources; treated as finished.")

    changed = True

    while changed:
        changed = False

        for i in range(len(allocation)):
            if not finished[i] and all(
                request[i][j] <= work[j]
                for j in range(len(work))
            ):
                for j in range(len(work)):
                    work[j] += allocation[i][j]

                finished[i] = True
                changed = True

    return [
        f"P{i}"
        for i, done in enumerate(finished)
        if not done
    ]


def run_deadlock_detection_demo():
    print("\n" + "=" * 70)
    print("DEADLOCK DETECTION")
    print("=" * 70)

    # Two processes each hold one resource and wait for another.
    available = [0]

    allocation = [
        [1],
        [1],
    ]

    request = [
        [1],
        [1],
    ]

    print(f"Available resources: {available}")
    print(f"Allocation matrix: {allocation}")
    print(f"Outstanding requests: {request}")

    deadlocked = detect_deadlock(available, allocation, request)

    if deadlocked:
        print("\nResult: DEADLOCK DETECTED")
        print("Processes unable to finish: " + ", ".join(deadlocked))
    else:
        print("\nResult: NO DEADLOCK DETECTED")
        print("All processes can finish.")


# ==========================================================
# MEMORY ALLOCATION: FIRST FIT, BEST FIT, WORST FIT
# ==========================================================

def memory_allocate(blocks, requests, strategy):
    """
    Simulate variable-size memory allocation.

    Each initial block is a contiguous free region. A process is
    placed inside a suitable region, and the remaining part of
    that region stays free.
    """
    segments = []
    address = 0

    for size in blocks:
        segments.append({
            "start": address,
            "size": size,
            "owner": None
        })
        address += size

    results = []

    for index, size in enumerate(requests):
        name = f"P{index + 1}"

        candidates = [
            segment for segment in segments
            if segment["owner"] is None and segment["size"] >= size
        ]

        if not candidates:
            free_memory = sum(
                segment["size"]
                for segment in segments
                if segment["owner"] is None
            )

            if free_memory >= size:
                reason = (
                    f"Enough free memory ({free_memory}), "
                    "but no single block is large enough."
                )
            else:
                reason = (
                    f"Not enough free memory. "
                    f"Available: {free_memory} units."
                )

            results.append({
                "name": name,
                "size": size,
                "ok": False,
                "reason": reason
            })
            continue

        if strategy == "first":
            chosen = candidates[0]
        elif strategy == "best":
            chosen = min(candidates, key=lambda s: s["size"])
        elif strategy == "worst":
            chosen = max(candidates, key=lambda s: s["size"])
        else:
            raise ValueError(f"Unknown allocation strategy: {strategy}")

        start = chosen["start"]
        original_size = chosen["size"]
        position = segments.index(chosen)

        # Replace the free block with the allocated process.
        replacement = [{
            "start": start,
            "size": size,
            "owner": name
        }]

        # Keep any remaining memory as a free block.
        if original_size > size:
            replacement.append({
                "start": start + size,
                "size": original_size - size,
                "owner": None
            })

        segments[position:position + 1] = replacement

        results.append({
            "name": name,
            "size": size,
            "ok": True,
            "start": start,
            "end": start + size - 1
        })

    return segments, results


def run_memory_demo():
    print("\n" + "=" * 70)
    print("MEMORY ALLOCATION")
    print("=" * 70)

    # Example values; edit these lists to try different workloads.
    blocks = [100, 500, 200, 300, 600]
    requests = [212, 417, 112, 426]

    print(f"Initial free blocks: {blocks}")
    print(f"Process requests:    {requests}")
    print(f"Total memory:         {sum(blocks)} units")

    strategies = [
        ("first", "FIRST FIT"),
        ("best", "BEST FIT"),
        ("worst", "WORST FIT"),
    ]

    for strategy, title in strategies:
        segments, results = memory_allocate(
            blocks, requests, strategy
        )

        free_blocks = [
            segment for segment in segments
            if segment["owner"] is None
        ]

        free_memory = sum(
            segment["size"] for segment in free_blocks
        )

        largest_free = max(
            (segment["size"] for segment in free_blocks),
            default=0
        )

        print(f"\n{'-' * 60}")
        print(title)
        print("-" * 60)

        print("\nMemory layout:")
        for segment in segments:
            start = segment["start"]
            end = start + segment["size"] - 1
            owner = segment["owner"] or "FREE"

            print(
                f"  Address {start:>4} - {end:>4} | "
                f"{owner:<5} | {segment['size']} units"
            )

        print("\nProcess allocation results:")
        print(
            f"{'Process':<10}{'Size':<12}"
            f"{'Start':<12}{'End':<12}Status"
        )

        for result in results:
            if result["ok"]:
                print(
                    f"{result['name']:<10}"
                    f"{result['size']:<12}"
                    f"{result['start']:<12}"
                    f"{result['end']:<12}"
                    f"Allocated"
                )
            else:
                print(
                    f"{result['name']:<10}"
                    f"{result['size']:<12}"
                    f"{'-':<12}{'-':<12}"
                    f"Not allocated"
                )
                print(f"    Reason: {result['reason']}")

        allocated_count = sum(
            result["ok"] for result in results
        )

        print(f"\nProcesses allocated: {allocated_count}/{len(requests)}")
        print(f"Total free memory: {free_memory} units")
        print(f"Largest free block: {largest_free} units")


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================

def main():
    run_cpu_and_ml()
    run_bankers_demo()
    run_deadlock_detection_demo()
    run_memory_demo()

    print("\n" + "=" * 70)
    print("ALL CLI DEMONSTRATIONS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
