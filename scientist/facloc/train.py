"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: multi-start greedy + local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import math


def _solve_greedy_client_first(opening_costs: list[int], assign_costs: list[list[int]],
                               seed: int) -> list[int]:
    """Greedy: assign each client to cheapest facility (with random tie-breaking)."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    assignment = []
    for j in range(n_clients):
        costs = [(assign_costs[i][j], i) for i in range(n_facilities)]
        costs.sort()
        min_cost = costs[0][0]
        best_facilities = [i for cost, i in costs if cost == min_cost]
        best_fac = random.choice(best_facilities) if best_facilities else 0
        assignment.append(best_fac)
    return assignment


def _solve_facility_first(opening_costs: list[int], assign_costs: list[list[int]],
                          seed: int) -> list[int]:
    """Facility-first with cost-weighted ordering."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    # Sort facilities by opening cost
    fac_order = sorted(range(n_facilities), key=lambda i: opening_costs[i])

    # Assign all clients to cheapest facility first, then refine
    assignment = [fac_order[0]] * n_clients

    # Try opening additional facilities and reassigning clients
    open_facilities = {fac_order[0]}

    for fac_idx in fac_order[1:]:
        open_facilities.add(fac_idx)

        # Try reassigning clients to new facility if it improves
        for j in range(n_clients):
            best_fac = min(open_facilities, key=lambda f: assign_costs[f][j])
            assignment[j] = best_fac

        # Check if this facility opening improved overall cost
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        if len(open_facilities) > 1:
            test_open = open_facilities - {fac_idx}
            test_cost = sum(opening_costs[i] for i in test_open)
            test_cost += sum(assign_costs[min(test_open, key=lambda f: assign_costs[f][j])][j]
                           for j in range(n_clients))
            if test_cost < current_cost:
                open_facilities.remove(fac_idx)
                for j in range(n_clients):
                    best_fac = min(open_facilities, key=lambda f: assign_costs[f][j])
                    assignment[j] = best_fac

    return assignment


def _solve_facility_load_balanced(opening_costs: list[int], assign_costs: list[list[int]],
                                   seed: int, weight: float = 1.0) -> list[int]:
    """Facility ordering by cost-to-benefit ratio (load-balanced)."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    # Compute average assignment cost per facility
    avg_cost = [sum(assign_costs[i]) / n_clients for i in range(n_facilities)]

    # Sort by cost-weighted heuristic: (weight * opening_cost) / avg_assignment_cost
    # Lower ratio = better value
    fac_order = sorted(range(n_facilities),
                      key=lambda i: (weight * opening_costs[i]) / max(1, avg_cost[i]))

    # Start with first facility, expand as needed
    assignment = [fac_order[0]] * n_clients
    open_facilities = {fac_order[0]}

    for fac_idx in fac_order[1:]:
        open_facilities.add(fac_idx)

        # Reassign clients
        for j in range(n_clients):
            best_fac = min(open_facilities, key=lambda f: assign_costs[f][j])
            assignment[j] = best_fac

        # Check if opening helped
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        if len(open_facilities) > 1:
            test_open = open_facilities - {fac_idx}
            test_cost = sum(opening_costs[i] for i in test_open)
            test_cost += sum(assign_costs[min(test_open, key=lambda f: assign_costs[f][j])][j]
                           for j in range(n_clients))
            if test_cost < current_cost:
                open_facilities.remove(fac_idx)
                for j in range(n_clients):
                    best_fac = min(open_facilities, key=lambda f: assign_costs[f][j])
                    assignment[j] = best_fac

    return assignment


def _solve_facility_load_balanced_w0_5(opening_costs: list[int], assign_costs: list[list[int]],
                                        seed: int) -> list[int]:
    """Load-balanced with weight 0.5 for opening cost."""
    return _solve_facility_load_balanced(opening_costs, assign_costs, seed, weight=0.5)


def _solve_facility_load_balanced_w0_7(opening_costs: list[int], assign_costs: list[list[int]],
                                        seed: int) -> list[int]:
    """Load-balanced with weight 0.7 for opening cost."""
    return _solve_facility_load_balanced(opening_costs, assign_costs, seed, weight=0.7)


def _solve_facility_load_balanced_w0_3(opening_costs: list[int], assign_costs: list[list[int]],
                                        seed: int) -> list[int]:
    """Load-balanced with weight 0.3 for opening cost."""
    return _solve_facility_load_balanced(opening_costs, assign_costs, seed, weight=0.3)


def _solve_random_assignment(opening_costs: list[int], assign_costs: list[list[int]],
                            seed: int) -> list[int]:
    """Purely random initialization: assign each client randomly."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    return [random.randint(0, n_facilities - 1) for _ in range(n_clients)]


def _solve_savings_based(opening_costs: list[int], assign_costs: list[list[int]],
                        seed: int) -> list[int]:
    """Savings algorithm: open facilities that maximize cost savings."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    # Start with cheapest facility
    cheapest = min(range(n_facilities), key=lambda i: opening_costs[i])
    open_facilities = {cheapest}
    assignment = [cheapest] * n_clients

    # Greedily add facilities with highest savings
    for _ in range(n_facilities - 1):
        best_saving = 0
        best_fac = None

        for fac in range(n_facilities):
            if fac in open_facilities:
                continue

            # Compute saving: cost reduction - opening cost
            test_open = open_facilities | {fac}
            test_assign = [min(test_open, key=lambda f: assign_costs[f][j]) for j in range(n_clients)]
            test_cost = sum(opening_costs[i] for i in test_open)
            test_cost += sum(assign_costs[test_assign[j]][j] for j in range(n_clients))

            curr_cost = sum(opening_costs[i] for i in open_facilities)
            curr_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

            saving = curr_cost - test_cost
            if saving > best_saving:
                best_saving = saving
                best_fac = fac

        if best_fac is None:
            break

        open_facilities.add(best_fac)
        assignment = [min(open_facilities, key=lambda f: assign_costs[f][j]) for j in range(n_clients)]

    return assignment


def _solve_greedy_cost_driven(opening_costs: list[int], assign_costs: list[list[int]],
                              seed: int) -> list[int]:
    """Greedy: directly minimize total cost by opening facilities incrementally."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    # Start with cheapest facility only
    best_idx = min(range(n_facilities), key=lambda i: opening_costs[i])
    open_facs = {best_idx}

    # Assign all clients to best facility initially
    assignment = [best_idx] * n_clients

    # Greedily add facilities if they reduce total cost
    for _ in range(n_facilities - 1):
        best_gain = 0
        best_fac = None

        # Try adding each unopened facility
        for fac in range(n_facilities):
            if fac in open_facs:
                continue

            # Compute cost with this facility added
            test_open = open_facs | {fac}
            test_assign = [min(test_open, key=lambda f: assign_costs[f][j]) for j in range(n_clients)]
            test_cost = sum(opening_costs[i] for i in test_open)
            test_cost += sum(assign_costs[test_assign[j]][j] for j in range(n_clients))

            # Current cost
            curr_cost = sum(opening_costs[i] for i in open_facs)
            curr_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

            gain = curr_cost - test_cost
            if gain > best_gain:
                best_gain = gain
                best_fac = fac

        if best_fac is None:
            break

        open_facs.add(best_fac)
        assignment = [min(open_facs, key=lambda f: assign_costs[f][j]) for j in range(n_clients)]

    return assignment


def _facility_closing_phase(opening_costs: list[int], assign_costs: list[list[int]],
                           assignment: list[int]) -> list[int]:
    """Aggressively close facilities that don't improve cost."""
    assignment = assignment[:]  # Copy
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    open_facilities = set(assignment)

    # Try closing each facility and reassigning clients
    for fac_to_close in sorted(open_facilities):
        if len(open_facilities) <= 1:
            break

        # Reassign clients from this facility to best remaining facility
        test_open = open_facilities - {fac_to_close}
        test_assignment = assignment[:]
        for j in range(n_clients):
            if assignment[j] == fac_to_close:
                test_assignment[j] = min(test_open, key=lambda f: assign_costs[f][j])

        # Compute cost before and after
        open_facilities_old = set(assignment)
        cost_old = sum(opening_costs[i] for i in open_facilities_old)
        cost_old += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        cost_new = sum(opening_costs[i] for i in test_open)
        cost_new += sum(assign_costs[test_assignment[j]][j] for j in range(n_clients))

        # If closing improves, keep it
        if cost_new < cost_old:
            assignment = test_assignment
            open_facilities = test_open

    return assignment


def _local_search_1opt(opening_costs: list[int], assign_costs: list[list[int]],
                       assignment: list[int]) -> list[int]:
    """1-opt local search: move clients to improve total cost (best-improvement)."""
    assignment = assignment[:]  # Copy
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    improved = True
    iterations = 0
    max_iterations = 1000

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Compute current cost
        open_facilities = set(assignment)
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        best_move = None
        best_move_cost = current_cost

        # Try moving each client to find the best move
        for j in range(n_clients):
            current_fac = assignment[j]

            # Try all other facilities
            for new_fac in range(n_facilities):
                if new_fac == current_fac:
                    continue

                # Compute new cost if we move client j to new_fac
                assignment[j] = new_fac
                new_open = set(assignment)
                new_cost = sum(opening_costs[i] for i in new_open)
                new_cost += sum(assign_costs[assignment[c]][c] for c in range(n_clients))

                # If improvement, track as best move so far
                if new_cost < best_move_cost:
                    best_move_cost = new_cost
                    best_move = (j, new_fac)

                assignment[j] = current_fac

        # Apply best move if found
        if best_move:
            j, new_fac = best_move
            assignment[j] = new_fac
            improved = True

    return assignment


def _simulated_annealing(opening_costs: list[int], assign_costs: list[list[int]],
                        assignment: list[int], max_iterations: int = 500, seed: int = 0) -> list[int]:
    """Simulated annealing to escape local optima."""
    random.seed(seed)
    assignment = assignment[:]  # Copy
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    # Compute initial cost
    open_facilities = set(assignment)
    current_cost = sum(opening_costs[i] for i in open_facilities)
    current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

    best_assignment = assignment[:]
    best_cost = current_cost

    # SA parameters
    temperature = 10.0
    cooling_rate = 0.95
    min_temp = 0.01

    iteration = 0
    while temperature > min_temp and iteration < max_iterations:
        iteration += 1

        # Generate a neighbor by moving a random client
        j = random.randint(0, n_clients - 1)
        old_fac = assignment[j]
        new_fac = random.randint(0, n_facilities - 1)

        if new_fac == old_fac:
            continue

        # Compute new cost
        assignment[j] = new_fac
        open_facilities = set(assignment)
        new_cost = sum(opening_costs[i] for i in open_facilities)
        new_cost += sum(assign_costs[assignment[c]][c] for c in range(n_clients))

        # Accept or reject move
        delta = new_cost - current_cost
        if delta < 0 or random.random() < math.exp(-delta / max(temperature, 0.01)):
            # Accept the move
            current_cost = new_cost
            if new_cost < best_cost:
                best_cost = new_cost
                best_assignment = assignment[:]
        else:
            # Reject the move
            assignment[j] = old_fac

        temperature *= cooling_rate

    return best_assignment


def _perturbation(assignment: list[int], n_facilities: int, strength: int = 3) -> list[int]:
    """Perturb assignment by moving k random clients to random facilities."""
    assignment = assignment[:]
    n_clients = len(assignment)
    for _ in range(min(strength, n_clients)):
        j = random.randint(0, n_clients - 1)
        assignment[j] = random.randint(0, n_facilities - 1)
    return assignment


def _iterated_local_search(opening_costs: list[int], assign_costs: list[list[int]],
                          initial_assignment: list[int], max_iterations: int = 10,
                          seed: int = 0) -> list[int]:
    """Iterated Local Search: aggressive perturbation to escape tight local optima."""
    random.seed(seed)
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    def compute_cost(assignment):
        open_facs = set(assignment)
        cost = sum(opening_costs[i] for i in open_facs)
        cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))
        return cost

    best_assignment = initial_assignment[:]
    best_cost = compute_cost(best_assignment)

    current_assignment = best_assignment[:]
    current_cost = best_cost

    for iteration in range(max_iterations):
        # Aggressive perturbation: move 15-25% of clients to random facilities
        strength = max(3, n_clients // (8 - iteration % 4))  # Gradually increase perturbation
        perturbed = _perturbation(current_assignment, n_facilities, strength=strength)

        # Re-optimize with 1-opt
        perturbed = _local_search_1opt_limited(opening_costs, assign_costs, perturbed, max_iter=500)

        perturbed_cost = compute_cost(perturbed)

        # Strict acceptance: only accept if equal or better
        if perturbed_cost <= current_cost:
            current_assignment = perturbed
            current_cost = perturbed_cost

            if perturbed_cost < best_cost:
                best_cost = perturbed_cost
                best_assignment = perturbed[:]

    return best_assignment


def _local_search_1opt_limited(opening_costs: list[int], assign_costs: list[list[int]],
                               assignment: list[int], max_iter: int = 500) -> list[int]:
    """1-opt with iteration limit for fast re-optimization in ILS."""
    assignment = assignment[:]
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    improved = True
    iterations = 0

    while improved and iterations < max_iter:
        improved = False
        iterations += 1

        open_facilities = set(assignment)
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        best_move = None
        best_move_cost = current_cost

        for j in range(n_clients):
            current_fac = assignment[j]
            for new_fac in range(n_facilities):
                if new_fac == current_fac:
                    continue

                assignment[j] = new_fac
                new_open = set(assignment)
                new_cost = sum(opening_costs[i] for i in new_open)
                new_cost += sum(assign_costs[assignment[c]][c] for c in range(n_clients))

                if new_cost < best_move_cost:
                    best_move_cost = new_cost
                    best_move = (j, new_fac)

                assignment[j] = current_fac

        if best_move:
            j, new_fac = best_move
            assignment[j] = new_fac
            improved = True

    return assignment


def _local_search_3opt_limited(opening_costs: list[int], assign_costs: list[list[int]],
                                assignment: list[int], max_iterations: int = 100) -> list[int]:
    """3-opt: swap triples of clients. For small instances to escape plateaus."""
    assignment = assignment[:]  # Copy
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Compute current cost
        open_facilities = set(assignment)
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        # Try swapping three clients
        for j1 in range(min(n_clients, 20)):  # Expanded search for small instances
            for j2 in range(j1 + 1, min(n_clients, j1 + 20)):
                for j3 in range(j2 + 1, min(n_clients, j2 + 20)):
                    # Try different facility combinations
                    old_f1, old_f2, old_f3 = assignment[j1], assignment[j2], assignment[j3]

                    for new_f1 in range(n_facilities):
                        for new_f2 in range(n_facilities):
                            assignment[j1] = new_f1
                            assignment[j2] = new_f2
                            assignment[j3] = new_f1

                            new_open = set(assignment)
                            new_cost = sum(opening_costs[i] for i in new_open)
                            new_cost += sum(assign_costs[assignment[c]][c] for c in range(n_clients))

                            if new_cost < current_cost:
                                current_cost = new_cost
                                improved = True
                                break

                            assignment[j1] = old_f1
                            assignment[j2] = old_f2
                            assignment[j3] = old_f3

                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return assignment


def _local_search_2opt(opening_costs: list[int], assign_costs: list[list[int]],
                       assignment: list[int], max_iterations: int = 20) -> list[int]:
    """2-opt: swap pairs of clients between facilities. Fast version for plateau escape."""
    assignment = assignment[:]  # Copy
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Compute current cost
        open_facilities = set(assignment)
        current_cost = sum(opening_costs[i] for i in open_facilities)
        current_cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

        # Try swapping two clients (limited scan for speed)
        for j1 in range(min(n_clients, 30)):  # Limit to first 30 clients for speed
            for j2 in range(j1 + 1, min(n_clients, j1 + 30)):  # Limit neighborhood
                # Try swapping their facility assignments
                old_fac1, old_fac2 = assignment[j1], assignment[j2]

                for new_fac1 in range(n_facilities):
                    for new_fac2 in range(n_facilities):
                        if (new_fac1 == old_fac1 and new_fac2 == old_fac2):
                            continue

                        assignment[j1] = new_fac1
                        assignment[j2] = new_fac2
                        new_open = set(assignment)
                        new_cost = sum(opening_costs[i] for i in new_open)
                        new_cost += sum(assign_costs[assignment[c]][c] for c in range(n_clients))

                        if new_cost < current_cost:
                            current_cost = new_cost
                            improved = True
                            break

                        assignment[j1] = old_fac1
                        assignment[j2] = old_fac2

                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

    return assignment


def solve(opening_costs: list[int], assign_costs: list[list[int]]) -> list[int]:
    """
    Solve the Uncapacitated Facility Location Problem.

    Choose which facilities to open and assign each client to an open facility
    to minimise total cost = sum of opening costs + sum of assignment costs.

    Args:
        opening_costs: list of n_facilities ints. opening_costs[i] = cost to
                       open facility i.
        assign_costs: n_facilities x n_clients matrix. assign_costs[i][j] =
                      cost of assigning client j to facility i.

    Returns:
        assignment: list of length n_clients where assignment[j] = index of
                    the facility that client j is assigned to. Facilities with
                    at least one assigned client are considered "open" and incur
                    their opening cost.
    """
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0
    if n_clients == 0:
        return []

    best_assignment = None
    best_cost = float('inf')

    # Try construction strategies with multiple seeds and weight variations
    strategies = [_solve_greedy_client_first, _solve_facility_first, _solve_facility_load_balanced,
                  _solve_facility_load_balanced_w0_3, _solve_facility_load_balanced_w0_5,
                  _solve_facility_load_balanced_w0_7, _solve_greedy_cost_driven, _solve_savings_based]

    for strategy in strategies:
        for seed in range(8):
            assignment = strategy(opening_costs, assign_costs, seed)

            # Close underutilized facilities
            assignment = _facility_closing_phase(opening_costs, assign_costs, assignment)

            # Apply 1-opt local search
            assignment = _local_search_1opt(opening_costs, assign_costs, assignment)

            # Compute cost of this solution
            open_facilities = set(assignment)
            cost = sum(opening_costs[i] for i in open_facilities)
            cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))

            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment

    # Apply Iterated Local Search once on best solution
    if best_assignment is not None:
        best_assignment = _iterated_local_search(opening_costs, assign_costs, best_assignment,
                                                max_iterations=3, seed=42)

    return best_assignment
