"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
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
    time_budget = 50.0  # Leave 10s buffer within 60s limit

    def cost(assignment):
        """Calculate total QAP cost for given assignment."""
        total = 0
        for i in range(n):
            for j in range(n):
                total += flow[i][j] * distance[assignment[i]][assignment[j]]
        return total

    def greedy_construct(randomized=False):
        """Greedy nearest-neighbor construction, optionally with random tie-breaking."""
        used_locs = set()
        assignment_nn = [-1] * n
        assignment_nn[0] = 0
        used_locs.add(0)

        for fac in range(1, n):
            best_cost = float('inf')
            candidates = []

            for loc in range(n):
                if loc in used_locs:
                    continue

                # Cost to assign facility fac to location loc
                partial_cost = 0
                for i in range(fac):
                    partial_cost += flow[fac][i] * distance[loc][assignment_nn[i]]
                    partial_cost += flow[i][fac] * distance[assignment_nn[i]][loc]

                if partial_cost < best_cost:
                    best_cost = partial_cost
                    candidates = [loc]
                elif partial_cost == best_cost:
                    candidates.append(loc)

            # Random tie-breaking for exploration
            if randomized and len(candidates) > 1:
                best_loc = random.choice(candidates)
            else:
                best_loc = candidates[0]

            assignment_nn[fac] = best_loc
            used_locs.add(best_loc)

        return assignment_nn

    def local_search_best_improvement(assignment_nn):
        """2-opt local search using best-improvement strategy."""
        improved = True
        iterations = 0
        max_iterations = min(n * n, 500)

        while improved and iterations < max_iterations:
            if time.time() - start_time > time_budget:
                break

            improved = False
            iterations += 1
            best_cost = cost(assignment_nn)
            best_i, best_j = -1, -1

            # Find best swap in the neighborhood
            for i in range(n):
                for j in range(i + 1, n):
                    assignment_nn[i], assignment_nn[j] = assignment_nn[j], assignment_nn[i]
                    new_cost = cost(assignment_nn)
                    assignment_nn[i], assignment_nn[j] = assignment_nn[j], assignment_nn[i]

                    if new_cost < best_cost:
                        best_cost = new_cost
                        improved = True
                        best_i, best_j = i, j

            # Apply best swap if improvement found
            if improved:
                assignment_nn[best_i], assignment_nn[best_j] = assignment_nn[best_j], assignment_nn[best_i]

        return assignment_nn

    # Greedy construction + local search
    assignment_nn = greedy_construct(randomized=False)
    assignment_nn = local_search_best_improvement(assignment_nn)

    return assignment_nn
