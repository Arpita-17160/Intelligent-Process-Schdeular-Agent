"""
predictor.py
------------
Burst-time prediction using exponential averaging.

A real OS cannot know how long a process will run before running it.
It can only ESTIMATE, based on how long the process ran the previous
times. The classic technique from OS textbooks is exponential averaging:

    next_prediction = alpha * last_actual + (1 - alpha) * previous_prediction

alpha (0 to 1) controls how much we trust recent behavior:
    alpha near 1 -> "the most recent burst is what matters"
    alpha near 0 -> "trust the long-term average, ignore recent changes"
"""

import random


def predict_next_burst(history, alpha=0.5, initial_guess=5):
    """
    history: list of a process's PAST actual burst times, oldest first
    alpha: weight given to the most recent observation (0 to 1)
    initial_guess: starting prediction before we have seen any history
    Returns: predicted length of the NEXT burst
    """
    prediction = initial_guess
    for actual in history:
        prediction = alpha * actual + (1 - alpha) * prediction
    return prediction


def simulate_history(burst_time, length=5, noise=0.3, rng=None):
    """
    Our simulator has no real past, so we fake one: past bursts are close
    to the process's true burst, but randomly off by up to +/- noise
    (0.3 = 30%). Real programs behave like this too - similar every time,
    but never exactly the same.
    """
    rng = rng or random.Random()
    return [max(1, round(burst_time * (1 + rng.uniform(-noise, noise))))
            for _ in range(length)]


def assign_predictions(processes, alpha=0.5, seed=42, history_length=5, noise=0.3):
    """
    Gives every process a predicted_burst. A fixed seed makes results
    repeatable, so tests and demos always show the same numbers.
    """
    rng = random.Random(seed)
    for p in processes:
        history = simulate_history(p.burst_time, history_length, noise, rng)
        p.predicted_burst = round(predict_next_burst(history, alpha), 2)
    return processes


def mean_absolute_error(processes):
    """Average gap between predicted and actual burst times (lower = better)."""
    errors = [abs(p.predicted_burst - p.burst_time) for p in processes]
    return round(sum(errors) / len(errors), 2)