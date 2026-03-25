"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: multi-weight greedy + 1-opt + facility cost strategies.
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

    def run_local_search(assignment, max_iter, use_first_improvement=False):
        improved = True
        iterations = 0

        while improved and iterations < max_iter:
            improved = False
            iterations += 1

            # Count clients per facility
            facility_load = [0] * n_facilities
            for j in range(n_clients):
                facility_load[assignment[j]] += 1

            # Try reassigning each client
            for j in range(n_clients):
                old_fac = assignment[j]
                old_assign_cost = assign_costs[old_fac][j]

                # Cost of moving away from old facility
                removal_saving = 0
                if facility_load[old_fac] == 1:
                    removal_saving = opening_costs[old_fac]

                # Try all facilities
                best_improvement = 0
                best_new_fac = old_fac

                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    new_assign_cost = assign_costs[new_fac][j]
                    assign_delta = new_assign_cost - old_assign_cost

                    # Cost of moving to new facility
                    opening_delta = 0
                    if facility_load[new_fac] == 0:
                        opening_delta = opening_costs[new_fac]

                    # Net improvement
                    improvement = removal_saving - assign_delta - opening_delta

                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_new_fac = new_fac

                        # First improvement: take the first improving move
                        if use_first_improvement and best_improvement > 0:
                            break

                if best_improvement > 0:
                    assignment[j] = best_new_fac
                    facility_load[old_fac] -= 1
                    facility_load[best_new_fac] += 1
                    improved = True

        return assignment

    def run_2opt_facilities(assignment, max_attempts=50):
        """2-opt on facility pairs: try swapping all clients between pairs of facilities."""
        improved = True
        attempts = 0

        while improved and attempts < max_attempts:
            improved = False
            attempts += 1
            open_facilities = list(set(assignment))

            for i in range(len(open_facilities)):
                for j in range(i + 1, len(open_facilities)):
                    fac1, fac2 = open_facilities[i], open_facilities[j]

                    # Get clients assigned to each facility
                    clients_f1 = [c for c in range(n_clients) if assignment[c] == fac1]
                    clients_f2 = [c for c in range(n_clients) if assignment[c] == fac2]

                    if not clients_f1 or not clients_f2:
                        continue

                    # Calculate cost before and after swap
                    current_cost = sum(assign_costs[fac1][c] for c in clients_f1) + \
                                  sum(assign_costs[fac2][c] for c in clients_f2)
                    swap_cost = sum(assign_costs[fac2][c] for c in clients_f1) + \
                               sum(assign_costs[fac1][c] for c in clients_f2)

                    if swap_cost < current_cost:
                        # Apply swap
                        for c in clients_f1:
                            assignment[c] = fac2
                        for c in clients_f2:
                            assignment[c] = fac1
                        improved = True
                        break

                if improved:
                    break

        return assignment

    def run_facility_closing(assignment, max_attempts):
        """Try closing facilities and reassigning clients to other open facilities."""
        improved = True
        attempts = 0

        while improved and attempts < max_attempts:
            improved = False
            attempts += 1

            open_facilities = set(assignment)

            for fac_to_close in open_facilities:
                # Find all clients assigned to this facility
                clients_to_move = [j for j in range(n_clients) if assignment[j] == fac_to_close]

                if not clients_to_move:
                    continue

                # Try reassigning each client to the best other open facility
                saving = opening_costs[fac_to_close]
                cost_increase = 0

                best_facilities = {}
                for j in clients_to_move:
                    old_cost = assign_costs[fac_to_close][j]
                    best_new_fac = min(
                        (f for f in open_facilities if f != fac_to_close),
                        key=lambda f: assign_costs[f][j],
                        default=None
                    )
                    if best_new_fac is None:
                        break
                    best_facilities[j] = best_new_fac
                    cost_increase += assign_costs[best_new_fac][j] - old_cost
                else:
                    # All clients can be reassigned
                    if cost_increase < saving:
                        # This closing is beneficial
                        for j, new_fac in best_facilities.items():
                            assignment[j] = new_fac
                        improved = True
                        break

        return assignment

    def run_3opt_clients(assignment, max_attempts=30):
        """3-opt on clients: try reassigning triplets of clients to different facilities."""
        improved = True
        attempts = 0

        while improved and attempts < max_attempts:
            improved = False
            attempts += 1

            # Try reassigning triplets of clients
            for j1 in range(n_clients):
                for j2 in range(j1 + 1, min(j1 + 8, n_clients)):  # Limit search window
                    for j3 in range(j2 + 1, min(j2 + 8, n_clients)):
                        old_facs = (assignment[j1], assignment[j2], assignment[j3])
                        old_cost = (assign_costs[old_facs[0]][j1] +
                                   assign_costs[old_facs[1]][j2] +
                                   assign_costs[old_facs[2]][j3])

                        # Try all permutations of reassigning these 3 clients
                        best_delta = 0
                        best_config = old_facs

                        # Try all 6 permutations of reassigning to 3 facilities
                        for perm_idx in range(6):
                            if perm_idx == 0:  # (j1→f1, j2→f2, j3→f3) - original
                                continue
                            # Generate permutation of facilities
                            perm = [(old_facs[0], old_facs[1], old_facs[2]),
                                   (old_facs[0], old_facs[2], old_facs[1]),
                                   (old_facs[1], old_facs[0], old_facs[2]),
                                   (old_facs[1], old_facs[2], old_facs[0]),
                                   (old_facs[2], old_facs[0], old_facs[1]),
                                   (old_facs[2], old_facs[1], old_facs[0])][perm_idx]

                            new_cost = (assign_costs[perm[0]][j1] +
                                       assign_costs[perm[1]][j2] +
                                       assign_costs[perm[2]][j3])
                            delta = old_cost - new_cost

                            if delta > best_delta:
                                best_delta = delta
                                best_config = perm

                        if best_delta > 0:
                            assignment[j1] = best_config[0]
                            assignment[j2] = best_config[1]
                            assignment[j3] = best_config[2]
                            improved = True
                            break

                    if improved:
                        break
                if improved:
                    break

        return assignment

    def run_oropt(assignment, max_iterations=50):
        """Or-opt: relocate sequences of 2-3 clients to different facilities."""
        import random
        improved = True
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            # Randomize client order for order-independence
            clients = list(range(n_clients))
            random.shuffle(clients)

            # Try moving sequences of 2-3 clients
            for seq_len in [2, 3]:
                for i in range(len(clients) - seq_len + 1):
                    client_seq = clients[i:i+seq_len]
                    # Get current facility for first client in sequence
                    current_fac = assignment[client_seq[0]]

                    # Check if all clients in sequence are in same facility
                    if not all(assignment[c] == current_fac for c in client_seq):
                        continue

                    # Try moving entire sequence to each other facility
                    current_cost = sum(assign_costs[current_fac][c] for c in client_seq)

                    for new_fac in range(n_facilities):
                        if new_fac == current_fac:
                            continue

                        new_cost = sum(assign_costs[new_fac][c] for c in client_seq)

                        # Compute opening/closing cost deltas
                        facility_load = [0] * n_facilities
                        for j in range(n_clients):
                            facility_load[assignment[j]] += 1

                        opening_delta = 0
                        # Cost to open new_fac if needed
                        if facility_load[new_fac] == 0:
                            opening_delta += opening_costs[new_fac]
                        # Savings from potentially closing current_fac
                        if facility_load[current_fac] == seq_len:
                            opening_delta -= opening_costs[current_fac]

                        assignment_delta = new_cost - current_cost
                        total_delta = opening_delta + assignment_delta

                        if total_delta < 0:
                            # Apply move
                            for c in client_seq:
                                assignment[c] = new_fac
                            improved = True
                            break

                    if improved:
                        break

                if improved:
                    break

        return assignment

    def perturb_assignment(assignment, num_changes):
        """Randomly reassign some clients to create perturbation."""
        import random
        perturbed = assignment[:]
        for _ in range(num_changes):
            j = random.randint(0, n_clients - 1)
            # Assign to a random facility
            fac = random.randint(0, n_facilities - 1)
            perturbed[j] = fac
        return perturbed

    def run_simulated_annealing(initial_assignment, max_iterations=500):
        """Simulated annealing to escape local optima."""
        import random
        import math

        current_assignment = initial_assignment[:]
        current_cost = evaluate_assignment(current_assignment)
        best_assignment = current_assignment[:]
        best_cost = current_cost

        temperature = current_cost * 0.1  # Scale temp with problem size
        cooling_rate = 0.98
        min_temp = 1.0

        for iteration in range(max_iterations):
            if temperature < min_temp:
                break

            # Try a random client reassignment
            j = random.randint(0, n_clients - 1)
            old_fac = current_assignment[j]
            new_fac = random.randint(0, n_facilities - 1)

            if new_fac == old_fac:
                continue

            # Evaluate change
            old_assign_cost = assign_costs[old_fac][j]
            new_assign_cost = assign_costs[new_fac][j]
            assign_delta = new_assign_cost - old_assign_cost

            # Opening cost delta
            facility_load = [0] * n_facilities
            for jj in range(n_clients):
                facility_load[current_assignment[jj]] += 1

            opening_delta = 0
            if facility_load[new_fac] == 0:
                opening_delta = opening_costs[new_fac]
            if facility_load[old_fac] == 1:
                opening_delta -= opening_costs[old_fac]

            delta_cost = assign_delta + opening_delta

            # Accept or reject
            if delta_cost < 0 or random.random() < math.exp(-delta_cost / temperature):
                current_assignment[j] = new_fac
                current_cost += delta_cost

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_assignment = current_assignment[:]

            temperature *= cooling_rate

        return best_assignment


    def evaluate_assignment(assignment):
        open_facilities = set(assignment)
        cost = sum(opening_costs[f] for f in open_facilities)
        cost += sum(assign_costs[assignment[j]][j] for j in range(n_clients))
        return cost

    best_assignment = None
    best_cost = float('inf')

    # --- Strategy 1: Multi-weight greedy initialization (expanded range) ---
    # Include extreme weights to explore different facility-opening strategies
    weights = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.3, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.5, 8.0, 10.0, 15.0, 20.0, 50.0, 100.0]
    for weight in weights:
        assignment = []
        for j in range(n_clients):
            best_fac = min(
                range(n_facilities),
                key=lambda i: assign_costs[i][j] + weight * opening_costs[i] / max(1, n_clients)
            )
            assignment.append(best_fac)

        assignment = run_local_search(assignment, min(2000, n_clients * 60), use_first_improvement=False)
        assignment = run_facility_closing(assignment, 100)
        assignment = run_local_search(assignment, min(1500, n_clients * 50), use_first_improvement=False)
        cost = evaluate_assignment(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # --- Strategy 2: Greedy-nearest (no weights) with first-improvement ---
    assignment = [min(range(n_facilities), key=lambda i: assign_costs[i][j]) for j in range(n_clients)]
    assignment = run_local_search(assignment, min(800, n_clients * 25), use_first_improvement=True)
    assignment = run_facility_closing(assignment, 50)
    assignment = run_local_search(assignment, min(400, n_clients * 12), use_first_improvement=True)
    cost = evaluate_assignment(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment

    # --- Strategy 3: Facility-cost prioritized (prefer cheap facilities) with first-improvement ---
    for cost_weight in [2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0]:
        assignment = []
        facility_load = [0] * n_facilities

        for j in range(n_clients):
            best_fac = min(
                range(n_facilities),
                key=lambda i: assign_costs[i][j] + (opening_costs[i] if facility_load[i] == 0 else 0) / cost_weight
            )
            assignment.append(best_fac)
            facility_load[best_fac] += 1

        assignment = run_local_search(assignment, min(500, n_clients * 15), use_first_improvement=True)
        assignment = run_facility_closing(assignment, 20)
        assignment = run_local_search(assignment, min(250, n_clients * 8), use_first_improvement=True)
        cost = evaluate_assignment(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # --- Strategy 4: Perturbation + re-optimization from best solution ---
    # Try random perturbations of the best solution found so far
    for _ in range(3):
        assignment = perturb_assignment(best_assignment, max(1, n_clients // 10))
        assignment = run_local_search(assignment, min(800, n_clients * 25), use_first_improvement=True)
        assignment = run_facility_closing(assignment, 50)
        assignment = run_local_search(assignment, min(400, n_clients * 12), use_first_improvement=True)
        cost = evaluate_assignment(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # --- Strategy 5: 2-opt facility pair swaps ---
    # Different neighborhood to escape local optimum
    assignment = best_assignment[:]
    assignment = run_2opt_facilities(assignment, max_attempts=100)
    assignment = run_local_search(assignment, min(500, n_clients * 15), use_first_improvement=False)
    cost = evaluate_assignment(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment

    # --- Strategy 6: Or-opt on best solution (new diversification) ---
    # Or-opt relocates sequences of 2-3 clients to different facilities
    # This is a different neighborhood from 1-opt (single client) and 2-opt (full facility swaps)
    assignment = best_assignment[:]
    assignment = run_oropt(assignment, max_iterations=100)
    assignment = run_local_search(assignment, min(500, n_clients * 15), use_first_improvement=False)
    assignment = run_facility_closing(assignment, 30)
    assignment = run_local_search(assignment, min(300, n_clients * 10), use_first_improvement=False)
    cost = evaluate_assignment(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment

    # --- Strategy 7: Multiple Or-opt passes with stronger local search ---
    # Aggressive Or-opt with more iterations
    for _ in range(2):
        assignment = perturb_assignment(best_assignment, max(2, n_clients // 8))
        assignment = run_oropt(assignment, max_iterations=150)
        assignment = run_local_search(assignment, min(800, n_clients * 25), use_first_improvement=False)
        assignment = run_facility_closing(assignment, 50)
        cost = evaluate_assignment(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    # --- Strategy 8: Facility-constrained initialization (novel approach) ---
    # Force a fixed set of facilities to be open and optimize client assignments
    # Try different numbers of facilities and random selections
    import random
    for num_facilities_to_use in [max(1, n_facilities // 4), n_facilities // 3, n_facilities // 2]:
        for attempt in range(2):
            # Randomly select facilities to use
            selected_facilities = random.sample(range(n_facilities), num_facilities_to_use)

            # Assign each client to the best facility among selected ones
            assignment = []
            for j in range(n_clients):
                best_fac = min(
                    selected_facilities,
                    key=lambda i: assign_costs[i][j]
                )
                assignment.append(best_fac)

            # Optimize with strong local search
            assignment = run_local_search(assignment, min(800, n_clients * 25), use_first_improvement=False)
            assignment = run_facility_closing(assignment, 50)
            assignment = run_local_search(assignment, min(500, n_clients * 15), use_first_improvement=False)
            cost = evaluate_assignment(assignment)
            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment

    # --- Strategy 8b: 3-opt diversification on best solution ---
    # Try 3-opt moves as a different neighborhood than 1-opt and 2-opt
    assignment = best_assignment[:]
    assignment = run_3opt_clients(assignment, max_attempts=50)
    assignment = run_local_search(assignment, min(500, n_clients * 15), use_first_improvement=False)
    assignment = run_facility_closing(assignment, 30)
    cost = evaluate_assignment(assignment)
    if cost < best_cost:
        best_cost = cost
        best_assignment = assignment

    # --- Strategy 9: Pure random initialization with aggressive chained optimization ---
    # Completely random starting point (not greedy), then heavy optimization
    for _ in range(3):
        # Random assignment: each client to random facility
        assignment = [random.randint(0, n_facilities - 1) for _ in range(n_clients)]

        # Chain multiple optimization phases without resetting
        assignment = run_local_search(assignment, min(1000, n_clients * 30), use_first_improvement=False)
        assignment = run_facility_closing(assignment, 60)
        assignment = run_local_search(assignment, min(1000, n_clients * 30), use_first_improvement=False)
        assignment = run_oropt(assignment, max_iterations=200)
        assignment = run_local_search(assignment, min(800, n_clients * 25), use_first_improvement=False)

        cost = evaluate_assignment(assignment)
        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment

    return best_assignment

