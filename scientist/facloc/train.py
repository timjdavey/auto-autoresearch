"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest (baseline).
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
    start_time = time.time()
    time_limit = 45.0  # 45 seconds, leaving 15s safety margin

    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    def compute_cost(assign):
        """Compute total cost: opening costs + assignment costs."""
        open_facilities = set(assign)
        cost = sum(opening_costs[f] for f in open_facilities)
        cost += sum(assign_costs[assign[j]][j] for j in range(n_clients))
        return cost

    def facility_insertion(start_fac):
        """Greedy Facility Insertion from a given starting facility."""
        assign = [start_fac] * n_clients
        open_f = {start_fac}

        for _ in range(n_facilities - 1):
            if time.time() - start_time >= time_limit * 0.15:
                break
            best_gain = 0
            best_fac = -1
            best_assign = None

            for new_fac in range(n_facilities):
                if new_fac in open_f:
                    continue
                test_assign = [min(open_f | {new_fac}, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
                cost_without = compute_cost(assign)
                cost_with = compute_cost(test_assign)
                gain = cost_without - cost_with
                if gain > best_gain:
                    best_gain = gain
                    best_fac = new_fac
                    best_assign = test_assign

            if best_fac >= 0 and best_assign:
                open_f.add(best_fac)
                assign = best_assign
            else:
                break

        return assign, compute_cost(assign)

    # Multi-start: try a few promising starting facilities
    best_assignment = None
    best_cost = float('inf')

    # Try top 10 facilities with best "cost per client" plus a few random ones for diversification
    greedy_candidates = sorted(range(n_facilities), key=lambda i: (opening_costs[i] + sum(assign_costs[i][j] for j in range(n_clients))) / n_clients)[:min(10, n_facilities)]

    # Add random facilities to diversify starting points
    random_candidates = random.sample([i for i in range(n_facilities) if i not in greedy_candidates],
                                       min(3, n_facilities - len(greedy_candidates)))
    start_candidates = greedy_candidates + random_candidates

    for start_fac in start_candidates:
        if time.time() - start_time >= time_limit * 0.15:
            break
        assign, cost = facility_insertion(start_fac)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assign

    assignment = best_assignment if best_assignment else facility_insertion(start_candidates[0])[0]

    best_cost = compute_cost(assignment)

    # Local search: 1-opt client reassignment (first improvement)
    improved = True
    while improved and time.time() - start_time < time_limit * 0.9:
        improved = False

        # Try reassigning individual clients to any facility
        for j in range(n_clients):
            current_fac = assignment[j]
            best_alt_fac = None
            best_alt_cost = best_cost

            # Find best alternative assignment for this client
            for new_fac in range(n_facilities):
                if new_fac == current_fac:
                    continue
                new_assignment = assignment[:]
                new_assignment[j] = new_fac
                new_cost = compute_cost(new_assignment)
                if new_cost < best_alt_cost:
                    best_alt_cost = new_cost
                    best_alt_fac = new_fac

            if best_alt_fac is not None:
                assignment[j] = best_alt_fac
                best_cost = best_alt_cost
                improved = True
                break

    return assignment
