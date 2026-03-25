"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest with local search.
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

    def calc_cost(assign):
        opened = set(assign)
        cost = sum(opening_costs[i] for i in opened)
        cost += sum(assign_costs[assign[j]][j] for j in range(n_clients))
        return cost

    def local_search(initial_assignment, time_limit=2.0):
        """Run local search from given initial assignment."""
        assignment = initial_assignment[:]
        improved = True
        iterations = 0
        max_iterations = 28
        start_time = time.time()

        while improved and iterations < max_iterations:
            if time.time() - start_time > time_limit:
                break
            improved = False
            iterations += 1
            current_cost = calc_cost(assignment)

            # Try closing each open facility (most expensive first) and reassigning its clients
            open_facilities = sorted(set(assignment), key=lambda i: opening_costs[i], reverse=True)
            for fac_to_close in open_facilities:
                new_assignment = assignment[:]
                clients_to_reassign = [j for j in range(n_clients) if assignment[j] == fac_to_close]

                valid = True
                for j in clients_to_reassign:
                    best_alt = min(
                        (i for i in range(n_facilities) if i != fac_to_close),
                        key=lambda i: assign_costs[i][j],
                        default=None
                    )
                    if best_alt is None:
                        valid = False
                        break
                    new_assignment[j] = best_alt

                if valid:
                    new_cost = calc_cost(new_assignment)
                    if new_cost < current_cost:
                        assignment = new_assignment
                        improved = True
                        break

            # Try reassigning individual clients (first-improvement)
            if not improved:
                for j in range(n_clients):
                    current_fac = assignment[j]
                    best_new_fac = current_fac
                    best_delta = 0

                    for new_fac in range(n_facilities):
                        if new_fac == current_fac:
                            continue

                        delta = assign_costs[new_fac][j] - assign_costs[current_fac][j]
                        clients_at_current = sum(1 for k in range(n_clients) if assignment[k] == current_fac)
                        if clients_at_current == 1:
                            delta -= opening_costs[current_fac]
                        clients_at_new = sum(1 for k in range(n_clients) if assignment[k] == new_fac)
                        if clients_at_new == 0:
                            delta += opening_costs[new_fac]

                        if delta < best_delta:
                            best_new_fac = new_fac
                            best_delta = delta

                    if best_new_fac != current_fac:
                        assignment[j] = best_new_fac
                        improved = True
                        break

            # Try 2-opt: swap a client between two open facilities (first-improvement)
            if not improved:
                open_facs = sorted(set(assignment))
                for j in range(n_clients):
                    current_fac = assignment[j]
                    for new_fac in open_facs:
                        if new_fac == current_fac:
                            continue

                        delta = assign_costs[new_fac][j] - assign_costs[current_fac][j]
                        clients_at_current = sum(1 for k in range(n_clients) if assignment[k] == current_fac)
                        if clients_at_current == 1:
                            delta -= opening_costs[current_fac]

                        if delta < 0:
                            assignment[j] = new_fac
                            improved = True
                            break
                    if improved:
                        break

            # Try facility swap: close one open facility, open a closed one (first-improvement)
            if not improved:
                open_facs = sorted(set(assignment))
                closed_facs = [i for i in range(n_facilities) if i not in open_facs]

                for fac_to_close in open_facs:
                    clients_at_fac = [j for j in range(n_clients) if assignment[j] == fac_to_close]

                    for fac_to_open in closed_facs:
                        # Cost to reassign clients from fac_to_close to fac_to_open
                        reassign_cost = sum(assign_costs[fac_to_open][j] - assign_costs[fac_to_close][j]
                                           for j in clients_at_fac)
                        delta = reassign_cost - opening_costs[fac_to_close] + opening_costs[fac_to_open]

                        if delta < 0:
                            new_assignment = assignment[:]
                            for j in clients_at_fac:
                                new_assignment[j] = fac_to_open
                            assignment = new_assignment
                            improved = True
                            break
                    if improved:
                        break

            # Try 3-opt-like: reassign multiple clients together for better opening cost tradeoffs
            if not improved and n_clients <= 150:
                # Limited 3-opt: try swapping pairs of clients between facilities
                open_facs = sorted(set(assignment))
                if len(open_facs) >= 2:
                    fac_pairs = [(open_facs[i], open_facs[j]) for i in range(len(open_facs)) for j in range(i+1, min(i+5, len(open_facs)))]

                    for fac1, fac2 in fac_pairs[:10]:  # Limit to top 10 pairs
                        clients_at_fac1 = [j for j in range(n_clients) if assignment[j] == fac1]
                        clients_at_fac2 = [j for j in range(n_clients) if assignment[j] == fac2]

                        if len(clients_at_fac1) < 2 or len(clients_at_fac2) < 2:
                            continue

                        # Try swapping one client from each facility
                        for j1 in clients_at_fac1[:3]:  # Limit to first 3 clients
                            for j2 in clients_at_fac2[:3]:
                                new_assignment = assignment[:]
                                new_assignment[j1] = fac2
                                new_assignment[j2] = fac1
                                new_cost = calc_cost(new_assignment)
                                if new_cost < current_cost:
                                    assignment = new_assignment
                                    improved = True
                                    break
                            if improved:
                                break
                        if improved:
                            break

        return assignment

    # Try multiple initialization strategies with perturbation
    best_assignment = None
    best_cost = float('inf')
    total_opening = sum(opening_costs)
    sorted_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])

    def perturbation_restart(current_assignment, n_perturb=None):
        """Apply random perturbation to escape local optima."""
        if n_perturb is None:
            n_perturb = max(1, n_clients // 10)
        perturbed = current_assignment[:]
        perturb_indices = random.sample(range(n_clients), min(n_perturb, n_clients))
        for j in perturb_indices:
            perturbed[j] = random.randint(0, n_facilities - 1)
        return perturbed

    # Strategy 1: Greedy nearest (best-fit)
    assignment = []
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)
    result = local_search(assignment)
    cost = calc_cost(result)
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Strategy 1b: Greedy worst-fit (forces different facilities)
    assignment = []
    for j in range(n_clients):
        worst_fac = max(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(worst_fac)
    result = local_search(assignment)
    cost = calc_cost(result)
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Strategies 2-5: Facility-minimizing with selected budget percentages (cheapest facilities)
    for budget_pct in [0.05, 0.10, 0.15, 0.25]:
        opening_budget = total_opening * budget_pct
        selected_facs = []
        budget_used = 0
        for fac in sorted_facs:
            selected_facs.append(fac)
            budget_used += opening_costs[fac]
            if budget_used > opening_budget:
                break

        assignment = []
        for j in range(n_clients):
            best_fac = min(selected_facs, key=lambda i: assign_costs[i][j])
            assignment.append(best_fac)
        result = local_search(assignment)
        cost = calc_cost(result)
        if cost < best_cost:
            best_cost = cost
            best_assignment = result

    # Strategies 6-8: Random initializations with different seeds
    for seed in [42, 123, 456]:
        random.seed(seed)
        assignment = [random.randint(0, n_facilities - 1) for _ in range(n_clients)]
        result = local_search(assignment)
        cost = calc_cost(result)
        if cost < best_cost:
            best_cost = cost
            best_assignment = result

    # Strategy 9: Preference clustering (group clients by cheapest facility)
    preferences = []
    for j in range(n_clients):
        cheapest_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        preferences.append(cheapest_fac)

    assignment = preferences[:]
    result = local_search(assignment)
    cost = calc_cost(result)
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Perturbation restarts from best solution so far
    if best_assignment is not None:
        for restart_seed in [99, 111, 222, 333]:
            random.seed(restart_seed)
            perturbed = perturbation_restart(best_assignment, n_perturb=max(1, n_clients // 8))
            result = local_search(perturbed)
            cost = calc_cost(result)
            if cost < best_cost:
                best_cost = cost
                best_assignment = result

    return best_assignment
