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

    def local_search(init_assignment):
        """Run local search from given initial assignment."""
        assignment = list(init_assignment)

        for iteration in range(30):
            opened = set(assignment)
            improved = False

            # Try reassigning individual clients to other facilities
            for j in range(n_clients):
                current_fac = assignment[j]
                current_cost = assign_costs[current_fac][j]

                for new_fac in range(n_facilities):
                    if new_fac == current_fac:
                        continue

                    new_cost = assign_costs[new_fac][j]
                    # Check if this client would benefit from the new facility
                    if new_cost < current_cost:
                        # Calculate full cost change including opening new facility if needed
                        cost_change = new_cost - current_cost

                        # If new facility not currently open, add its opening cost
                        if new_fac not in assignment:
                            cost_change += opening_costs[new_fac]

                        # If current facility would no longer be open after this move, save opening cost
                        if assignment.count(current_fac) == 1:
                            cost_change -= opening_costs[current_fac]

                        if cost_change < 0:
                            assignment[j] = new_fac
                            improved = True

            # Try pairwise client swaps (2-opt style moves)
            for j1 in range(n_clients):
                for j2 in range(j1 + 1, n_clients):
                    fac1 = assignment[j1]
                    fac2 = assignment[j2]
                    if fac1 == fac2:
                        continue

                    # Current cost
                    current_cost = assign_costs[fac1][j1] + assign_costs[fac2][j2]
                    # Cost after swap
                    swap_cost = assign_costs[fac2][j1] + assign_costs[fac1][j2]

                    if swap_cost < current_cost:
                        assignment[j1], assignment[j2] = assignment[j2], assignment[j1]
                        improved = True

            # Try closing facilities
            for fac in list(opened):
                clients = [j for j in range(n_clients) if assignment[j] == fac]
                if not clients:
                    improved = True
                    continue

                reassign_cost = 0
                reassign_map = []
                for j in clients:
                    next_best = min(
                        (i for i in range(n_facilities) if i != fac),
                        key=lambda i: assign_costs[i][j]
                    )
                    reassign_cost += assign_costs[next_best][j] - assign_costs[fac][j]
                    reassign_map.append((j, next_best))

                if reassign_cost < opening_costs[fac]:
                    for j, next_best in reassign_map:
                        assignment[j] = next_best
                    improved = True

            # Try opening closed facilities if they help (open all beneficial ones)
            closed = set(range(n_facilities)) - set(assignment)

            for fac in closed:
                net_benefit = -opening_costs[fac]
                reassign_map = []
                for j in range(n_clients):
                    current_cost = assign_costs[assignment[j]][j]
                    new_cost = assign_costs[fac][j]
                    if new_cost < current_cost:
                        net_benefit += current_cost - new_cost
                        reassign_map.append(j)

                if net_benefit > 0 and reassign_map:
                    for j in reassign_map:
                        assignment[j] = fac
                    improved = True

            if not improved:
                break

        return assignment

    # Try multiple starts and keep best
    best_assignment = None
    best_cost = float('inf')

    # Start 1: greedy nearest
    assignment = []
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)

    result = local_search(assignment)
    cost = sum(opening_costs[i] for i in set(result)) + sum(assign_costs[result[j]][j] for j in range(n_clients))
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Start 2: assign based on normalized opening cost (balance assignment quality with opening cost)
    assignment = []
    min_opening = min(opening_costs)
    max_opening = max(opening_costs)
    for j in range(n_clients):
        best_score = float('inf')
        best_fac = 0
        for i in range(n_facilities):
            # Normalize opening cost to 0-1 range, weight at 0.1
            normalized_opening = 0.1 * (opening_costs[i] - min_opening) / max(1, max_opening - min_opening)
            score = assign_costs[i][j] + normalized_opening
            if score < best_score:
                best_score = score
                best_fac = i
        assignment.append(best_fac)

    result = local_search(assignment)
    cost = sum(opening_costs[i] for i in set(result)) + sum(assign_costs[result[j]][j] for j in range(n_clients))
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Start 4: prefer low-cost facilities
    # Sort facilities by opening cost and bias assignments toward cheaper ones
    facility_by_cost = sorted(range(n_facilities), key=lambda i: opening_costs[i])
    assignment = []
    for j in range(n_clients):
        # Among cheapest 33% of facilities, pick the best for this client
        num_cheap = max(1, n_facilities // 3)
        cheap_facilities = facility_by_cost[:num_cheap]
        best_fac = min(cheap_facilities, key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)

    result = local_search(assignment)
    cost = sum(opening_costs[i] for i in set(result)) + sum(assign_costs[result[j]][j] for j in range(n_clients))
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Start 5: facility-centric greedy (select facilities, then assign clients)
    # Open facilities greedily based on their benefit-cost ratio
    assignment = [0] * n_clients  # Initialize with arbitrary facility
    opened = set()

    for _ in range(min(n_facilities, max(1, n_clients // 10))):  # Open ~10% of facilities
        best_facility = None
        best_benefit = -float('inf')

        for fac in range(n_facilities):
            if fac in opened:
                continue
            # Calculate benefit of opening this facility
            benefit = 0
            for j in range(n_clients):
                current_best = min(assign_costs[f][j] for f in opened) if opened else float('inf')
                if assign_costs[fac][j] < current_best:
                    benefit += current_best - assign_costs[fac][j]

            facility_value = benefit - opening_costs[fac]
            if facility_value > best_benefit:
                best_benefit = facility_value
                best_facility = fac

        if best_facility is not None and best_benefit > 0:
            opened.add(best_facility)
        else:
            break

    # Assign all clients to closest open facility, or greedy if no facilities opened
    if not opened:
        opened = {min(range(n_facilities), key=lambda i: opening_costs[i])}

    for j in range(n_clients):
        best_fac = min(opened, key=lambda i: assign_costs[i][j])
        assignment[j] = best_fac

    result = local_search(assignment)
    cost = sum(opening_costs[i] for i in set(result)) + sum(assign_costs[result[j]][j] for j in range(n_clients))
    if cost < best_cost:
        best_cost = cost
        best_assignment = result

    # Start 8-13: hybrid with different opening cost weights
    for weight in [0.01, 0.04, 0.1, 0.2, 0.4, 0.6]:
        assignment = []
        for j in range(n_clients):
            best_score = float('inf')
            best_fac = 0
            for i in range(n_facilities):
                # Combined score: assignment cost + weight * opening cost / num_clients
                score = assign_costs[i][j] + weight * opening_costs[i] / max(1, n_clients)
                if score < best_score:
                    best_score = score
                    best_fac = i
            assignment.append(best_fac)

        result = local_search(assignment)
        cost = sum(opening_costs[i] for i in set(result)) + sum(assign_costs[result[j]][j] for j in range(n_clients))
        if cost < best_cost:
            best_cost = cost
            best_assignment = result

    return best_assignment
