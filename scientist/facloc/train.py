"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest with local search (client reassignment).
The agent should improve this to maximise avg_improvement across all instances.
"""

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

    # --- Greedy nearest: initial assignment ---
    assignment = []
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)

    # --- Compute total cost helper ---
    def total_cost(asgn):
        opened = set(asgn)
        cost = sum(opening_costs[i] for i in opened)
        cost += sum(assign_costs[asgn[j]][j] for j in range(n_clients))
        return cost

    # --- Alternating local search and facility closure ---
    global_start = time.time()
    time_limit = 50

    while (time.time() - global_start) < time_limit:
        # Local search phase (2 seconds max per iteration)
        search_start = time.time()
        search_limit = 2.0
        current_cost = total_cost(assignment)

        while (time.time() - search_start) < search_limit:
            best_delta = 0
            best_move = None

            # Find the best single client move
            for j in range(n_clients):
                old_fac = assignment[j]
                old_assignment_cost = assign_costs[old_fac][j]

                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    new_assignment_cost = assign_costs[new_fac][j]
                    delta = new_assignment_cost - old_assignment_cost

                    # Check if facility new_fac is currently open
                    fac_opening_delta = 0
                    if new_fac not in assignment:
                        # Would need to open new facility
                        fac_opening_delta = opening_costs[new_fac]

                    # Check if closing old facility saves money
                    if assignment.count(old_fac) == 1:
                        # This is the last client on old_fac
                        fac_opening_delta -= opening_costs[old_fac]

                    total_delta = delta + fac_opening_delta

                    if total_delta < best_delta:
                        best_delta = total_delta
                        best_move = (j, old_fac, new_fac)

            if best_move is None:
                break

            j, old_fac, new_fac = best_move
            assignment[j] = new_fac
            current_cost += best_delta

        # Facility closure phase
        if (time.time() - global_start) < (time_limit - 0.5):
            open_facilities = list(set(assignment))
            for fac_to_close in open_facilities:
                clients_on_fac = [j for j in range(n_clients) if assignment[j] == fac_to_close]
                n_clients_on_fac = len(clients_on_fac)

                # Compute cost of reassigning all clients from this facility
                total_reassign_cost_delta = 0
                reassignments = []

                for j in clients_on_fac:
                    # Find best alternative facility for this client
                    best_alt_fac = min((f for f in range(n_facilities) if f != fac_to_close),
                                       key=lambda f: assign_costs[f][j])
                    cost_delta = assign_costs[best_alt_fac][j] - assign_costs[fac_to_close][j]
                    total_reassign_cost_delta += cost_delta
                    reassignments.append((j, best_alt_fac))

                # Close if:
                # 1. Saves money overall, OR
                # 2. Facility has very few clients and high opening cost relative to reassignment
                savings = opening_costs[fac_to_close]
                avg_client_cost = total_reassign_cost_delta / n_clients_on_fac if n_clients_on_fac > 0 else 0

                # Aggressive closure: close if few clients and opening cost is high per client
                should_close = (total_reassign_cost_delta < savings) or \
                              (n_clients_on_fac <= 2 and savings > avg_client_cost * 0.5)

                if should_close:
                    for j, new_fac in reassignments:
                        assignment[j] = new_fac

    return assignment
