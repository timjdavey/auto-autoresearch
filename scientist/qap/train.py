"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: Greedy construction + 2-opt local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import time
import random


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
    time_limit = 55.0  # Leave 5s buffer for safety

    def compute_cost(assignment):
        """Compute total QAP cost for given assignment."""
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    def greedy_construction(randomized=False):
        """Greedy nearest-neighbor construction."""
        assignment = [-1] * n
        used = [False] * n

        for facility in range(n):
            best_locs = []
            best_cost_delta = float('inf')

            for loc in range(n):
                if used[loc]:
                    continue

                # Calculate cost increase if we assign facility to loc
                cost_delta = 0
                for i in range(n):
                    if assignment[i] != -1:
                        cost_delta += flow[facility][i] * distance[loc][assignment[i]]
                        cost_delta += flow[i][facility] * distance[assignment[i]][loc]

                if cost_delta < best_cost_delta:
                    best_cost_delta = cost_delta
                    best_locs = [loc]
                elif randomized and cost_delta == best_cost_delta:
                    best_locs.append(loc)

            # Pick random location among tied best choices, or best if no ties
            best_loc = random.choice(best_locs) if randomized and best_locs else (best_locs[0] if best_locs else 0)
            assignment[facility] = best_loc
            used[best_loc] = True

        return assignment

    def compute_swap_delta(assignment, i, j):
        """Compute cost delta for swapping facilities i and j efficiently."""
        delta = 0
        loc_i = assignment[i]
        loc_j = assignment[j]

        # Cost change from swapping facilities i and j
        for k in range(n):
            if k == i or k == j:
                continue
            loc_k = assignment[k]
            delta += flow[i][k] * (distance[loc_j][loc_k] - distance[loc_i][loc_k])
            delta += flow[k][i] * (distance[loc_k][loc_j] - distance[loc_k][loc_i])
            delta += flow[j][k] * (distance[loc_i][loc_k] - distance[loc_j][loc_k])
            delta += flow[k][j] * (distance[loc_k][loc_i] - distance[loc_k][loc_j])

        # Cost change between facilities i and j themselves
        delta += flow[i][j] * (distance[loc_j][loc_i] - distance[loc_i][loc_j])
        delta += flow[j][i] * (distance[loc_i][loc_j] - distance[loc_j][loc_i])

        return delta

    def local_search_2opt(assignment):
        """Apply 2-opt local search: multiple passes until convergence."""
        max_passes = 10
        for pass_num in range(max_passes):
            if time.time() - start_time > time_limit:
                break
            improved = False
            for i in range(n):
                if time.time() - start_time > time_limit:
                    break
                for j in range(i + 1, n):
                    delta = compute_swap_delta(assignment, i, j)
                    if delta < 0:
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        improved = True
            if not improved:
                break

        return assignment

    # Try multiple greedy constructions
    best_assignment = greedy_construction(randomized=False)
    best_assignment = local_search_2opt(best_assignment)
    best_cost = compute_cost(best_assignment)

    # Try 1-2 randomized greedy constructions if time permits
    for attempt in range(2):
        if time.time() - start_time > time_limit - 5:
            break

        assignment = greedy_construction(randomized=True)
        assignment = local_search_2opt(assignment)
        cost = compute_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment
