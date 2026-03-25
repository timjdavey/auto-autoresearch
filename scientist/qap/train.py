"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


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

    def calculate_cost(assignment):
        cost = 0
        for i in range(n):
            for j in range(n):
                cost += flow[i][j] * distance[assignment[i]][assignment[j]]
        return cost

    def calculate_delta(assignment, i, j):
        """Calculate cost change when swapping facilities i and j."""
        cost_before = 0
        cost_after = 0
        for k in range(n):
            if k != i and k != j:
                cost_before += flow[i][k] * distance[assignment[i]][assignment[k]]
                cost_before += flow[k][i] * distance[assignment[k]][assignment[i]]
                cost_before += flow[j][k] * distance[assignment[j]][assignment[k]]
                cost_before += flow[k][j] * distance[assignment[k]][assignment[j]]

                cost_after += flow[i][k] * distance[assignment[j]][assignment[k]]
                cost_after += flow[k][i] * distance[assignment[k]][assignment[j]]
                cost_after += flow[j][k] * distance[assignment[i]][assignment[k]]
                cost_after += flow[k][j] * distance[assignment[k]][assignment[i]]

        cost_before += flow[i][j] * distance[assignment[i]][assignment[j]]
        cost_before += flow[j][i] * distance[assignment[j]][assignment[i]]

        cost_after += flow[i][j] * distance[assignment[j]][assignment[i]]
        cost_after += flow[j][i] * distance[assignment[i]][assignment[j]]

        return cost_after - cost_before

    def greedy_init(start_facility=0, flow_weighted=False):
        """Greedy construction heuristic starting from a specific facility.

        If flow_weighted=True, order facilities by total flow (high-flow first).
        This prioritizes assigning high-impact facilities to good locations.
        If flow_weighted=2, use reverse order (low-flow first) for diversification.
        """
        assignment = [-1] * n
        available = set(range(n))

        if flow_weighted == 1:
            # Order by sum of flows (descending) — high-flow facilities first
            flows = [sum(flow[i]) for i in range(n)]
            order = sorted(range(n), key=lambda i: -flows[i])
        elif flow_weighted == 2:
            # Reverse order — low-flow facilities first
            flows = [sum(flow[i]) for i in range(n)]
            order = sorted(range(n), key=lambda i: flows[i])
        else:
            # Original order starting from start_facility
            order = list(range(start_facility, n)) + list(range(start_facility))

        for facility in order:
            if assignment[facility] != -1:
                continue
            best_loc = None
            best_delta = float('inf')

            for loc in available:
                assignment[facility] = loc
                delta = 0
                for i in range(n):
                    if i != facility and assignment[i] != -1:
                        for j in range(n):
                            delta += flow[i][facility] * distance[assignment[i]][loc]
                            delta += flow[facility][i] * distance[loc][assignment[i]]
                delta += flow[facility][facility] * distance[loc][loc]

                if delta < best_delta:
                    best_delta = delta
                    best_loc = loc

            assignment[facility] = best_loc
            available.remove(best_loc)

        return assignment

    def random_init():
        """Random initialization."""
        assignment = list(range(n))
        random.shuffle(assignment)
        return assignment

    def local_search(assignment, ils_depth=6):
        """2-opt local search with first-improvement + iterated local search."""
        best_assignment = assignment[:]
        best_cost = calculate_cost(best_assignment)

        for iteration in range(ils_depth):  # ILS iterations with double-swap perturbations
            # 2-opt first-improvement
            improved = True
            while improved:
                improved = False
                for i in range(n):
                    for j in range(i + 1, n):
                        delta = calculate_delta(assignment, i, j)
                        if delta < -1e-9:
                            assignment[i], assignment[j] = assignment[j], assignment[i]
                            improved = True
                            break
                    if improved:
                        break

            # Check if this is better
            cost = calculate_cost(assignment)
            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment[:]

            # Perturbation: double random swap for stronger escape (ILS intensification)
            if iteration < ils_depth - 1:
                # First swap
                i = random.randint(0, n - 1)
                j = random.randint(0, n - 1)
                while j == i:
                    j = random.randint(0, n - 1)
                assignment[i], assignment[j] = assignment[j], assignment[i]

                # Second swap for stronger perturbation
                i = random.randint(0, n - 1)
                j = random.randint(0, n - 1)
                while j == i:
                    j = random.randint(0, n - 1)
                assignment[i], assignment[j] = assignment[j], assignment[i]

        return best_assignment

    # --- Multi-start: 1 greedy + adaptive random restarts ---
    best_assignment = None
    best_cost = float('inf')

    # Single greedy initialization
    assignment = greedy_init()
    assignment = local_search(assignment, ils_depth=7)
    cost = calculate_cost(assignment)
    best_assignment = assignment
    best_cost = cost

    # Run random restarts with adaptive count based on size
    if n <= 50:
        num_runs = 25
    elif n <= 60:
        num_runs = 16
    else:
        num_runs = 10

    for _ in range(num_runs):
        assignment = random_init()
        assignment = local_search(assignment, ils_depth=7)
        cost = calculate_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment
