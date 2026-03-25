"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest with local search (client reassignment + facility closure).
The agent should improve this to maximise avg_improvement across all instances.
"""

import time
import random


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

    # --- Compute total cost helper ---
    def total_cost(asgn):
        opened = set(asgn)
        cost = sum(opening_costs[i] for i in opened)
        cost += sum(assign_costs[asgn[j]][j] for j in range(n_clients))
        return cost

    def local_search(assignment, time_budget, start_time):
        """Apply local search to assignment."""
        max_iterations = 100
        iteration = 0
        while (time.time() - start_time) < time_budget and iteration < max_iterations:
            iteration += 1
            improved = False
            best_delta = 0
            best_move = None

            # Phase 1: Find best individual client reassignment move
            for j in range(n_clients):
                old_fac = assignment[j]
                old_assignment_cost = assign_costs[old_fac][j]

                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    new_assignment_cost = assign_costs[new_fac][j]

                    # Calculate facility opening/closing costs (before moving)
                    assignment_delta = new_assignment_cost - old_assignment_cost
                    facility_delta = 0

                    # Would we open new_fac? (check if any OTHER client uses it)
                    if sum(1 for k in range(n_clients) if assignment[k] == new_fac) == 0:
                        facility_delta += opening_costs[new_fac]

                    # Would we close old_fac? (check if this is the only client on it)
                    if sum(1 for k in range(n_clients) if assignment[k] == old_fac) == 1:
                        facility_delta -= opening_costs[old_fac]

                    total_delta = assignment_delta + facility_delta

                    if total_delta < best_delta:
                        best_delta = total_delta
                        best_move = (j, new_fac)

            # Apply best move if found
            if best_move:
                j, new_fac = best_move
                assignment[j] = new_fac
                improved = True

            # Phase 1.5: Try 2-opt swaps if time permits
            if not improved and (time.time() - start_time) < (time_budget - 0.5):
                best_delta = 0
                best_swap = None
                for j1 in range(n_clients):
                    for j2 in range(j1 + 1, n_clients):
                        fac1 = assignment[j1]
                        fac2 = assignment[j2]
                        if fac1 == fac2:
                            continue
                        old_cost = assign_costs[fac1][j1] + assign_costs[fac2][j2]
                        new_cost = assign_costs[fac2][j1] + assign_costs[fac1][j2]
                        delta = new_cost - old_cost
                        if delta < best_delta:
                            best_delta = delta
                            best_swap = (j1, j2, fac1, fac2)
                if best_swap:
                    j1, j2, fac1, fac2 = best_swap
                    assignment[j1] = fac2
                    assignment[j2] = fac1
                    improved = True

            # Phase 2: Facility closure (if time permits and no client move improved)
            if not improved and (time.time() - start_time) < (time_budget - 1):
                open_facilities = list(set(assignment))
                for fac_to_close in open_facilities:
                    clients_on_fac = [j for j in range(n_clients) if assignment[j] == fac_to_close]
                    if not clients_on_fac:
                        continue

                    # Compute cost of reassigning all clients from this facility
                    total_reassign_cost_delta = 0
                    reassignments = []

                    for j in clients_on_fac:
                        # Find best alternative facility
                        best_alt_fac = min((f for f in range(n_facilities) if f != fac_to_close),
                                           key=lambda f: assign_costs[f][j])
                        cost_delta = assign_costs[best_alt_fac][j] - assign_costs[fac_to_close][j]
                        total_reassign_cost_delta += cost_delta
                        reassignments.append((j, best_alt_fac))

                    # Close if it saves money
                    if total_reassign_cost_delta < opening_costs[fac_to_close]:
                        for j, new_fac in reassignments:
                            assignment[j] = new_fac
                        improved = True
                        break

            if not improved:
                break
        return assignment

    global_start = time.time()
    time_limit = 45

    # Try multiple initializations and keep the best
    best_assignment = None
    best_cost = float('inf')

    # Init 1: Greedy nearest (usually best, get more time)
    assignment = []
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)
    assignment = local_search(assignment, 18, global_start)
    cost = total_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment[:]

    # Init 2: Cost-aware (minimize assignment + opening spread)
    if (time.time() - global_start) < 33:
        avg_opening = sum(opening_costs) / n_facilities
        assignment = []
        for j in range(n_clients):
            best_fac = min(range(n_facilities),
                          key=lambda i: assign_costs[i][j] + avg_opening / n_clients)
            assignment.append(best_fac)
        assignment = local_search(assignment, 13, global_start)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    # Init 3: Cheapest facility bias
    if (time.time() - global_start) < 41:
        assignment = []
        for j in range(n_clients):
            best_fac = min(range(n_facilities),
                          key=lambda i: assign_costs[i][j] + 0.1 * opening_costs[i])
            assignment.append(best_fac)
        assignment = local_search(assignment, 10, global_start)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

    return best_assignment if best_assignment else [0] * n_clients
