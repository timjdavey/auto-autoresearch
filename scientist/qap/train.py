"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: 2-opt local search with identity start.
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
    n = len(flow)
    if n == 0:
        return []
    if n == 1:
        return [0]

    def swap_cost_delta(assignment, i, j):
        """Cost change from swapping locations of facilities i and j."""
        delta = 0
        li, lj = assignment[i], assignment[j]
        for k in range(n):
            if k != i and k != j:
                lk = assignment[k]
                # Facility i: was lk, now lj
                delta += flow[i][k] * (distance[lj][lk] - distance[li][lk])
                delta += flow[k][i] * (distance[lk][lj] - distance[lk][li])
                # Facility j: was lk, now li
                delta += flow[j][k] * (distance[li][lk] - distance[lj][lk])
                delta += flow[k][j] * (distance[lk][li] - distance[lk][lj])
        # i-j interaction
        delta += flow[i][j] * (distance[lj][li] - distance[li][lj])
        delta += flow[j][i] * (distance[li][lj] - distance[lj][li])
        return delta

    def compute_cost(assignment):
        """Compute total cost for an assignment."""
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    def greedy_init():
        """Greedy initialization: assign facilities to minimize immediate costs."""
        assigned = [False] * n
        assignment = [0] * n
        cost_so_far = [[0] * n for _ in range(n)]  # cost_so_far[i][l] = cost of assigning facility i to location l

        # Precompute all facility-location assignment costs
        for i in range(n):
            for l in range(n):
                for k in range(n):
                    cost_so_far[i][l] += flow[i][k] * distance[l][l]  # placeholder

        # Greedy: assign facilities in order of total flow (high-flow first)
        flow_sums = [sum(flow[i]) for i in range(n)]
        facility_order = sorted(range(n), key=lambda i: -flow_sums[i])

        assigned_locs = [False] * n
        assignment = [-1] * n

        for i in facility_order:
            best_loc = -1
            best_cost_delta = float('inf')

            for l in range(n):
                if assigned_locs[l]:
                    continue

                # Cost of assigning facility i to location l
                cost_delta = 0
                for k in range(n):
                    if assignment[k] != -1:  # k already assigned
                        cost_delta += flow[i][k] * distance[l][assignment[k]]
                        cost_delta += flow[k][i] * distance[assignment[k]][l]

                if cost_delta < best_cost_delta:
                    best_cost_delta = cost_delta
                    best_loc = l

            assignment[i] = best_loc
            assigned_locs[best_loc] = True

        return assignment

    def or_opt_move_cost(assignment, i, j):
        """Cost change from moving facility i to position j."""
        if i == j:
            return 0
        n = len(assignment)
        assignment_copy = assignment[:]
        # Remove facility i and insert at position j
        facility = assignment_copy.pop(i)
        if j > i:
            j -= 1
        assignment_copy.insert(j, facility)

        # Compute cost difference
        old_cost = 0
        new_cost = 0
        for a in range(n):
            for b in range(n):
                old_cost += flow[a][b] * distance[assignment[a]][assignment[b]]
                new_cost += flow[a][b] * distance[assignment_copy[a]][assignment_copy[b]]
        return new_cost - old_cost

    def two_opt_search(initial_assignment, time_budget_remaining):
        """Run 2-opt local search from a given starting point."""
        assignment = initial_assignment[:]
        improved = True
        iterations = 0
        max_iterations = min(200, n * 5)
        start = time.time()

        while improved and iterations < max_iterations:
            if time.time() - start > time_budget_remaining:
                break

            improved = False
            iterations += 1

            for i in range(n):
                for j in range(i + 1, n):
                    delta = swap_cost_delta(assignment, i, j)
                    if delta < 0:
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        improved = True
                        break
                if improved:
                    break

        return assignment

    def or_opt_search(initial_assignment, time_budget_remaining):
        """Run Or-opt local search (single facility moves)."""
        assignment = initial_assignment[:]
        improved = True
        start = time.time()

        while improved:
            if time.time() - start > time_budget_remaining:
                break

            improved = False
            for i in range(n):
                for j in range(n):
                    if i != j:
                        delta = or_opt_move_cost(assignment, i, j)
                        if delta < 0:
                            # Apply move
                            facility = assignment.pop(i)
                            if j > i:
                                j -= 1
                            assignment.insert(j, facility)
                            improved = True
                            break
                if improved:
                    break

        return assignment

    # Try greedy + 2-opt + or-opt
    start_time = time.time()
    time_budget = 55

    assignment = greedy_init()
    assignment = two_opt_search(assignment, (time_budget - (time.time() - start_time)) * 0.7)
    assignment = or_opt_search(assignment, time_budget - (time.time() - start_time))

    return assignment
