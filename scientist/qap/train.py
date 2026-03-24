"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time

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
    random.seed(42)  # Fixed seed for reproducibility
    n = len(flow)
    if n == 0:
        return []
    if n == 1:
        return [0]

    def swap_cost_delta(assignment, i, j):
        """Compute cost change from swapping positions i and j."""
        ai, aj = assignment[i], assignment[j]
        delta = 0
        for k in range(n):
            if k != i and k != j:
                ak = assignment[k]
                delta += flow[i][k] * (distance[aj][ak] - distance[ai][ak])
                delta += flow[k][i] * (distance[ak][aj] - distance[ak][ai])
                delta += flow[j][k] * (distance[ai][ak] - distance[aj][ak])
                delta += flow[k][j] * (distance[ak][ai] - distance[ak][aj])
        delta += flow[i][j] * (distance[aj][ai] - distance[ai][aj])
        delta += flow[j][i] * (distance[ai][aj] - distance[aj][ai])
        return delta

    def greedy_initial_solution(randomized=False):
        """Generate initial solution using greedy nearest-neighbor."""
        max_flow_facility = max(range(n), key=lambda i: sum(flow[i]))
        assignment = [-1] * n
        unassigned_facilities = set(range(n))
        unassigned_locations = set(range(n))

        assignment[max_flow_facility] = 0
        unassigned_facilities.remove(max_flow_facility)
        unassigned_locations.remove(0)

        while unassigned_facilities:
            next_facility = max(unassigned_facilities,
                              key=lambda f: sum(flow[f][i] for i in range(n) if assignment[i] != -1))

            def location_score(loc):
                flow_cost = sum(flow[next_facility][i] * distance[loc][assignment[i]]
                              for i in range(n) if assignment[i] != -1)
                assigned_locs = [assignment[i] for i in range(n) if assignment[i] != -1]
                avg_dist = sum(distance[loc][l] for l in assigned_locs) / len(assigned_locs) if assigned_locs else 0
                return flow_cost + 0.1 * avg_dist

            sorted_locs = sorted(unassigned_locations, key=location_score)
            if randomized and len(sorted_locs) > 1:
                k = min(3, len(sorted_locs))
                best_loc = random.choice(sorted_locs[:k])
            else:
                best_loc = sorted_locs[0]

            assignment[next_facility] = best_loc
            unassigned_facilities.remove(next_facility)
            unassigned_locations.remove(best_loc)

        return assignment

    def local_search(assignment, time_limit):
        """Apply 2-opt local search with time budget and perturbation."""
        start_time = time.time()
        best_assignment = assignment[:]
        best_cost = solution_cost(best_assignment)

        while time.time() - start_time < time_limit:
            improved = True
            iterations = 0
            max_iterations = n

            # Local search phase
            while improved and iterations < max_iterations:
                if time.time() - start_time > time_limit:
                    break
                improved = False
                iterations += 1
                for i in range(n - 1):
                    for j in range(i + 1, n):
                        delta = swap_cost_delta(assignment, i, j)
                        if delta < 0:
                            assignment[i], assignment[j] = assignment[j], assignment[i]
                            improved = True
                            break
                    if improved:
                        break

            # Check if we improved
            cost = solution_cost(assignment)
            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment[:]

            # Perturbation: random double move to escape local optimum
            if time.time() - start_time < time_limit * 0.9:  # Reserve final 10% for last local search
                i, j = random.sample(range(n), 2)
                assignment[i], assignment[j] = assignment[j], assignment[i]
            else:
                break

        return best_assignment

    def solution_cost(assignment):
        """Calculate total cost of an assignment."""
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    # Multi-start: try multiple initial solutions and keep the best
    start_time = time.time()
    total_time_budget = 55  # Reserve 5s buffer for safety
    best_assignment = None
    best_cost = float('inf')
    num_starts = 4 if n <= 60 else (3 if n < 75 else 1)  # More starts for smaller instances

    for start in range(num_starts):
        elapsed = time.time() - start_time
        if elapsed > total_time_budget:
            break

        # Allocate remaining time fairly among remaining starts
        remaining_time = total_time_budget - elapsed
        remaining_starts = num_starts - start
        time_per_start = remaining_time / remaining_starts

        assignment = greedy_initial_solution(randomized=(start > 0))
        assignment = local_search(assignment, time_per_start * 0.8)  # Use 80% for search, 20% buffer
        cost = solution_cost(assignment)

        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    return best_assignment
