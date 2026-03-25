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
    """Compute QAP objective: sum of flow[i][j] * distance[assignment[i]][assignment[j]]."""
    n = len(flow)
    cost = 0
    for i in range(n):
        pi = assignment[i]
        for j in range(n):
            cost += flow[i][j] * distance[pi][assignment[j]]
    return cost


def _cost_delta(flow, distance, assignment, i, j):
    """
    Compute cost change from swapping assignment[i] and assignment[j].
    Returns the delta (new_cost - current_cost).
    """
    n = len(flow)
    ai, aj = assignment[i], assignment[j]
    delta = 0

    # Changes in facility i's cost (now at location aj instead of ai)
    for k in range(n):
        ak = assignment[k]
        delta += flow[i][k] * (distance[aj][ak] - distance[ai][ak])
        delta += flow[k][i] * (distance[ak][aj] - distance[ak][ai])

    # Changes in facility j's cost (now at location ai instead of aj)
    for k in range(n):
        ak = assignment[k]
        delta += flow[j][k] * (distance[ai][ak] - distance[aj][ak])
        delta += flow[k][j] * (distance[ak][ai] - distance[ak][aj])

    # Avoid double-counting the direct i-j interaction
    delta -= 2 * (flow[i][j] * (distance[aj][ai] - distance[ai][aj]))
    delta -= 2 * (flow[j][i] * (distance[ai][aj] - distance[aj][ai]))

    return delta


def _two_opt(flow, distance, assignment, time_limit, start_time):
    """Perform 2-opt local search until time limit."""
    n = len(assignment)
    i = 0
    while time.time() - start_time < time_limit:
        j = i + 1
        found_improvement = False
        while j < n:
            delta = _cost_delta(flow, distance, assignment, i, j)
            if delta < 0:
                assignment[i], assignment[j] = assignment[j], assignment[i]
                found_improvement = True
                i = 0
                break
            j += 1
        if not found_improvement:
            i += 1
            if i >= n - 1:
                break


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

    start_time = time.time()
    time_limit = 55.0

    best_assignment = list(range(n))
    best_cost = _compute_cost(flow, distance, best_assignment)

    # Multi-start 2-opt
    num_restarts = max(2, min(10, n // 10))
    restart_time_each = time_limit / num_restarts

    for restart in range(num_restarts):
        if time.time() - start_time >= time_limit:
            break

        # Random initial solution
        assignment = list(range(n))
        random.shuffle(assignment)

        # 2-opt from this starting point
        _two_opt(flow, distance, assignment, restart_time_each, time.time())

        cost = _compute_cost(flow, distance, assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    return best_assignment
