"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: multi-start greedy + 1-opt local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time
import math


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

    # Time tracking
    start_time = time.time()
    time_limit = 59  # Safety margin: 59s out of 60s

    # Compute cost for a given assignment
    def cost(assignment):
        total = 0
        for i in range(n):
            pi = assignment[i]
            for j in range(n):
                total += flow[i][j] * distance[pi][assignment[j]]
        return total

    def time_remaining():
        return (start_time + time_limit) - time.time()

    def solve_once():
        """Run one complete solve pass with multi-start greedy + SA + polish"""

    # Greedy construction: facility-first (assign each facility to best location)
    def build_greedy_facility_first(fac_order):
        assignment = [-1] * n
        used = [False] * n

        for fac in fac_order:
            # Find best location for this facility
            best_loc = -1
            best_cost = float('inf')
            for loc in range(n):
                if used[loc]:
                    continue
                inc_cost = 0
                for j in range(n):
                    if assignment[j] != -1:
                        inc_cost += flow[fac][j] * distance[loc][assignment[j]]
                        inc_cost += flow[j][fac] * distance[assignment[j]][loc]
                if inc_cost < best_cost:
                    best_cost = inc_cost
                    best_loc = loc

            assignment[fac] = best_loc
            used[best_loc] = True

        return assignment

    # Greedy construction: location-first (assign each location to best facility)
    def build_greedy_location_first(loc_order):
        assignment = [-1] * n
        used = [False] * n

        for loc in loc_order:
            # Find best facility for this location
            best_fac = -1
            best_cost = float('inf')
            for fac in range(n):
                if used[fac]:
                    continue
                inc_cost = 0
                for j in range(n):
                    if assignment[j] != -1:
                        inc_cost += flow[fac][j] * distance[loc][assignment[j]]
                        inc_cost += flow[j][fac] * distance[assignment[j]][loc]
                if inc_cost < best_cost:
                    best_cost = inc_cost
                    best_fac = fac

            assignment[best_fac] = loc
            used[best_fac] = True

        return assignment

    # Greedy construction with random tie-breaking
    def build_greedy_facility_first_random_ties(fac_order, random_seed):
        random.seed(random_seed)
        assignment = [-1] * n
        used = [False] * n

        for fac in fac_order:
            # Collect candidates within 10% of best cost
            candidates = []
            best_cost_found = float('inf')
            for loc in range(n):
                if used[loc]:
                    continue
                inc_cost = 0
                for j in range(n):
                    if assignment[j] != -1:
                        inc_cost += flow[fac][j] * distance[loc][assignment[j]]
                        inc_cost += flow[j][fac] * distance[assignment[j]][loc]
                candidates.append((inc_cost, loc))
                if inc_cost < best_cost_found:
                    best_cost_found = inc_cost

            # Filter to top candidates (within 10% margin)
            threshold = best_cost_found * 1.1
            top_candidates = [loc for cost, loc in candidates if cost <= threshold]

            # Randomly pick from top candidates
            if top_candidates:
                best_loc = random.choice(top_candidates)
            else:
                best_loc = min(candidates, key=lambda x: x[0])[1]

            assignment[fac] = best_loc
            used[best_loc] = True

        return assignment

    # Multi-start: facility-first and location-first with different orderings
    best_assignment = None
    best_cost_val = float('inf')

    # Standard facility-first order (highest demand first)
    fac_order_std = list(range(n))
    fac_order_std.sort(key=lambda fac: sum(flow[fac][j] for j in range(n)), reverse=True)
    assignment = build_greedy_facility_first(fac_order_std)
    assignment_cost = cost(assignment)
    if assignment_cost < best_cost_val:
        best_cost_val = assignment_cost
        best_assignment = assignment

    # Random facility orderings (standard best-fit) - increased diversity
    for seed in [42, 123, 456, 789, 999, 2024, 3141, 2718]:
        if time_remaining() < 6:
            break
        random.seed(seed)
        fac_order_rand = list(range(n))
        random.shuffle(fac_order_rand)
        assignment = build_greedy_facility_first(fac_order_rand)
        assignment_cost = cost(assignment)
        if assignment_cost < best_cost_val:
            best_cost_val = assignment_cost
            best_assignment = assignment

    # Location-first ordering (explore different basin)
    if time_remaining() > 8:
        loc_order_std = list(range(n))
        loc_order_std.sort(key=lambda loc: sum(distance[loc][k] for k in range(n)), reverse=True)
        assignment = build_greedy_location_first(loc_order_std)
        assignment_cost = cost(assignment)
        if assignment_cost < best_cost_val:
            best_cost_val = assignment_cost
            best_assignment = assignment

    # Random location-first ordering
    if time_remaining() > 8:
        random.seed(999)
        loc_order_rand = list(range(n))
        random.shuffle(loc_order_rand)
        assignment = build_greedy_location_first(loc_order_rand)
        assignment_cost = cost(assignment)
        if assignment_cost < best_cost_val:
            best_cost_val = assignment_cost
            best_assignment = assignment

    # Random tie-breaking variant (explores different regions)
    for seed in [456, 789]:
        if time_remaining() < 8:
            break
        fac_order_std2 = list(range(n))
        fac_order_std2.sort(key=lambda fac: sum(flow[fac][j] for j in range(n)), reverse=True)
        assignment = build_greedy_facility_first_random_ties(fac_order_std2, seed)
        assignment_cost = cost(assignment)
        if assignment_cost < best_cost_val:
            best_cost_val = assignment_cost
            best_assignment = assignment

    assignment = best_assignment

    # Simulated Annealing: escape local optima
    current_cost = cost(assignment)
    best_cost_sa = current_cost
    best_assignment_sa = assignment[:]

    # Temperature schedule: start high enough to explore
    initial_temp = current_cost * 0.01  # 1% of current cost as temperature scale
    temp = initial_temp
    cooling_rate = 0.98  # Slightly slower cooling from 0.975
    iteration = 0
    max_iterations = 1500 if n > 60 else 3000

    while iteration < max_iterations and time_remaining() > 5 and temp > 0.001:
        iteration += 1

        # Random 1-opt move: swap two facilities
        i, j = random.sample(range(n), 2)
        assignment[i], assignment[j] = assignment[j], assignment[i]
        new_cost = cost(assignment)

        # Metropolis criterion: accept if better or with probability
        delta = new_cost - current_cost
        if delta < 0 or random.random() < math.exp(-delta / temp):
            current_cost = new_cost
            if new_cost < best_cost_sa:
                best_cost_sa = new_cost
                best_assignment_sa = assignment[:]
        else:
            # Reject: revert
            assignment[i], assignment[j] = assignment[j], assignment[i]

        # Cool down every N iterations
        if iteration % 50 == 0:
            temp *= cooling_rate

    # Use best solution found by SA
    assignment = best_assignment_sa

    # Final 1-opt polish: clean up with first-improvement
    def polish_1opt(assignment):
        improved = True
        polish_iterations = 0
        while improved and polish_iterations < 200 and time_remaining() > 1:
            improved = False
            polish_iterations += 1
            current_cost = cost(assignment)
            for i in range(n):
                for j in range(i + 1, n):
                    assignment[i], assignment[j] = assignment[j], assignment[i]
                    new_cost = cost(assignment)
                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                        break
                    else:
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                if improved:
                    break
        return assignment

    # Run initial polish if time permits
    if time_remaining() > 3:
        assignment = polish_1opt(assignment)

    # Perturbation + re-polish cycles to escape local optima
    best_overall = assignment[:]
    best_overall_cost = cost(assignment)

    perturbation_rounds = 0
    while time_remaining() > 4 and perturbation_rounds < 6:
        perturbation_rounds += 1

        # Random 3-move perturbation: balanced disruption
        perturbed = assignment[:]
        for _ in range(3):
            if n > 1:
                i, j = random.sample(range(n), 2)
                perturbed[i], perturbed[j] = perturbed[j], perturbed[i]

        # Re-polish the perturbed solution
        assignment = perturbed
        assignment = polish_1opt(assignment)

        # Track best found
        assignment_cost = cost(assignment)
        if assignment_cost < best_overall_cost:
            best_overall_cost = assignment_cost
            best_overall = assignment[:]

    assignment = best_overall
    return assignment
