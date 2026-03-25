"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: greedy construction + 2-opt local search.
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
    time_limit = 55  # 60s minus buffer

    best_assignment = list(range(n))
    best_cost = calculate_cost(flow, distance, best_assignment)

    # Multi-start with both greedy and nearest-neighbor construction
    # Reduced number of starts to ensure we stay within time budget
    num_greedy_starts = min(2, n)
    num_nn_starts = min(1, n)

    # Greedy construction starts
    for trial_num in range(num_greedy_starts):
        if time.time() - start_time > time_limit:
            break

        # Use greedy construction with different seeds for diversity
        assignment = greedy_construct(flow, distance, n, trial_num)

        # Best-improvement 2-opt local search for stronger local optima
        remaining_time = time_limit - (time.time() - start_time)
        if remaining_time > 2:
            assignment = or_opt(flow, distance, assignment, remaining_time * 0.8)

        cost = calculate_cost(flow, distance, assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Nearest-neighbor construction starts
    for trial_num in range(num_nn_starts):
        if time.time() - start_time > time_limit:
            break

        assignment = nearest_neighbor_construct(flow, distance, n, trial_num)

        # Best-improvement 2-opt local search for stronger local optima
        remaining_time = time_limit - (time.time() - start_time)
        if remaining_time > 2:
            assignment = or_opt(flow, distance, assignment, remaining_time * 0.8)

        cost = calculate_cost(flow, distance, assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment


def calculate_cost(flow: list[list[int]], distance: list[list[int]], assignment: list[int]) -> int:
    """Calculate QAP cost for a given assignment."""
    n = len(flow)
    cost = 0
    for i in range(n):
        for j in range(n):
            cost += flow[i][j] * distance[assignment[i]][assignment[j]]
    return cost


def nearest_neighbor_construct(flow: list[list[int]], distance: list[list[int]], n: int, seed: int) -> list[int]:
    """Nearest-neighbor construction: start from random facility, assign nearest unassigned facilities."""
    assignment = [-1] * n
    assigned = [False] * n
    used_locations = [False] * n

    # Start with a random facility based on seed
    current_facility = seed % n
    start_location = (seed // n) % n
    assignment[current_facility] = start_location
    assigned[current_facility] = True
    used_locations[start_location] = True

    # Greedily assign remaining facilities based on distance to already-assigned facilities
    for _ in range(n - 1):
        best_facility = -1
        best_location = -1
        best_cost = float('inf')

        for facility in range(n):
            if assigned[facility]:
                continue

            for location in range(n):
                if used_locations[location]:
                    continue

                # Cost of assigning this facility to this location
                cost = 0
                for i in range(n):
                    if assigned[i]:
                        cost += flow[facility][i] * distance[location][assignment[i]]
                        cost += flow[i][facility] * distance[assignment[i]][location]

                if cost < best_cost:
                    best_cost = cost
                    best_facility = facility
                    best_location = location

        if best_facility != -1:
            assignment[best_facility] = best_location
            assigned[best_facility] = True
            used_locations[best_location] = True

    return assignment


def greedy_construct(flow: list[list[int]], distance: list[list[int]], n: int, seed: int) -> list[int]:
    """Greedy construction: assign high-flow facilities first for better cost foundation."""
    assignment = [-1] * n
    assigned = [False] * n
    used_locations = [False] * n

    # Calculate total flow for each facility to prioritize high-flow facilities
    facility_flow = [sum(flow[i]) for i in range(n)]

    # Sort facilities by total flow (descending) with seed-based tie-breaking for diversity
    sorted_facilities = sorted(range(n), key=lambda i: (-facility_flow[i], i ^ seed))

    # Assign facilities in order of total flow (with seed-based randomization)
    for facility in sorted_facilities:
        best_location = -1
        best_increase = float('inf')

        # Cache assigned facilities and their locations for faster lookup
        assigned_list = [i for i in range(n) if assigned[i]]

        for location in range(n):
            if used_locations[location]:
                continue
            # Calculate cost increase using cached assigned list
            increase = 0
            for i in assigned_list:
                increase += flow[facility][i] * distance[location][assignment[i]]
                increase += flow[i][facility] * distance[assignment[i]][location]

            if increase < best_increase:
                best_increase = increase
                best_location = location

        if best_location != -1:
            assignment[facility] = best_location
            assigned[facility] = True
            used_locations[best_location] = True

    return assignment


def two_opt(flow: list[list[int]], distance: list[list[int]], assignment: list[int], time_limit: float) -> list[int]:
    """Apply 2-opt local search to improve assignment (first-improvement with delta cost)."""
    n = len(assignment)
    start_time = time.time()
    improved = True
    iteration = 0
    max_iterations = max(1, int(n / 2))  # Limit iterations for large problems

    while improved and time.time() - start_time < time_limit and iteration < max_iterations:
        improved = False
        iteration += 1

        # Check time more frequently for large problems
        if n > 50 and iteration % 2 == 0 and time.time() - start_time > time_limit:
            break

        for i in range(n):
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, n):
                # Calculate delta cost for swapping locations of facilities i and j
                delta = delta_cost(flow, distance, assignment, i, j)

                if delta < 0:
                    # Swap and continue (first-improvement)
                    assignment[i], assignment[j] = assignment[j], assignment[i]
                    improved = True
                    break

            if improved:
                break

    return assignment


def or_opt(flow: list[list[int]], distance: list[list[int]], assignment: list[int], time_limit: float) -> list[int]:
    """Apply best-improvement 2-opt (exhaustive local search) for fine-tuning."""
    n = len(assignment)
    start_time = time.time()
    improved = True

    while improved and time.time() - start_time < time_limit:
        improved = False
        best_delta = 0
        best_i = -1
        best_j = -1

        for i in range(n):
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, n):
                delta = delta_cost(flow, distance, assignment, i, j)
                if delta < best_delta:
                    best_delta = delta
                    best_i = i
                    best_j = j

        if best_i != -1:
            assignment[best_i], assignment[best_j] = assignment[best_j], assignment[best_i]
            improved = True

    return assignment


def three_opt(flow: list[list[int]], distance: list[list[int]], assignment: list[int], time_limit: float) -> list[int]:
    """Apply 3-opt local search for deeper exploration (limited random iterations)."""
    n = len(assignment)
    if n < 4:
        return assignment

    start_time = time.time()
    best_cost = calculate_cost(flow, distance, assignment)
    num_trials = min(50, n * 2)  # Limit trials to avoid timeout

    for trial in range(num_trials):
        if time.time() - start_time > time_limit:
            break

        # Randomly select 3 facilities
        i = random.randint(0, n - 1)
        j = random.randint(0, n - 1)
        k = random.randint(0, n - 1)

        if len({i, j, k}) != 3:
            continue

        # Try different 3-opt moves (there are 8 possible reconnections)
        for move_type in range(4):
            current = assignment[:]
            if move_type == 0:
                # Reverse segment between i and j
                if i > j:
                    i, j = j, i
                current[i:j + 1] = reversed(current[i:j + 1])
            elif move_type == 1:
                # Reverse segment between j and k
                if j > k:
                    j, k = k, j
                current[j:k + 1] = reversed(current[j:k + 1])
            elif move_type == 2:
                # Swap segments
                if i > j:
                    i, j = j, i
                if j > k:
                    j, k = k, j
                current[i:j + 1], current[j:k + 1] = current[j:k + 1][:], current[i:j + 1][:]
            else:
                continue

            cost = calculate_cost(flow, distance, current)
            if cost < best_cost:
                best_cost = cost
                assignment = current

    return assignment


def delta_cost(flow: list[list[int]], distance: list[list[int]], assignment: list[int], i: int, j: int) -> int:
    """Calculate delta cost (new_cost - current_cost) for swapping facilities i and j."""
    n = len(assignment)
    loc_i = assignment[i]
    loc_j = assignment[j]

    delta = 0
    for k in range(n):
        if k == i or k == j:
            continue
        loc_k = assignment[k]
        # Current cost components involving i
        current_i = flow[i][k] * distance[loc_i][loc_k] + flow[k][i] * distance[loc_k][loc_i]
        # New cost after swap
        new_i = flow[i][k] * distance[loc_j][loc_k] + flow[k][i] * distance[loc_k][loc_j]
        delta += new_i - current_i

        # Current cost components involving j
        current_j = flow[j][k] * distance[loc_j][loc_k] + flow[k][j] * distance[loc_k][loc_j]
        # New cost after swap
        new_j = flow[j][k] * distance[loc_i][loc_k] + flow[k][j] * distance[loc_k][loc_i]
        delta += new_j - current_j

    # Add the cross term between i and j
    current_cross = flow[i][j] * distance[loc_i][loc_j] + flow[j][i] * distance[loc_j][loc_i]
    new_cross = flow[i][j] * distance[loc_j][loc_i] + flow[j][i] * distance[loc_i][loc_j]
    delta += new_cross - current_cross

    return delta
