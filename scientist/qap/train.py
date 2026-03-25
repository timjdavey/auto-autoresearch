"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


import time
import random


def _compute_cost(flow, distance, assignment):
    """Compute QAP objective cost."""
    n = len(flow)
    cost = 0
    for i in range(n):
        pi = assignment[i]
        for j in range(n):
            cost += flow[i][j] * distance[pi][assignment[j]]
    return cost


def _greedy_construction(flow, distance):
    """Greedy nearest-neighbor construction: build assignment incrementally."""
    n = len(flow)
    assignment = [-1] * n
    used_locations = set()
    remaining_facilities = list(range(n))

    # Start with first facility at location 0
    assignment[0] = 0
    used_locations.add(0)
    remaining_facilities.remove(0)

    # Greedily place remaining facilities
    while remaining_facilities:
        best_facility = None
        best_location = None
        best_cost_delta = float('inf')

        for fac in remaining_facilities:
            for loc in range(n):
                if loc in used_locations:
                    continue
                # Cost delta if we place facility fac at location loc
                delta = 0
                for i in range(n):
                    if assignment[i] != -1:
                        delta += flow[fac][i] * distance[loc][assignment[i]]
                        delta += flow[i][fac] * distance[assignment[i]][loc]

                if delta < best_cost_delta:
                    best_cost_delta = delta
                    best_facility = fac
                    best_location = loc

        if best_facility is not None:
            assignment[best_facility] = best_location
            used_locations.add(best_location)
            remaining_facilities.remove(best_facility)

    return assignment


def _two_opt_delta(flow, distance, assignment, i, j):
    """Compute cost delta for swapping facilities i and j (not locations)."""
    n = len(assignment)
    delta = 0

    # When we swap assignment[i] and assignment[j]:
    # Old: assignment[i] and assignment[j]
    # New: assignment[j] and assignment[i]

    pi = assignment[i]
    pj = assignment[j]

    for k in range(n):
        if k == i or k == j:
            continue
        pk = assignment[k]

        # Old cost: flow[i][k] * distance[pi][pk] + flow[k][i] * distance[pk][pi]
        #           flow[j][k] * distance[pj][pk] + flow[k][j] * distance[pk][pj]
        # New cost: flow[i][k] * distance[pj][pk] + flow[k][i] * distance[pk][pj]
        #           flow[j][k] * distance[pi][pk] + flow[k][j] * distance[pk][pi]

        old = flow[i][k] * distance[pi][pk] + flow[k][i] * distance[pk][pi]
        old += flow[j][k] * distance[pj][pk] + flow[k][j] * distance[pk][pj]

        new = flow[i][k] * distance[pj][pk] + flow[k][i] * distance[pk][pj]
        new += flow[j][k] * distance[pi][pk] + flow[k][j] * distance[pk][pi]

        delta += new - old

    # Self-pair cost changes
    old_pair = flow[i][j] * distance[pi][pj] + flow[j][i] * distance[pj][pi]
    new_pair = flow[i][j] * distance[pj][pi] + flow[j][i] * distance[pi][pj]
    delta += new_pair - old_pair

    return delta


def _two_opt_search(flow, distance, assignment, time_limit=50):
    """2-opt local search with delta costs and time budget."""
    n = len(flow)
    best_assignment = assignment[:]

    start_time = time.time()
    improved = True
    iterations = 0

    while improved and time.time() - start_time < time_limit:
        improved = False
        iterations += 1

        # Limit iterations on large instances
        if n > 60 and iterations > 5:
            break

        for i in range(n):
            for j in range(i + 1, n):
                delta = _two_opt_delta(flow, distance, best_assignment, i, j)

                if delta < 0:
                    # Perform swap
                    best_assignment[i], best_assignment[j] = best_assignment[j], best_assignment[i]
                    improved = True
                    break

            if improved:
                break

    return best_assignment


def solve(flow: list[list[int]], distance: list[list[int]]) -> list[int]:
    """
    Solve the Quadratic Assignment Problem.

    Assign n facilities to n locations to minimise total cost:
        cost = sum over all (i,j) of flow[i][j] * distance[assignment[i]][assignment[j]]

    Args:
        flow: n x n symmetric matrix. flow[i][j] = flow between facility i and j.
        distance: n x n symmetric matrix. distance[k][l] = distance between location k and l.

    Returns:
        assignment: list of length n where assignment[i] = location assigned to
                    facility i. Must be a permutation of 0..n-1.
    """
    n = len(flow)
    if n == 0:
        return []
    if n == 1:
        return [0]

    best_assignment = None
    best_cost = float('inf')
    start_time = time.time()

    # Multi-start: try greedy construction + random permutations
    num_restarts = 4 if n > 60 else 5
    time_per_run = 50 / num_restarts

    for restart in range(num_restarts):
        if time.time() - start_time > 55:  # Leave 5s margin
            break

        if restart == 0:
            # First run: greedy construction
            assignment = _greedy_construction(flow, distance)
        else:
            # Random permutation
            assignment = list(range(n))
            random.shuffle(assignment)

        # Local search
        assignment = _two_opt_search(flow, distance, assignment, time_limit=time_per_run)
        cost = _compute_cost(flow, distance, assignment)

        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment if best_assignment is not None else list(range(n))
