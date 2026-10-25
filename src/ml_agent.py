"""
ml_agent.py
-----------
The machine-learning scheduling agent.

Given a workload and a GOAL (waiting / response / priority), it asks the
trained decision tree (ml/model.pkl) which algorithm will do best, and
explains the decision by showing the path the tree followed.

Train the model first with:  python -m ml.train_model
"""

from pathlib import Path

import joblib
import pandas as pd

from src.agent import analyze_workload

# Works no matter which folder you run Python from.
MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "model.pkl"

# The simple baseline found during training: best algorithm per goal.
GOAL_LOOKUP = {"waiting": "SJF", "response": "MLFQ", "priority": "SJF"}

_bundle = None   # the model is loaded once, then reused


def _load_model():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def _feature_row(stats, goal, feature_columns):
    """
    Builds the one row of numbers the model expects, in the same column
    order it was trained with. The goal becomes 0/1 columns (one-hot).
    """
    row = {}
    for column in feature_columns:
        if column.startswith("goal_"):
            row[column] = 1 if column == f"goal_{goal}" else 0
        else:
            row[column] = stats[column]
    return pd.DataFrame([row], columns=feature_columns)


def explain_decision(model, row):
    """
    Lists the yes/no questions the tree asked for THIS workload, in order.
    This is what makes a decision tree explainable.
    """
    tree = model.tree_
    names = list(row.columns)
    steps = []
    for node in model.decision_path(row).indices:     # nodes visited, root first
        is_leaf = tree.children_left[node] == tree.children_right[node]
        if is_leaf:
            continue
        feature = names[tree.feature[node]]
        value = row.iloc[0][feature]
        side = "<=" if value <= tree.threshold[node] else ">"
        steps.append(f"{feature} = {value:g} ({side} {tree.threshold[node]:.2f})")
    return " -> ".join(steps)


def recommend_algorithm_ml(processes, goal):
    """
    Returns: (algorithm_name, explanation, workload_stats)
    goal: "waiting", "response" or "priority"
    """
    bundle = _load_model()
    model, columns = bundle["model"], bundle["feature_columns"]

    stats = analyze_workload(processes)
    row = _feature_row(stats, goal, columns)
    algorithm = str(model.predict(row)[0])
    return algorithm, explain_decision(model, row), stats