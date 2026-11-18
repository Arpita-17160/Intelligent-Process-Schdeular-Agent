
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from src.process import Process
from src.algorithms.fcfs import fcfs

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "Backend is running"
    })


@app.route("/api/scheduling/fcfs", methods=["POST"])
def run_fcfs():
    data = request.get_json(silent=True) or {}
    raw_processes = data.get("processes", [])

    if not raw_processes:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        processes = []

        for item in raw_processes:
            pid = str(item["pid"]).strip()
            arrival = int(item["arrival_time"])
            burst = int(item["burst_time"])
            priority = int(item.get("priority", 1))

            if not pid or arrival < 0 or burst < 1 or priority < 0:
                raise ValueError("Invalid process values")

            processes.append(Process(
                pid=pid,
                arrival_time=arrival,
                burst_time=burst,
                priority=priority
            ))

        if len({p.pid for p in processes}) != len(processes):
            raise ValueError("Process IDs must be unique")

        scheduled, gantt = fcfs(processes)

        return jsonify({
            "algorithm": "FCFS",
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "turnaround_time": p.turnaround_time,
                    "waiting_time": p.waiting_time,
                    "response_time": p.response_time
                }
                for p in scheduled
            ],
            "gantt_chart": [
                {
                    "pid": pid,
                    "start": start,
                    "end": end
                }
                for pid, start, end in gantt
            ]
        })

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/scheduling/sjf", methods=["POST"])
def schedule_sjf():
    from flask import request, jsonify
    from src.process import Process
    from src.algorithms.sjf import sjf

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        processes = [
            Process(
                pid=str(p["pid"]),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0))
            )
            for p in process_data
        ]

        scheduled, gantt = sjf(processes)

        return jsonify({
            "algorithm": "SJF",
            "gantt_chart": [
                {"pid": pid, "start": start, "end": end}
                for pid, start, end in gantt
            ],
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "waiting_time": p.waiting_time,
                    "turnaround_time": p.turnaround_time,
                    "response_time": p.response_time
                }
                for p in scheduled
            ]
        })

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid process data: {e}"}), 400


@app.route("/api/scheduling/round-robin", methods=["POST"])
def schedule_round_robin():
    from flask import request, jsonify
    from src.process import Process
    from src.algorithms.round_robin import round_robin

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    time_quantum = data.get("time_quantum", 2)

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        time_quantum = int(time_quantum)

        if time_quantum <= 0:
            return jsonify({"error": "Time quantum must be greater than 0"}), 400

        processes = [
            Process(
                pid=str(p["pid"]),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0))
            )
            for p in process_data
        ]

        if any(p.arrival_time < 0 or p.burst_time <= 0 for p in processes):
            return jsonify({
                "error": "Arrival times must be non-negative and burst times must be positive"
            }), 400

        scheduled, gantt = round_robin(processes, time_quantum)

        return jsonify({
            "algorithm": "Round Robin",
            "time_quantum": time_quantum,
            "gantt_chart": [
                {"pid": pid, "start": start, "end": end}
                for pid, start, end in gantt
            ],
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "waiting_time": p.waiting_time,
                    "turnaround_time": p.turnaround_time,
                    "response_time": p.response_time
                }
                for p in scheduled
            ]
        })

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid process data: {e}"}), 400


@app.route("/api/scheduling/priority", methods=["POST"])
def schedule_priority():
    from flask import request, jsonify
    from src.process import Process
    from src.algorithms.priority_scheduling import priority_scheduling

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    aging_interval = data.get("aging_interval", 4)
    aging_boost = data.get("aging_boost", 1)

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        aging_interval = int(aging_interval)
        aging_boost = int(aging_boost)

        if aging_interval <= 0:
            return jsonify({"error": "Aging interval must be greater than 0"}), 400

        if aging_boost < 0:
            return jsonify({"error": "Aging boost cannot be negative"}), 400

        processes = [
            Process(
                pid=str(p["pid"]),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0))
            )
            for p in process_data
        ]

        if any(p.arrival_time < 0 or p.burst_time <= 0 for p in processes):
            return jsonify({
                "error": "Arrival times must be non-negative and burst times must be positive"
            }), 400

        scheduled, gantt = priority_scheduling(
            processes,
            aging_interval=aging_interval,
            aging_boost=aging_boost
        )

        return jsonify({
            "algorithm": "Priority Scheduling with Aging",
            "aging_interval": aging_interval,
            "aging_boost": aging_boost,
            "gantt_chart": [
                {"pid": pid, "start": start, "end": end}
                for pid, start, end in gantt
            ],
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "waiting_time": p.waiting_time,
                    "turnaround_time": p.turnaround_time,
                    "response_time": p.response_time
                }
                for p in scheduled
            ]
        })

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid process data: {e}"}), 400


@app.route("/api/scheduling/mlfq", methods=["POST"])
def schedule_mlfq():
    from flask import request, jsonify
    from src.process import Process
    from src.algorithms.mlfq import mlfq

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    quantums = data.get("quantums", [2, 4, 8])

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        if not isinstance(quantums, list) or not quantums:
            return jsonify({
                "error": "Quantums must be a non-empty list of positive integers"
            }), 400

        quantums = [int(q) for q in quantums]

        if any(q <= 0 for q in quantums):
            return jsonify({
                "error": "Every queue quantum must be greater than 0"
            }), 400

        processes = [
            Process(
                pid=str(p["pid"]),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 0))
            )
            for p in process_data
        ]

        if any(p.arrival_time < 0 or p.burst_time <= 0 for p in processes):
            return jsonify({
                "error": "Arrival times must be non-negative and burst times must be positive"
            }), 400

        scheduled, gantt = mlfq(processes, quantums=tuple(quantums))

        return jsonify({
            "algorithm": "MLFQ",
            "quantums": quantums,
            "gantt_chart": [
                {"pid": pid, "start": start, "end": end}
                for pid, start, end in gantt
            ],
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "priority": p.priority,
                    "start_time": p.start_time,
                    "completion_time": p.completion_time,
                    "waiting_time": p.waiting_time,
                    "turnaround_time": p.turnaround_time,
                    "response_time": p.response_time
                }
                for p in scheduled
            ]
        })

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid process data: {e}"}), 400


@app.route("/api/recommend", methods=["POST"])
def recommend_algorithm():
    from src.ml_agent import recommend_algorithm_ml

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    goal = data.get("goal", "waiting")

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        if goal not in ("waiting", "response", "priority"):
            return jsonify({
                "error": "Goal must be waiting, response, or priority"
            }), 400

        processes = [
            Process(
                pid=str(p["pid"]).strip(),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 1))
            )
            for p in process_data
        ]

        if any(
            not p.pid or p.arrival_time < 0 or
            p.burst_time <= 0 or p.priority < 0
            for p in processes
        ):
            return jsonify({"error": "Invalid process values"}), 400

        if len({p.pid for p in processes}) != len(processes):
            return jsonify({"error": "Process IDs must be unique"}), 400

        algorithm, explanation, stats = recommend_algorithm_ml(
            processes, goal
        )

        return jsonify({
            "goal": goal,
            "recommended_algorithm": algorithm,
            "explanation": explanation,
            "workload_stats": stats
        })

    except FileNotFoundError:
        return jsonify({
            "error": "ML model not found. Train it first using: python -m ml.train_model"
        }), 500
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/predictions", methods=["POST"])
def predict_burst_times():
    from src.predictor import assign_predictions, mean_absolute_error

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    alpha = data.get("alpha", 0.5)

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        alpha = float(alpha)

        if not 0 < alpha <= 1:
            return jsonify({"error": "Alpha must be greater than 0 and at most 1"}), 400

        processes = [
            Process(
                pid=str(p["pid"]).strip(),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 1))
            )
            for p in process_data
        ]

        if any(
            not p.pid or p.arrival_time < 0 or
            p.burst_time <= 0 or p.priority < 0
            for p in processes
        ):
            return jsonify({"error": "Invalid process values"}), 400

        if len({p.pid for p in processes}) != len(processes):
            return jsonify({"error": "Process IDs must be unique"}), 400

        assign_predictions(processes, alpha=alpha)
        error = mean_absolute_error(processes)

        return jsonify({
            "alpha": alpha,
            "mean_absolute_error": error,
            "processes": [
                {
                    "pid": p.pid,
                    "arrival_time": p.arrival_time,
                    "burst_time": p.burst_time,
                    "predicted_burst": p.predicted_burst,
                    "prediction_error": round(
                        abs(p.predicted_burst - p.burst_time), 2
                    )
                }
                for p in processes
            ]
        })

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400



@app.route("/api/scheduling/compare", methods=["POST"])
def compare_scheduling_algorithms():
    from src.analytics import compare_algorithms
    from src.algorithms.sjf import sjf
    from src.algorithms.round_robin import round_robin
    from src.algorithms.priority_scheduling import priority_scheduling
    from src.algorithms.mlfq import mlfq
    from src.predictor import assign_predictions

    data = request.get_json(silent=True) or {}
    process_data = data.get("processes", [])
    goal = data.get("goal", "waiting")

    metric_map = {
        "waiting": "avg_waiting_time",
        "turnaround": "avg_turnaround_time",
        "response": "avg_response_time"
    }

    if goal not in metric_map:
        return jsonify({
            "error": "Goal must be waiting, turnaround, or response"
        }), 400

    if not process_data:
        return jsonify({"error": "Provide at least one process"}), 400

    try:
        processes = [
            Process(
                pid=str(p["pid"]).strip(),
                arrival_time=int(p["arrival_time"]),
                burst_time=int(p["burst_time"]),
                priority=int(p.get("priority", 1))
            )
            for p in process_data
        ]

        if any(
            not p.pid or p.arrival_time < 0
            or p.burst_time <= 0 or p.priority < 0
            for p in processes
        ):
            return jsonify({"error": "Invalid process values"}), 400

        if len({p.pid for p in processes}) != len(processes):
            return jsonify({"error": "Process IDs must be unique"}), 400

        assign_predictions(processes)

        algorithms = {
            "FCFS": fcfs,
            "SJF": sjf,
            "Round Robin": lambda ps: round_robin(ps, time_quantum=2),
            "Priority (aging)": priority_scheduling,
            "MLFQ": mlfq
        }

        comparison = compare_algorithms(processes, algorithms)

        metric = metric_map[goal]
        comparison.sort(key=lambda item: item[metric])

        best_value = comparison[0][metric]

        for item in comparison:
            item["is_best"] = abs(item[metric] - best_value) < 1e-9

        return jsonify({
            "goal": goal,
            "ranking_metric": metric,
            "ranking_criterion": goal,
            "comparison": comparison
        })

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": f"Invalid process data: {exc}"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
