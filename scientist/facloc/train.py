"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time


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
    if n_facilities == 1:
        return [0] * n_clients

    def compute_cost(assignment):
        open_facilities = set(assignment)
        open_cost = sum(opening_costs[f] for f in open_facilities)
        assign_cost = sum(assign_costs[assignment[j]][j] for j in range(n_clients))
        return open_cost + assign_cost

    def local_search(assignment):
        improved = True
        max_iterations = 100
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            current_cost = compute_cost(assignment)
            best_move = None
            best_move_cost = current_cost

            # Find best single move
            for j in range(n_clients):
                old_fac = assignment[j]
                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue
                    assignment[j] = new_fac
                    new_cost = compute_cost(assignment)
                    if new_cost < best_move_cost:
                        best_move_cost = new_cost
                        best_move = (j, old_fac, new_fac)
                        improved = True
                    assignment[j] = old_fac

            # Apply best move
            if best_move:
                j, old_fac, new_fac = best_move
                assignment[j] = new_fac

        return assignment

    def local_search_2opt(assignment):
        """2-opt: try swapping assignments between pairs of clients assigned to different facilities."""
        improved = True
        max_iterations = 50
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            current_cost = compute_cost(assignment)
            best_swap = None
            best_swap_cost = current_cost

            # Build facility-to-clients map for efficiency
            facility_clients = [[] for _ in range(n_facilities)]
            for j in range(n_clients):
                facility_clients[assignment[j]].append(j)

            # Try swapping clients from different facilities
            for f1 in range(n_facilities):
                if not facility_clients[f1]:
                    continue
                for f2 in range(f1 + 1, n_facilities):
                    if not facility_clients[f2]:
                        continue
                    # Try all pairs of clients from these two facilities
                    for j1 in facility_clients[f1]:
                        for j2 in facility_clients[f2]:
                            # Swap assignments
                            assignment[j1] = f2
                            assignment[j2] = f1
                            new_cost = compute_cost(assignment)

                            if new_cost < best_swap_cost:
                                best_swap_cost = new_cost
                                best_swap = (j1, j2, f1, f2)
                                improved = True

                            # Revert
                            assignment[j1] = f1
                            assignment[j2] = f2

            # Apply best swap if found
            if best_swap:
                j1, j2, f1, f2 = best_swap
                assignment[j1] = f2
                assignment[j2] = f1

        return assignment

    def local_search_3opt_selective(assignment):
        """3-opt: Try relocating clients from one facility to another (on small/medium instances only)."""
        # Only run on smaller instances due to computational cost
        if n_clients > 150:
            return assignment

        improved = True
        max_iterations = 20
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            current_cost = compute_cost(assignment)
            best_move = None
            best_move_cost = current_cost

            # Try moving a client from its current facility to another facility,
            # then reassigning a second client to fill any gap
            for j1 in range(n_clients):
                old_fac1 = assignment[j1]
                for new_fac1 in range(n_facilities):
                    if new_fac1 == old_fac1:
                        continue

                    # Try reassigning j1 to new_fac1
                    assignment[j1] = new_fac1

                    # For each other client, try moving it to j1's old facility
                    for j2 in range(n_clients):
                        if j2 == j1:
                            continue
                        old_fac2 = assignment[j2]
                        if old_fac2 == old_fac1:
                            continue

                        assignment[j2] = old_fac1
                        new_cost = compute_cost(assignment)

                        if new_cost < best_move_cost:
                            best_move_cost = new_cost
                            best_move = (j1, new_fac1, j2, old_fac1)
                            improved = True

                        # Revert j2
                        assignment[j2] = old_fac2

                    # Revert j1
                    assignment[j1] = old_fac1

            # Apply best move if found
            if best_move:
                j1, new_fac1, j2, new_fac2 = best_move
                assignment[j1] = new_fac1
                assignment[j2] = new_fac2

        return assignment

    # Try multiple initialization strategies and keep best
    best_assignment = None
    best_cost = float('inf')

    # Strategy 1: Greedy nearest
    assignment = [-1] * n_clients
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment[j] = best_fac
    assignment = local_search(assignment)
    cost = compute_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Strategy 2: Facility-first (process facilities in order)
    assignment = [-1] * n_clients
    unassigned = set(range(n_clients))
    for f in range(n_facilities):
        if unassigned:
            # Find client with minimum cost at this facility
            best_client = min(unassigned, key=lambda j: assign_costs[f][j])
            assignment[best_client] = f
            unassigned.remove(best_client)
    # Assign remaining unassigned to nearest facility
    for j in unassigned:
        assignment[j] = min(range(n_facilities), key=lambda i: assign_costs[i][j])
    assignment = local_search(assignment)
    cost = compute_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Strategy 3: Load-balanced (assign clients to minimize load per facility)
    assignment = [-1] * n_clients
    facility_load = [0] * n_facilities
    sorted_clients = sorted(range(n_clients), key=lambda j: min(assign_costs[i][j] for i in range(n_facilities)))
    for j in sorted_clients:
        # Find facility with lowest cost for this client, considering load balance
        best_fac = min(range(n_facilities),
                      key=lambda i: assign_costs[i][j] + 0.01 * facility_load[i])
        assignment[j] = best_fac
        facility_load[best_fac] += 1
    assignment = local_search(assignment)
    cost = compute_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Strategy 4: Facility-cost-aware (consider opening costs in initialization)
    assignment = [-1] * n_clients
    facility_load = [0] * n_facilities
    opened_facilities = set()

    # First pass: assign clients with strong preferences
    for j in sorted_clients:
        # Cost includes assignment + amortized opening cost (with 0.3 weight)
        best_fac = min(range(n_facilities),
                      key=lambda i: assign_costs[i][j] + 0.3 * (opening_costs[i] / max(1, len([c for c in range(n_clients) if assignment[c] == i]) + 1)))
        assignment[j] = best_fac
        facility_load[best_fac] += 1
        opened_facilities.add(best_fac)

    assignment = local_search(assignment)

    # Facility closing phase: try closing facilities with few clients
    improved = True
    max_iter = 20
    iter_count = 0
    while improved and iter_count < max_iter:
        improved = False
        iter_count += 1
        current_cost = compute_cost(assignment)

        # Count clients per facility
        facility_clients = [[] for _ in range(n_facilities)]
        for j in range(n_clients):
            facility_clients[assignment[j]].append(j)

        # Try closing each facility
        for f in range(n_facilities):
            if not facility_clients[f]:
                continue
            # Try reassigning all clients from facility f to their best alternative
            old_assignment = assignment[:]
            for j in facility_clients[f]:
                assignment[j] = min(range(n_facilities),
                                   key=lambda i: assign_costs[i][j] if i != f else float('inf'))
            new_cost = compute_cost(assignment)
            if new_cost < current_cost:
                current_cost = new_cost
                improved = True
            else:
                assignment = old_assignment[:]

    # Second pass of 1-opt after facility closing
    assignment = local_search(assignment)

    cost = compute_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Strategy 5: Random initialization with local search (explore different regions)
    assignment = [random.randint(0, n_facilities - 1) for _ in range(n_clients)]
    assignment = local_search(assignment)
    cost = compute_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Perturbation-based restarts to escape local optima
    start_time = time.time()
    timeout_budget = 50  # Leave 10s margin before 60s hard limit for safety
    restart_count = 0

    # Analyze current best solution for facility-aware perturbation
    facility_usage = {}
    for j in range(n_clients):
        f = best_assignment[j]
        if f not in facility_usage:
            facility_usage[f] = []
        facility_usage[f].append(j)

    while time.time() - start_time < timeout_budget:
        restart_count += 1

        # Use mixed perturbation strategy
        perturbed = best_assignment[:]

        # Decide perturbation type based on restart count
        if restart_count % 3 == 0:
            # Every 3rd restart: facility-aware (perturb clients from expensive facilities)
            expensive_facilities = [f for f in facility_usage if opening_costs[f] > sum(opening_costs) / len(opening_costs)]
            if expensive_facilities:
                perturbation_pool = []
                for f in expensive_facilities:
                    if f in facility_usage:
                        perturbation_pool.extend(facility_usage[f])
                n_perturb = max(1, len(perturbation_pool) // 3)
                if perturbation_pool:
                    perturb_indices = random.sample(perturbation_pool, min(n_perturb, len(perturbation_pool)))
                    for j in perturb_indices:
                        perturbed[j] = random.randint(0, n_facilities - 1)
            else:
                # Fallback to random if no expensive facilities
                n_perturb = max(1, n_clients // 10)
                perturb_indices = random.sample(range(n_clients), min(n_perturb, n_clients))
                for j in perturb_indices:
                    perturbed[j] = random.randint(0, n_facilities - 1)
        else:
            # Regular random perturbation for other restarts
            n_perturb = max(1, n_clients // 10)  # Perturb ~10% of assignments
            perturb_indices = random.sample(range(n_clients), min(n_perturb, n_clients))
            for j in perturb_indices:
                perturbed[j] = random.randint(0, n_facilities - 1)

        # Apply local search to perturbed solution
        perturbed = local_search(perturbed)

        # Apply facility closing
        improved = True
        max_iter = 10
        iter_count = 0
        while improved and iter_count < max_iter:
            improved = False
            iter_count += 1
            current_cost = compute_cost(perturbed)
            facility_clients = [[] for _ in range(n_facilities)]
            for j in range(n_clients):
                facility_clients[perturbed[j]].append(j)
            for f in range(n_facilities):
                if not facility_clients[f]:
                    continue
                old_assignment = perturbed[:]
                for j in facility_clients[f]:
                    perturbed[j] = min(range(n_facilities),
                                      key=lambda i: assign_costs[i][j] if i != f else float('inf'))
                new_cost = compute_cost(perturbed)
                if new_cost < current_cost:
                    current_cost = new_cost
                    improved = True
                else:
                    perturbed = old_assignment[:]

        # Final 1-opt
        perturbed = local_search(perturbed)

        cost = compute_cost(perturbed)
        if cost < best_cost:
            best_cost = cost
            best_assignment = perturbed[:]

    return best_assignment
