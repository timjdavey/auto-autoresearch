"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""
import random


def _calc_cost(assignment: list[int], flow: list[list[int]], distance: list[list[int]]) -> int:
    """Calculate total cost of an assignment."""
    cost = 0
    n = len(assignment)
    for i in range(n):
        for j in range(n):
            cost += flow[i][j] * distance[assignment[i]][assignment[j]]
    return cost


def _local_search(assignment: list[int], flow: list[list[int]], distance: list[list[int]], max_iter: int = 50) -> list[int]:
    """Apply 2-opt and Or-opt local search."""
    n = len(assignment)
    improved = True
    iterations = 0
    while improved and iterations < max_iter:
        improved = False
        iterations += 1

        # 2-opt: swap pairs
        for i in range(n):
            for j in range(i + 1, n):
                loc_i, loc_j = assignment[i], assignment[j]
                current_cost = 0
                swap_cost = 0

                for k in range(n):
                    if k != i and k != j:
                        current_cost += flow[i][k] * distance[loc_i][assignment[k]]
                        current_cost += flow[k][i] * distance[assignment[k]][loc_i]
                        current_cost += flow[j][k] * distance[loc_j][assignment[k]]
                        current_cost += flow[k][j] * distance[assignment[k]][loc_j]
                        swap_cost += flow[i][k] * distance[loc_j][assignment[k]]
                        swap_cost += flow[k][i] * distance[assignment[k]][loc_j]
                        swap_cost += flow[j][k] * distance[loc_i][assignment[k]]
                        swap_cost += flow[k][j] * distance[assignment[k]][loc_i]

                current_cost += flow[i][j] * distance[loc_i][loc_j]
                current_cost += flow[j][i] * distance[loc_j][loc_i]
                swap_cost += flow[i][j] * distance[loc_j][loc_i]
                swap_cost += flow[j][i] * distance[loc_i][loc_j]

                if swap_cost < current_cost:
                    assignment[i], assignment[j] = assignment[j], assignment[i]
                    improved = True

        # Or-opt: move single facility to different location
        if not improved:
            for i in range(n):
                for j in range(n):
                    if i != j:
                        loc_i, loc_j = assignment[i], assignment[j]
                        current_cost = 0
                        move_cost = 0

                        for k in range(n):
                            if k != i and k != j:
                                current_cost += flow[i][k] * distance[loc_i][assignment[k]]
                                current_cost += flow[k][i] * distance[assignment[k]][loc_i]
                                move_cost += flow[i][k] * distance[loc_j][assignment[k]]
                                move_cost += flow[k][i] * distance[assignment[k]][loc_j]

                        current_cost += flow[i][j] * distance[loc_i][loc_j]
                        move_cost += flow[i][j] * distance[loc_j][loc_j]

                        if move_cost < current_cost:
                            assignment[i] = loc_j
                            assignment[j] = loc_i
                            improved = True
                            break
                if improved:
                    break

    return assignment


def _greedy_assign(flow: list[list[int]], distance: list[list[int]]) -> list[int]:
    """Greedy assignment: facilities in random order, pick from top-2 best locations."""
    n = len(flow)
    assignment = [-1] * n
    available = list(range(n))
    facilities = list(range(n))
    random.shuffle(facilities)

    for facility in facilities:
        costs = []
        for loc in available:
            cost = 0
            for other_facility in range(n):
                if assignment[other_facility] != -1:
                    cost += flow[facility][other_facility] * distance[loc][assignment[other_facility]]
                    cost += flow[other_facility][facility] * distance[assignment[other_facility]][loc]
            costs.append((cost, loc))

        costs.sort()
        # Pick from top 2 (or 1 if only 1 available)
        k = min(2, len(costs))
        loc = random.choice([c[1] for c in costs[:k]])

        assignment[facility] = loc
        available.remove(loc)

    return assignment


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

    # Number of restarts and iterations based on problem size
    if n <= 50:
        num_restarts, max_iter = 12, 13
    elif n <= 60:
        num_restarts, max_iter = 9, 11
    else:
        num_restarts, max_iter = 6, 9

    for _ in range(num_restarts):
        # Greedy initialization
        assignment = _greedy_assign(flow, distance)
        # Local search
        assignment = _local_search(assignment, flow, distance, max_iter=max_iter)
        # Track best
        cost = _calc_cost(assignment, flow, distance)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    return best_assignment
