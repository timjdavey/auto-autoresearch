"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest (baseline).
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
    start_time = time.time()
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    def total_cost(asn):
        opened = set(asn)
        cost = sum(opening_costs[i] for i in opened)
        cost += sum(assign_costs[asn[j]][j] for j in range(len(asn)))
        return cost

    def local_search(assignment):
        # 1-opt local search: reassign clients if it improves total cost
        improved = True
        while improved:
            if time.time() - start_time > 58.0:
                break
            improved = False

            for j in range(n_clients):
                current_fac = assignment[j]
                for fac in range(n_facilities):
                    if fac == current_fac:
                        continue
                    # Cost delta for reassigning client j to facility fac
                    delta = assign_costs[fac][j] - assign_costs[current_fac][j]

                    # If current facility loses its last client, save its opening cost
                    if sum(1 for c in range(n_clients) if assignment[c] == current_fac) == 1:
                        delta -= opening_costs[current_fac]

                    # If new facility is unused, pay its opening cost
                    if sum(1 for c in range(n_clients) if assignment[c] == fac) == 0:
                        delta += opening_costs[fac]

                    if delta < -1e-6:
                        assignment[j] = fac
                        improved = True
                        break
                if improved:
                    break

        return assignment

    best_assignment = None
    best_cost = float('inf')

    # Seed 1: greedy nearest
    assignment = [min(range(n_facilities), key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
    assignment = local_search(assignment[:])
    cost = total_cost(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment

    # Seed 2: all to cheapest facility
    if time.time() - start_time < 20.0:
        assignment = [min(range(n_facilities), key=lambda i: opening_costs[i]) for _ in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 3: facility-first approach - open cheapest facilities, assign clients optimally
    if time.time() - start_time < 30.0:
        # Try opening a small subset of cheapest facilities
        n_facs_to_use = max(1, n_facilities // 3)
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 4: balanced assignment - assign considering both assignment cost and facility overhead
    if time.time() - start_time < 40.0:
        facility_load = [0] * n_facilities
        assignment = [0] * n_clients
        for j in range(n_clients):
            best_fac = 0
            best_score = float('inf')
            for i in range(n_facilities):
                # Score: assignment cost + load penalty + amortized opening cost
                # Amortized opening cost = opening_costs[i] / (1 + facility_load[i])
                amortized_opening = opening_costs[i] / max(1.0, facility_load[i] + 1)
                score = assign_costs[i][j] + 0.15 * facility_load[i] + 0.08 * amortized_opening
                if score < best_score:
                    best_score = score
                    best_fac = i
            assignment[j] = best_fac
            facility_load[best_fac] += 1
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 5: facility-first with n/2 facilities
    if time.time() - start_time < 45.0:
        n_facs_to_use = max(1, n_facilities // 2)
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 6: facility-first with n/5 facilities (more restrictive)
    if time.time() - start_time < 50.0:
        n_facs_to_use = max(1, max(1, n_facilities // 5))
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 7: facility-first with n/4 facilities
    if time.time() - start_time < 50.0:
        n_facs_to_use = max(1, n_facilities // 4)
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 8: greedy facility opening - start with single cheapest
    if time.time() - start_time < 52.0:
        cheapest_fac = min(range(n_facilities), key=lambda i: opening_costs[i])
        assignment = [cheapest_fac] * n_clients
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 9: minimize facility count - only use cheapest sqrt(n_facilities) facilities
    if time.time() - start_time < 54.0:
        import math
        n_facs_to_use = max(1, int(math.sqrt(n_facilities)))
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 10: even more restrictive - sqrt(sqrt(n_facilities))
    if time.time() - start_time < 56.0:
        import math
        n_facs_to_use = max(1, int(math.sqrt(math.sqrt(n_facilities))))
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # Seed 11: facility-first with n/6 facilities (mid-range)
    if time.time() - start_time < 57.0:
        n_facs_to_use = max(1, n_facilities // 6)
        cheapest_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])[:n_facs_to_use]
        assignment = [min(cheapest_facs, key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
        assignment = local_search(assignment)
        cost = total_cost(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment
