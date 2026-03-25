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

    def compute_cost(assignment):
        """Compute total QAP cost for an assignment."""
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    def local_search_2opt(initial_assignment):
        """First-improvement 2-opt local search from given starting point."""
        assignment = initial_assignment[:]
        current_cost = compute_cost(assignment)

        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False

            for i in range(n):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 1, n):
                    # Compute cost delta of swapping positions i and j
                    assignment[i], assignment[j] = assignment[j], assignment[i]
                    new_cost = compute_cost(assignment)
                    assignment[i], assignment[j] = assignment[j], assignment[i]

                    delta = new_cost - current_cost
                    if delta < 0:  # First improvement
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        current_cost = new_cost
                        improved = True
                        break

                if improved:
                    break

        return assignment, current_cost

    def greedy_nn_assignment():
        """Greedy nearest-neighbor assignment based on flow/distance heuristic."""
        used_locations = set()
        assignment = [-1] * n
        facility_order = list(range(n))
        # Sort by total flow (facilities with high flow should be assigned first)
        facility_order.sort(key=lambda i: -sum(flow[i]))

        for facility in facility_order:
            best_loc = -1
            best_score = float('inf')

            for loc in range(n):
                if loc in used_locations:
                    continue

                # Estimate cost of assigning facility to loc
                # Consider flow to already-assigned facilities
                score = 0
                for other_facility in range(n):
                    if assignment[other_facility] != -1:
                        score += flow[facility][other_facility] * distance[loc][assignment[other_facility]]

                if score < best_score:
                    best_score = score
                    best_loc = loc

            assignment[facility] = best_loc
            used_locations.add(best_loc)

        return assignment

    start_time = time.time()
    time_limit = 55  # Leave margin for evaluation harness

    # Multi-start: try identity + greedy + random restarts
    best_assignment = list(range(n))
    best_cost = compute_cost(best_assignment)

    # Local search from identity
    assignment, cost = local_search_2opt(best_assignment)
    if cost < best_cost:
        best_assignment = assignment
        best_cost = cost

    # Local search from greedy initialization
    greedy = greedy_nn_assignment()
    assignment, cost = local_search_2opt(greedy)
    if cost < best_cost:
        best_assignment = assignment
        best_cost = cost

    # Random restarts - prioritize exploration with multiple restarts
    num_restarts = 6 if n < 70 else 4
    for restart in range(num_restarts):
        if time.time() - start_time >= time_limit:
            break

        current = list(range(n))
        random.shuffle(current)

        assignment, cost = local_search_2opt(current)
        if cost < best_cost:
            best_assignment = assignment
            best_cost = cost

    return best_assignment
