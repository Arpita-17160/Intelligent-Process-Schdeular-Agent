"""
memory.py
---------
Memory allocation strategies: First Fit, Best Fit and Worst Fit.

Memory is a row of HOLES (free chunks). Each process asks for some amount
of memory and the strategy decides which hole it gets. If the process is
smaller than the hole, the process takes the front part and the rest stays
behind as a smaller hole.

    First Fit  - the first hole that is big enough
    Best Fit   - the SMALLEST hole that is big enough
    Worst Fit  - the LARGEST hole

Over time, many small leftover holes build up. That is EXTERNAL
FRAGMENTATION: plenty of free memory in total, but no single hole large
enough for the next request.

Run the demo with:   python -m src.memory
"""


def _first_fit(free_segments):
    return free_segments[0]


def _best_fit(free_segments):
    return min(free_segments, key=lambda seg: (seg["size"], seg["start"]))


def _worst_fit(free_segments):
    return max(free_segments, key=lambda seg: (seg["size"], -seg["start"]))


# Each strategy receives the holes that are BIG ENOUGH (in address order)
# and returns the one it prefers.
STRATEGIES = {
    "First Fit": _first_fit,
    "Best Fit": _best_fit,
    "Worst Fit": _worst_fit,
}


def _validate(partitions, requests, strategy):
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose one of: {', '.join(STRATEGIES)}")
    if not partitions:
        raise ValueError("there must be at least one memory block")
    if any(size <= 0 for size in partitions) or any(size <= 0 for size in requests):
        raise ValueError("all memory sizes must be positive")


def allocate(partitions, requests, strategy):
    """
    partitions: sizes of the initial free blocks, in address order, e.g. [100, 500, 200]
    requests:   memory each process asks for, in arrival order -> P1, P2, ...
    strategy:   "First Fit", "Best Fit" or "Worst Fit"

    Returns a dict with:
        placements  one entry per process: where it went, or why it failed
        memory_map  the final layout, in address order
        stats       totals and the fragmentation figure
    """
    _validate(partitions, requests, strategy)
    choose = STRATEGIES[strategy]

    # Lay the blocks out one after another, with start addresses.
    segments, address = [], 0
    for size in partitions:
        segments.append({"start": address, "size": size, "owner": None})
        address += size

    placements = []
    for number, size in enumerate(requests, start=1):
        name = f"P{number}"
        candidates = [s for s in segments if s["owner"] is None and s["size"] >= size]

        if not candidates:
            total_free = sum(s["size"] for s in segments if s["owner"] is None)
            if total_free >= size:
                reason = (f"external fragmentation: {total_free} free in total, "
                          f"but no single hole of {size}")
            else:
                reason = f"not enough memory: only {total_free} free in total"
            placements.append({"process": name, "size": size, "start": None,
                               "placed": False, "reason": reason})
            continue

        chosen = choose(candidates)
        if chosen["size"] > size:                       # split: leftover stays a hole
            leftover = {"start": chosen["start"] + size,
                        "size": chosen["size"] - size, "owner": None}
            segments.insert(segments.index(chosen) + 1, leftover)
        chosen["size"] = size
        chosen["owner"] = name
        placements.append({"process": name, "size": size, "start": chosen["start"],
                           "placed": True, "reason": ""})

    holes = [s["size"] for s in segments if s["owner"] is None]
    total_free = sum(holes)
    largest = max(holes) if holes else 0
    stats = {
        "total_memory": sum(partitions),
        "placed": sum(1 for p in placements if p["placed"]),
        "failed": sum(1 for p in placements if not p["placed"]),
        "used": sum(p["size"] for p in placements if p["placed"]),
        "total_free": total_free,
        "largest_hole": largest,
        # 0% = all free memory is in one piece. Higher = more scattered.
        "external_fragmentation": round((1 - largest / total_free) * 100, 1) if total_free else 0.0,
    }
    return {"strategy": strategy, "placements": placements,
            "memory_map": segments, "stats": stats}


def compare_strategies(partitions, requests):
    """Runs all three strategies on the same input. Returns {name: result}."""
    return {name: allocate(partitions, requests, name) for name in STRATEGIES}


# ----------------------------------------------------------------------
# Demo
# ----------------------------------------------------------------------

def _print_result(result):
    stats = result["stats"]
    print(f"\n--- {result['strategy']} ---")
    for p in result["placements"]:
        if p["placed"]:
            print(f"  {p['process']} ({p['size']:>3}) -> placed at address {p['start']}")
        else:
            print(f"  {p['process']} ({p['size']:>3}) -> FAILED, {p['reason']}")

    print("  Final memory map:")
    for seg in result["memory_map"]:
        end = seg["start"] + seg["size"] - 1
        label = seg["owner"] if seg["owner"] else "free hole"
        print(f"    {seg['start']:>5} - {end:<5} size {seg['size']:>3}  {label}")
    print(f"  Free: {stats['total_free']} in total, largest hole {stats['largest_hole']}"
          f"  ->  external fragmentation {stats['external_fragmentation']}%")


def demo():
    partitions = [100, 500, 200, 300, 600]     # a classic textbook example
    requests = [212, 417, 112, 426]

    print("=" * 66)
    print("Memory blocks:", partitions, "  Process requests:", requests)
    print("=" * 66)

    results = compare_strategies(partitions, requests)
    for result in results.values():
        _print_result(result)

    print("\n" + "=" * 66)
    print("Comparison")
    print("=" * 66)
    print(f"{'Strategy':<12}{'Placed':>8}{'Failed':>8}{'Free':>7}{'Largest hole':>14}{'Fragmentation':>16}")
    for name, result in results.items():
        s = result["stats"]
        print(f"{name:<12}{s['placed']:>8}{s['failed']:>8}{s['total_free']:>7}"
              f"{s['largest_hole']:>14}{s['external_fragmentation']:>15}%")


if __name__ == "__main__":
    demo()