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
    time_limit = 58  # Tighter margin: 58s to leave 2s for cleanup

    # Multi-start: try 4 different initialization strategies
    best_assignment = None
    best_cost = float('inf')

    strategies = [
        'high_flow',      # Best strategy (35% time)
        'pair_based',     # Pair-based (35% time)
        'random',         # Random facility order (15% time)
        'high_degree',    # Facilities with most connections (15% time)
    ]

    # Allocate time proportionally
    time_allocations = {
        'high_flow': time_limit * 0.35,
        'pair_based': time_limit * 0.35,
        'random': time_limit * 0.15,
        'high_degree': time_limit * 0.15,
    }

    for strategy in strategies:
        if time.time() - start_time > time_limit - 2:  # Stop if running out of time
            break

        start_budget = time_allocations[strategy] * 0.95  # Use 95% of allocated time per start
        phase_start = time.time()

        # Greedy construction with chosen strategy
        assignment = greedy_construction(flow, distance, n, strategy)

        # First-improvement 1-opt
        assignment = local_search_first_improvement(flow, distance, assignment, n, phase_start, start_budget)

        # 2-opt local search — increased iterations for better exploitation
        assignment = local_search_2opt(flow, distance, assignment, n, phase_start, start_budget)

        # 3-opt for small instances (rand50a, rand60a)
        if n <= 60:
            assignment = local_search_3opt(flow, distance, assignment, n, phase_start, start_budget)

        # Track best solution across all starts
        cost = compute_cost(flow, distance, assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment if best_assignment else [0] * n


def pair_based_greedy_construction(flow, distance, n):
    """Pair-based greedy: start with highest mutual flow pair, then extend."""
    # Find pair with highest mutual flow
    best_pair = None
    best_pair_flow = -1
    for i in range(n):
        for j in range(i + 1, n):
            mutual = flow[i][j] + flow[j][i]
            if mutual > best_pair_flow:
                best_pair_flow = mutual
                best_pair = (i, j)

    if best_pair is None:
        # Fallback to high_flow
        return greedy_construction(flow, distance, n, 'high_flow')

    assignment_dict = {}
    used_locations = set()

    # Assign the pair to best two locations
    i, j = best_pair
    best_cost = float('inf')
    best_locs = None
    for loc_i in range(n):
        for loc_j in range(n):
            if loc_i == loc_j:
                continue
            cost = flow[i][j] * distance[loc_i][loc_j] + flow[j][i] * distance[loc_j][loc_i]
            if cost < best_cost:
                best_cost = cost
                best_locs = (loc_i, loc_j)

    if best_locs:
        assignment_dict[i] = best_locs[0]
        assignment_dict[j] = best_locs[1]
        used_locations.add(best_locs[0])
        used_locations.add(best_locs[1])

    # Greedily assign remaining facilities
    remaining = set(range(n)) - {i, j}
    while remaining:
        best_facility = None
        best_location = None
        best_loc_cost = float('inf')

        for facility in remaining:
            for loc in range(n):
                if loc in used_locations:
                    continue
                cost = 0
                for assigned_f, assigned_l in assignment_dict.items():
                    cost += flow[facility][assigned_f] * distance[loc][assigned_l]
                    cost += flow[assigned_f][facility] * distance[assigned_l][loc]
                if cost < best_loc_cost:
                    best_loc_cost = cost
                    best_facility = facility
                    best_location = loc

        if best_facility is not None:
            assignment_dict[best_facility] = best_location
            used_locations.add(best_location)
            remaining.remove(best_facility)
        else:
            break

    # Assign any remaining unassigned facilities to remaining locations
    for fac in remaining:
        for loc in range(n):
            if loc not in used_locations:
                assignment_dict[fac] = loc
                used_locations.add(loc)
                break

    assignment = [assignment_dict.get(i, 0) for i in range(n)]
    return assignment


def greedy_construction(flow, distance, n, strategy='high_flow'):
    """Greedy construction: assign facilities in order based on strategy."""

    if strategy == 'high_flow':
        # Order facilities by total flow (descending)
        facility_order = sorted(range(n), key=lambda i: sum(flow[i]), reverse=True)
    elif strategy == 'high_degree':
        # Order facilities by number of significant connections (non-zero flow)
        facility_order = sorted(range(n), key=lambda i: sum(1 for j in range(n) if flow[i][j] > 0), reverse=True)
    elif strategy == 'random':
        # Random ordering
        facility_order = list(range(n))
        random.shuffle(facility_order)
    elif strategy == 'pair_based':
        # Pair-based: start with highest-flow pair, then extend greedily
        return pair_based_greedy_construction(flow, distance, n)
    else:
        # Default to high_flow
        facility_order = sorted(range(n), key=lambda i: sum(flow[i]), reverse=True)

    assignment_dict = {}
    used_locations = set()

    for i in facility_order:
        best_loc = -1
        best_cost = float('inf')
        for loc in range(n):
            if loc in used_locations:
                continue
            # Cost of assigning facility i to location loc
            cost = 0
            for j in range(n):
                if j in assignment_dict:
                    cost += flow[i][j] * distance[loc][assignment_dict[j]]
                    cost += flow[j][i] * distance[assignment_dict[j]][loc]
            if cost < best_cost:
                best_cost = cost
                best_loc = loc
        assignment_dict[i] = best_loc
        used_locations.add(best_loc)

    # Convert dict to list indexed by facility
    assignment = [assignment_dict[i] for i in range(n)]
    return assignment


def local_search_first_improvement(flow, distance, assignment, n, start_time, time_limit):
    """First-improvement 1-opt: accept first improving swap."""
    improved = True
    iterations = 0
    max_iterations = 250

    while improved and iterations < max_iterations:
        if time.time() - start_time > time_limit:
            break

        improved = False
        iterations += 1
        old_total_cost = compute_cost(flow, distance, assignment)

        for i in range(n):
            for j in range(i + 1, n):
                assignment[i], assignment[j] = assignment[j], assignment[i]
                new_cost = compute_cost(flow, distance, assignment)
                if new_cost < old_total_cost:
                    improved = True
                    break
                else:
                    assignment[i], assignment[j] = assignment[j], assignment[i]

            if improved:
                break

    return assignment


def local_search_2opt(flow, distance, assignment, n, start_time, time_limit):
    """2-opt local search: swap pairs of facilities at positions i and j."""
    improved = True
    iterations = 0
    max_iterations = 100  # Increased for deeper exploration

    while improved and iterations < max_iterations:
        if time.time() - start_time > time_limit:
            break

        improved = False
        iterations += 1
        old_total_cost = compute_cost(flow, distance, assignment)

        # Try swapping pairs of facilities (proper 2-opt: swap positions i and j)
        for i in range(n):
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, n):
                # Swap facilities at positions i and j
                assignment[i], assignment[j] = assignment[j], assignment[i]
                new_cost = compute_cost(flow, distance, assignment)
                if new_cost < old_total_cost:
                    improved = True
                    old_total_cost = new_cost
                    break
                else:
                    assignment[i], assignment[j] = assignment[j], assignment[i]

            if improved:
                break

    return assignment


def local_search_3opt(flow, distance, assignment, n, start_time, time_limit):
    """3-opt local search: swap triples of facilities at positions i, j, k."""
    improved = True
    iterations = 0
    max_iterations = 50  # Increased for deeper exploration on small instances

    while improved and iterations < max_iterations:
        if time.time() - start_time > time_limit:
            break

        improved = False
        iterations += 1
        old_total_cost = compute_cost(flow, distance, assignment)

        # Try swapping triples of facilities
        for i in range(n):
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    # Swap three facilities: assignment[i], assignment[j], assignment[k]
                    # Try one rotation: (i,j,k) -> (j,k,i)
                    temp_i, temp_j, temp_k = assignment[i], assignment[j], assignment[k]
                    assignment[i], assignment[j], assignment[k] = temp_j, temp_k, temp_i
                    new_cost = compute_cost(flow, distance, assignment)
                    if new_cost < old_total_cost:
                        improved = True
                        old_total_cost = new_cost
                    else:
                        # Revert and try alternative rotation: (i,j,k) -> (k,i,j)
                        assignment[i], assignment[j], assignment[k] = temp_i, temp_j, temp_k
                        assignment[i], assignment[j], assignment[k] = temp_k, temp_i, temp_j
                        new_cost = compute_cost(flow, distance, assignment)
                        if new_cost < old_total_cost:
                            improved = True
                            old_total_cost = new_cost
                        else:
                            # Revert to original
                            assignment[i], assignment[j], assignment[k] = temp_i, temp_j, temp_k

                    if improved:
                        break

                if improved:
                    break

            if improved:
                break

    return assignment


def compute_cost(flow, distance, assignment):
    """Compute QAP cost for a given assignment."""
    n = len(flow)
    cost = 0
    for i in range(n):
        pi = assignment[i]
        for j in range(n):
            cost += flow[i][j] * distance[pi][assignment[j]]
    return cost
