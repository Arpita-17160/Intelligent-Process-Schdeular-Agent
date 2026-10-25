"""
deadlock.py
-----------
Deadlock handling, two ways:

1. AVOIDANCE - the Banker's Algorithm.
   Before granting a resource request, pretend to grant it and check that
   the system is still in a SAFE state (there is some order in which every
   process can finish). If not, the request is refused.

2. DETECTION.
   Let processes request freely, then work out which of them are stuck
   waiting on each other forever.

Resources are described with small tables (lists of lists):
    available[j]      free units of resource j right now
    max_demand[i][j]  the most process i may ever ask for of resource j
    allocation[i][j]  units of resource j that process i holds now
    need[i][j]        max_demand - allocation: what i may still ask for
    request[i][j]     (detection only) what process i is waiting for now

Run the demo with:   python -m src.deadlock
"""


def _names(count):
    return [f"P{i}" for i in range(count)]


def _check_shapes(available, *tables):
    """Every table must have one row per process and one column per resource."""
    m = len(available)
    n = len(tables[0])
    if any(x < 0 for x in available):
        raise ValueError("available cannot contain negative numbers")
    for table in tables:
        if len(table) != n:
            raise ValueError("all tables must have the same number of processes (rows)")
        for row in table:
            if len(row) != m:
                raise ValueError("every row must have one entry per resource")
            if any(x < 0 for x in row):
                raise ValueError("tables cannot contain negative numbers")


def calculate_need(max_demand, allocation):
    """need = max_demand - allocation, for every process and resource."""
    need = []
    for i, (max_row, alloc_row) in enumerate(zip(max_demand, allocation)):
        row = [mx - al for mx, al in zip(max_row, alloc_row)]
        if any(x < 0 for x in row):
            raise ValueError(f"P{i} holds more than its declared maximum")
        need.append(row)
    return need


def _find_finishing_order(available, needs, allocation, already_finished=None):
    """
    The heart of both algorithms. Repeatedly look for a process whose
    outstanding demand (`needs`) fits in what is free right now. Let it
    run to completion and give back everything it holds, which may let
    others run. Returns (finishing order as indices, finished flags).
    """
    n, m = len(allocation), len(available)
    work = list(available)
    finished = list(already_finished) if already_finished else [False] * n
    order = []

    progress = True
    while progress:
        progress = False
        for i in range(n):
            if not finished[i] and all(needs[i][j] <= work[j] for j in range(m)):
                for j in range(m):
                    work[j] += allocation[i][j]     # process i finishes and releases all
                finished[i] = True
                order.append(i)
                progress = True
    return order, finished


def is_safe(available, max_demand, allocation):
    """
    Safety algorithm. Returns (safe?, safe_sequence_as_names).
    The sequence is empty if the state is unsafe.
    """
    _check_shapes(available, max_demand, allocation)
    need = calculate_need(max_demand, allocation)
    order, finished = _find_finishing_order(available, need, allocation)

    if all(finished):
        names = _names(len(allocation))
        return True, [names[i] for i in order]
    return False, []


def request_resources(process, request, available, max_demand, allocation):
    """
    Banker's resource-request algorithm for ONE process.

    process: index of the requesting process (0 = P0, 1 = P1, ...)
    Returns a dict with:
        granted        True / False
        reason         plain-English explanation
        available      the system state AFTER the decision
        allocation     (unchanged if the request was not granted)
        safe_sequence  a safe order, if the request was granted

    The inputs are never modified.
    """
    _check_shapes(available, max_demand, allocation)
    if len(request) != len(available) or any(x < 0 for x in request):
        raise ValueError("request needs one non-negative entry per resource")

    name = f"P{process}"
    need = calculate_need(max_demand, allocation)
    m = len(available)

    def refused(reason):
        return {"granted": False, "reason": reason, "available": list(available),
                "allocation": [list(row) for row in allocation], "safe_sequence": []}

    # Rule 1: a process may not ask for more than it declared it would need.
    if any(request[j] > need[process][j] for j in range(m)):
        raise ValueError(f"{name} is asking for more than its declared maximum")

    # Rule 2: the resources must actually be free right now.
    if any(request[j] > available[j] for j in range(m)):
        return refused(f"{name} must WAIT: not enough resources are free right now")

    # Rule 3: pretend to grant it, and check the system would still be safe.
    new_available = [available[j] - request[j] for j in range(m)]
    new_allocation = [list(row) for row in allocation]
    for j in range(m):
        new_allocation[process][j] += request[j]

    safe, sequence = is_safe(new_available, max_demand, new_allocation)
    if not safe:
        return refused(f"{name} must WAIT: granting it would leave the system in an UNSAFE state")

    return {"granted": True,
            "reason": f"{name}'s request can be granted: the system stays safe",
            "available": new_available, "allocation": new_allocation,
            "safe_sequence": sequence}


def detect_deadlock(available, allocation, request):
    """
    Detection algorithm. Returns the list of processes that are deadlocked
    (empty list = no deadlock).

    Same idea as the safety check, but it looks at what each process is
    waiting for RIGHT NOW (`request`), not its worst-case future need.
    A process holding nothing cannot be part of a deadlock.
    """
    _check_shapes(available, allocation, request)
    holds_nothing = [all(x == 0 for x in row) for row in allocation]
    order, finished = _find_finishing_order(available, request, allocation, holds_nothing)

    names = _names(len(allocation))
    return [names[i] for i in range(len(allocation)) if not finished[i]]


# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------

def _print_table(title, table, resources):
    print(f"\n{title}")
    print("      " + "".join(f"{r:>4}" for r in resources))
    for i, row in enumerate(table):
        print(f"  P{i}  " + "".join(f"{x:>4}" for x in row))


def demo():
    resources = ["A", "B", "C"]

    # A classic textbook example: 5 processes, 3 resource types.
    available = [3, 3, 2]
    max_demand = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    allocation = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]

    print("=" * 62)
    print("PART 1: Is the current state safe?")
    print("=" * 62)
    _print_table("Allocation (what each process holds now)", allocation, resources)
    _print_table("Max (the most each may ever ask for)", max_demand, resources)
    _print_table("Need = Max - Allocation", calculate_need(max_demand, allocation), resources)
    print(f"\nAvailable: {dict(zip(resources, available))}")
    safe, sequence = is_safe(available, max_demand, allocation)
    print(f"Safe state? {safe}")
    print(f"Safe sequence: {' -> '.join(sequence)}")

    print("\n" + "=" * 62)
    print("PART 2: Banker's Algorithm deciding on resource requests")
    print("=" * 62)
    state = (available, allocation)
    for process, request in [(1, [1, 0, 2]), (4, [3, 3, 0]), (0, [0, 2, 0])]:
        result = request_resources(process, request, state[0], max_demand, state[1])
        print(f"\nP{process} requests {dict(zip(resources, request))}")
        print(f"  -> {'GRANTED' if result['granted'] else 'REFUSED'}: {result['reason']}")
        if result["granted"]:
            print(f"  Safe sequence afterwards: {' -> '.join(result['safe_sequence'])}")
            state = (result["available"], result["allocation"])

    print("\n" + "=" * 62)
    print("PART 3: Deadlock DETECTION")
    print("=" * 62)
    two = ["R0", "R1"]
    allocation2 = [[1, 0], [0, 1]]     # P0 holds R0, P1 holds R1
    request2 = [[0, 1], [1, 0]]        # P0 wants R1, P1 wants R0
    _print_table("Allocation", allocation2, two)
    _print_table("Waiting for (Request)", request2, two)
    print(f"\nFree resources: {dict(zip(two, [0, 0]))}")
    print(f"Deadlocked processes: {detect_deadlock([0, 0], allocation2, request2) or 'none'}")

    print(f"\nNow one spare R1 appears: {dict(zip(two, [0, 1]))}")
    print(f"Deadlocked processes: {detect_deadlock([0, 1], allocation2, request2) or 'none'}")


if __name__ == "__main__":
    demo()