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
    prediction = initial_guess
    for actual in history:
        prediction = alpha * actual + (1 - alpha) * prediction
    return prediction


def simulate_history(burst_time, length=5, noise=0.3, rng=None):
    rng = rng or random.Random()
    return [max(1, round(burst_time * (1 + rng.uniform(-noise, noise))))
            for _ in range(length)]


def assign_predictions(processes, alpha=0.5, seed=42, history_length=5, noise=0.3):
    rng = random.Random(seed)
    for p in processes:
        history = simulate_history(p.burst_time, history_length, noise, rng)
        p.predicted_burst = round(predict_next_burst(history, alpha), 2)
    return processes


def mean_absolute_error(processes):
    errors = [abs(p.predicted_burst - p.burst_time) for p in processes]
    return round(sum(errors) / len(errors), 2)