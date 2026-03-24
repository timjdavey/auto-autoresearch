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
    time_limit = 58.0  # Leave 2s margin

    def compute_cost(assignment):
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    def compute_cost_delta(assignment, i, j):
        """Cost change if we swap facilities i and j."""
        cost = 0
        for k in range(n):
            if k != i and k != j:
                cost += flow[i][k] * (distance[assignment[j]][assignment[k]] - distance[assignment[i]][assignment[k]])
                cost += flow[k][i] * (distance[assignment[k]][assignment[j]] - distance[assignment[k]][assignment[i]])
                cost += flow[j][k] * (distance[assignment[i]][assignment[k]] - distance[assignment[j]][assignment[k]])
                cost += flow[k][j] * (distance[assignment[k]][assignment[i]] - distance[assignment[k]][assignment[j]])
        cost += flow[i][j] * (distance[assignment[j]][assignment[j]] - distance[assignment[i]][assignment[i]])
        cost += flow[j][i] * (distance[assignment[i]][assignment[i]] - distance[assignment[j]][assignment[j]])
        return cost

    def local_search_2opt(assignment):
        """Apply 2-opt local search until convergence or time limit."""
        improved = True
        iterations = 0
        dont_look_bits = [False] * n  # Don't-look bits optimization

        while improved and (time.time() - start_time) < time_limit:
            improved = False
            iterations += 1

            for i in range(n):
                if (time.time() - start_time) >= time_limit:
                    break
                if dont_look_bits[i]:
                    continue
                dont_look_bits[i] = True

                for j in range(i + 1, n):
                    delta = compute_cost_delta(assignment, i, j)
                    if delta < 0:
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        improved = True
                        dont_look_bits[i] = False
                        dont_look_bits[j] = False
                        break
                if improved:
                    break

            if improved:
                dont_look_bits = [False] * n  # Reset for next iteration
        return assignment

    def perturbation(assignment):
        """Apply random perturbation to escape local optimum."""
        perm = assignment[:]
        # Adaptive perturbation: use more swaps based on problem size
        k = max(3, n // 8)  # More aggressive for better diversification
        for _ in range(k):
            i = random.randint(0, n - 1)
            j = random.randint(0, n - 1)
            if i != j:
                perm[i], perm[j] = perm[j], perm[i]
        return perm

    def nearest_neighbor_init(seed_facility=0):
        """Greedy nearest-neighbor construction (faster variant with sampled candidates)."""
        assignment = [-1] * n
        used_locations = [False] * n
        assignment[seed_facility] = 0
        used_locations[0] = True

        for facility in range(n):
            if assignment[facility] != -1:
                continue
            best_loc = -1
            best_cost = float('inf')

            # For large problems, sample candidates instead of evaluating all
            candidates = [loc for loc in range(n) if not used_locations[loc]]
            if len(candidates) > 20:
                import random as _random
                sample_size = min(20, len(candidates))
                candidates = _random.sample(candidates, sample_size)

            for loc in candidates:
                # Cost of assigning facility to loc
                cost = 0
                for other_facility in range(n):
                    if assignment[other_facility] != -1:
                        other_loc = assignment[other_facility]
                        cost += flow[facility][other_facility] * distance[loc][other_loc]
                        cost += flow[other_facility][facility] * distance[other_loc][loc]
                if cost < best_cost:
                    best_cost = cost
                    best_loc = loc
            assignment[facility] = best_loc
            used_locations[best_loc] = True
        return assignment

    best_assignment = None
    best_cost = float('inf')

    # Iterated local search: try multiple initialization seeds for better starting point
    for seed_facility in range(min(5, n)):  # Try up to 5 different starting facilities
        if (time.time() - start_time) >= time_limit:
            break
        assignment = nearest_neighbor_init(seed_facility)
        assignment = local_search_2opt(assignment)
        cost = compute_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    # Iterate: perturb and improve
    iterations = 0
    no_improve_count = 0
    while (time.time() - start_time) < time_limit:
        iterations += 1
        # Perturb current best solution
        assignment = perturbation(best_assignment)
        # Local search
        assignment = local_search_2opt(assignment)
        cost = compute_cost(assignment)
        # Update best if improved
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]
            no_improve_count = 0
        else:
            no_improve_count += 1
        # Exit early if no improvement for many iterations
        if no_improve_count > 12:
            break

    return best_assignment if best_assignment is not None else list(range(n))
