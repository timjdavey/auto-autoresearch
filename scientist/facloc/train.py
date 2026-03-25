"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


def solve(opening_costs: list[int], assign_costs: list[list[int]]) -> list[int]:
    """
    Solve the Uncapacitated Facility Location Problem using multi-seed approach.

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
    import time
    import random
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    start_time = time.time()
    time_limit = 55  # 55s out of 60s limit, maximize time for local search

    def evaluate_cost(assignment):
        """Compute total cost of an assignment."""
        opened = set(assignment)
        facility_cost = sum(opening_costs[f] for f in opened)
        assignment_cost = sum(assign_costs[assignment[j]][j] for j in range(n_clients))
        return facility_cost + assignment_cost

    def local_search(assignment):
        """Improve assignment via client reassignment, 2-opt swaps, and facility closing moves."""
        improved = True
        phase = 0  # 0 = single moves, 1 = 2-opt swaps, 2 = facility closing
        while improved and time.time() - start_time < time_limit:
            improved = False
            current_cost = evaluate_cost(assignment)

            if phase == 0:
                # Phase 0: Single client reassignment moves (best-improvement)
                best_move = None
                best_move_cost = current_cost
                for j in range(n_clients):
                    old_fac = assignment[j]
                    for new_fac in range(n_facilities):
                        if new_fac == old_fac:
                            continue
                        assignment[j] = new_fac
                        new_cost = evaluate_cost(assignment)
                        if new_cost < best_move_cost:
                            best_move_cost = new_cost
                            best_move = (j, new_fac)
                        assignment[j] = old_fac
                # Apply best move if found
                if best_move is not None:
                    j, new_fac = best_move
                    assignment[j] = new_fac
                    improved = True
                if not improved:
                    phase = 1  # Move to 2-opt if single moves don't help
            elif phase == 1:
                # Phase 1: 2-opt swaps (swap facility assignments of pairs of clients)
                best_move = None
                best_move_cost = current_cost
                for j1 in range(n_clients):
                    for j2 in range(j1 + 1, n_clients):
                        # Swap assignments: client j1 gets j2's facility, j2 gets j1's facility
                        old_fac1, old_fac2 = assignment[j1], assignment[j2]
                        if old_fac1 == old_fac2:
                            continue
                        assignment[j1], assignment[j2] = old_fac2, old_fac1
                        new_cost = evaluate_cost(assignment)
                        if new_cost < best_move_cost:
                            best_move_cost = new_cost
                            best_move = (j1, j2)
                        assignment[j1], assignment[j2] = old_fac1, old_fac2
                # Apply best move if found
                if best_move is not None:
                    j1, j2 = best_move
                    assignment[j1], assignment[j2] = assignment[j2], assignment[j1]
                    improved = True
                if not improved:
                    phase = 2  # Move to facility closing if 2-opt doesn't help
            else:
                # Phase 2: Try closing a facility and reassigning its clients
                opened = set(assignment)
                for fac_to_close in opened:
                    # Find clients assigned to this facility
                    clients_to_move = [j for j in range(n_clients) if assignment[j] == fac_to_close]
                    if not clients_to_move:
                        continue
                    # Try reassigning each client to best alternative facility
                    old_assignments = {j: assignment[j] for j in clients_to_move}
                    for j in clients_to_move:
                        best_new_fac = min((i for i in range(n_facilities) if i != fac_to_close),
                                          key=lambda i: assign_costs[i][j])
                        assignment[j] = best_new_fac
                    new_cost = evaluate_cost(assignment)
                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                        break
                    else:
                        # Revert
                        for j in clients_to_move:
                            assignment[j] = old_assignments[j]
        return assignment

    # Multi-seed initialization strategies
    candidates = []

    # Strategy 1: Facility-first (try opening different facilities first)
    for seed_fac in range(min(n_facilities, 6)):
        if time.time() - start_time >= time_limit:
            break
        assignment = [seed_fac] * n_clients
        assignment = local_search(assignment)
        candidates.append(assignment[:])

    # Strategy 2: Load-balanced with opening cost awareness (multiple weight variations)
    for weight in [0.2, 0.4, 0.6, 0.8]:
        if time.time() - start_time >= time_limit:
            break
        assignment = []
        facility_loads = [0] * n_facilities
        for j in range(n_clients):
            best_fac = 0
            best_score = float('inf')
            for i in range(n_facilities):
                current_load = facility_loads[i] + 1
                amortized_cost = opening_costs[i] / current_load if facility_loads[i] > 0 else opening_costs[i]
                score = assign_costs[i][j] + amortized_cost * weight
                if score < best_score:
                    best_score = score
                    best_fac = i
            assignment.append(best_fac)
            facility_loads[best_fac] += 1
        assignment = local_search(assignment)
        candidates.append(assignment[:])

    # Strategy 3: Greedy nearest (baseline)
    if time.time() - start_time < time_limit:
        assignment = []
        for j in range(n_clients):
            best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
            assignment.append(best_fac)
        assignment = local_search(assignment)
        candidates.append(assignment[:])

    # Return best solution found
    best = min(candidates, key=evaluate_cost)
    return best
