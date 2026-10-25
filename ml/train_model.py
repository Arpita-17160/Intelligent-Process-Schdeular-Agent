"""
train_model.py
--------------
Trains a Decision Tree that predicts the best scheduling algorithm from
a workload's shape + the goal, using data/training_data.csv.

Steps:
  1. Load the data and turn it into numbers the model can use.
  2. Split into TRAIN (80%) and TEST (20%). The test part is hidden from
     the model, so its score shows how it does on unseen workloads.
  3. Choose the tree depth by cross-validation (on the train part only).
  4. Evaluate on the test part and compare with simple baselines.
  5. Save the final model to ml/model.pkl.

Run from the project root with:
    python -m ml.train_model
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

from ml.generate_training_data import FEATURE_NAMES, GOALS, ALGORITHMS

DATA_PATH = "data/training_data.csv"
MODEL_PATH = "ml/model.pkl"

# The exact columns the model sees, in a fixed order.
FEATURE_COLUMNS = FEATURE_NAMES + [f"goal_{g}" for g in GOALS]


def encode(df):
    """
    Turns each row into numbers. The goal is text ("waiting"), so it
    becomes three 0/1 columns (one-hot encoding): goal_waiting,
    goal_response, goal_priority. Exactly one of them is 1 per row.
    """
    X = df[FEATURE_NAMES].copy()
    for g in GOALS:
        X[f"goal_{g}"] = (df["goal"] == g).astype(int)
    return X[FEATURE_COLUMNS]


def evaluate(df_test, picks):
    """
    Two fair ways to judge a list of picks:

    optimal-pick rate: % of cases where the pick scored as well as the
        best possible. If two algorithms TIE for best, picking either
        counts as correct (calling one of them "wrong" would be unfair).

    average regret: how much worse the pick scored than the best, on
        average. 0.0 = perfect. A wrong pick that is nearly as good is a
        small mistake; a terrible pick is a big one.
    """
    scores = df_test[[f"score_{a}" for a in ALGORITHMS]]
    best = scores.min(axis=1).values
    chosen = np.array([row[f"score_{pick}"]
                       for (_, row), pick in zip(df_test.iterrows(), picks)])
    optimal = (np.abs(chosen - best) < 1e-9).mean() * 100
    regret = (chosen - best).mean()
    return round(optimal, 1), round(regret, 2)


def main():
    df = pd.read_csv(DATA_PATH)
    X, y, groups = encode(df), df["best_algorithm"], df["workload_id"]

    # --- 1. Split by WORKLOAD, so the 3 rows of one workload never land on
    #        both sides (that would let the model "peek" at the answer).
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=0)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    df_test = df.iloc[test_idx]
    print(f"Training rows: {len(X_train)}   Test rows: {len(X_test)}\n")

    # --- 2. Choose tree depth with cross-validation (train data only).
    #        Too shallow = too simple. Too deep = memorises the training data.
    print("Choosing tree depth (5-fold cross-validation on training data):")
    best_depth, best_score = None, -1
    for depth in [1, 2, 3, 4, 5, 6, 8, 10]:
        model = DecisionTreeClassifier(max_depth=depth, random_state=0)
        cv = cross_val_score(model, X_train, y_train, cv=GroupKFold(n_splits=5),
                             groups=groups.iloc[train_idx]).mean()
        print(f"  max_depth={depth:<3} score={cv * 100:.1f}%")
        if cv > best_score + 1e-9:          # strictly better -> prefer simpler tree
            best_depth, best_score = depth, cv
    print(f"\n-> Chosen max_depth = {best_depth}\n")

    # --- 3. Train on the training part, test on the hidden part.
    tree = DecisionTreeClassifier(max_depth=best_depth, random_state=0)
    tree.fit(X_train, y_train)
    tree_picks = list(tree.predict(X_test))

    # --- 4. Baselines: what would simple strategies score?
    always_same = [y_train.mode()[0]] * len(X_test)
    per_goal_best = y_train.groupby(df["goal"].iloc[train_idx]).agg(lambda s: s.mode()[0])
    goal_lookup = [per_goal_best[g] for g in df_test["goal"]]

    print("Results on the hidden TEST set (workloads the model never saw):")
    print(f"  {'Strategy':<40}{'Optimal-pick rate':>19}{'Avg regret':>12}")
    for name, picks in [
        ("Always pick the most common winner", always_same),
        ("Simple lookup: best algorithm per goal", goal_lookup),
        ("Decision tree (ML)", tree_picks),
    ]:
        optimal, regret = evaluate(df_test, picks)
        print(f"  {name:<40}{optimal:>18}%{regret:>12}")

    print("\nThe simple lookup (per goal):")
    for goal, algo in per_goal_best.items():
        print(f"  goal = {goal:<9} -> {algo}")

    print("\nWhat the tree pays attention to (feature importance):")
    importances = sorted(zip(FEATURE_COLUMNS, tree.feature_importances_), key=lambda x: -x[1])
    for name, value in importances:
        if value > 0:
            print(f"  {name:<18}{value * 100:5.1f}%")

    # --- 5. Save a final model trained on ALL the data. (We already
    #        measured honestly on the hidden test set above.)
    final = DecisionTreeClassifier(max_depth=best_depth, random_state=0).fit(X, y)
    joblib.dump({"model": final, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)
    print(f"\nSaved final model to {MODEL_PATH}")


if __name__ == "__main__":
    main()