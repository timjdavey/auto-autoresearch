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

    # --- Helper: compute total cost ---
    def total_cost(assign):
        opened = set(assign)
        cost = sum(opening_costs[i] for i in opened)
        cost += sum(assign_costs[assign[j]][j] for j in range(n_clients))
        return cost

    def refine_assignment(assign, max_iterations=5):
        """Client reassignment refinement with iteration limit."""
        for iteration in range(max_iterations):
            improved = False
            current_cost = total_cost(assign)

            for j in range(n_clients):
                old_fac = assign[j]

                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    assign[j] = new_fac
                    new_cost = total_cost(assign)

                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                        break
                    else:
                        assign[j] = old_fac

            if not improved:
                break
        return assign

    # --- Refine initial assignment ---
    assignment = refine_assignment(assignment)

    # --- Local search: facility closing with refinement ---
    improved = True
    facility_iterations = 0
    max_facility_iterations = 50  # Allow reasonable iterations while preventing infinite loops
    while improved and facility_iterations < max_facility_iterations:
        improved = False
        facility_iterations += 1
        current_cost = total_cost(assignment)
        opened = set(assignment)

        for close_fac in opened:
            if len(opened) == 1:
                continue

            clients_of_fac = [j for j in range(n_clients) if assignment[j] == close_fac]

            for j in clients_of_fac:
                best_new_fac = min(
                    (i for i in range(n_facilities) if i != close_fac),
                    key=lambda i: assign_costs[i][j]
                )
                assignment[j] = best_new_fac

            # Light refinement after closing (single pass only)
            assignment = refine_assignment(assignment, max_iterations=1)
            new_cost = total_cost(assignment)

            if new_cost < current_cost:
                improved = True
                current_cost = new_cost
            else:
                # Revert
                for j in clients_of_fac:
                    assignment[j] = close_fac

    return assignment
