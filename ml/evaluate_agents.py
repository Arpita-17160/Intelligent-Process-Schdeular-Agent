
"""
evaluate_agents.py
------------------
Head-to-head test of every agent on FRESH workloads - a different random
seed from the training data, so the model has never seen any of them.

For each workload and each goal we run all five algorithms, then ask:
"Did the agent pick an algorithm that scores as well as the best one?"

Run from the project root with:
    python -m ml.evaluate_agents
"""

import random

from src.agent import recommend_algorithm          # the OLD rule-based agent
from src.ml_agent import recommend_algorithm_ml, GOAL_LOOKUP
from ml.generate_training_data import (
    ALGORITHMS, GOALS, generate_workload, score,
)

FRESH_SEED = 12345        # training used seed 7 - this is a different world
NUM_WORKLOADS = 1000


def main():
    rng = random.Random(FRESH_SEED)

    strategies = {
        "Old rule-based agent (ignores goal)": lambda procs, goal: recommend_algorithm(procs)[0],
        "Always pick SJF": lambda procs, goal: "SJF",
        "Simple lookup: best algorithm per goal": lambda procs, goal: GOAL_LOOKUP[goal],
        "ML decision tree agent": lambda procs, goal: recommend_algorithm_ml(procs, goal)[0],
    }

    # results[strategy][goal] = [times optimal, total regret, count]
    results = {s: {g: [0, 0.0, 0] for g in GOALS} for s in strategies}

    for _ in range(NUM_WORKLOADS):
        procs = generate_workload(rng)
        scheduled = {name: fn(procs)[0] for name, fn in ALGORITHMS.items()}

        for goal in GOALS:
            scores = {name: score(goal, res) for name, res in scheduled.items()}
            best = min(scores.values())

            for strategy, pick_fn in strategies.items():
                pick = pick_fn(procs, goal)
                regret = scores[pick] - best
                cell = results[strategy][goal]
                cell[0] += 1 if regret < 1e-9 else 0     # ties count as correct
                cell[1] += regret
                cell[2] += 1

    print(f"Tested on {NUM_WORKLOADS} brand-new workloads x {len(GOALS)} goals "
          f"= {NUM_WORKLOADS * len(GOALS)} decisions\n")

    print(f"{'Strategy':<42}{'Optimal-pick rate':>19}{'Avg regret':>12}")
    print("-" * 73)
    for strategy in strategies:
        cells = results[strategy].values()
        total = sum(c[2] for c in cells)
        optimal = sum(c[0] for c in cells) / total * 100
        regret = sum(c[1] for c in cells) / total
        print(f"{strategy:<42}{optimal:>18.1f}%{regret:>12.2f}")

    print("\nOptimal-pick rate, split by goal:")
    print(f"{'Strategy':<42}" + "".join(f"{g:>11}" for g in GOALS))
    print("-" * (42 + 11 * len(GOALS)))
    for strategy in strategies:
        row = "".join(f"{results[strategy][g][0] / results[strategy][g][2] * 100:>10.1f}%"
                      for g in GOALS)
        print(f"{strategy:<42}{row}")


if __name__ == "__main__":
    main()