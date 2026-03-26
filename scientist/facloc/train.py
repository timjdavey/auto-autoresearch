"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: multi-start greedy + local search with ILS.
The agent should improve this to maximise avg_improvement across all instances.
"""

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

    def calc_cost(assignment):
        """Calculate total cost of an assignment."""
        total = 0
        open_facilities = set(assignment)
        for fac in open_facilities:
            total += opening_costs[fac]
        for j, fac in enumerate(assignment):
            total += assign_costs[fac][j]
        return total

    def one_opt_search(assignment, max_iterations=None):
        """1-opt local search."""
        if max_iterations is None:
            max_iterations = 80 if n_clients < 60 else 50
        improved = True
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            for j in range(n_clients):
                old_fac = assignment[j]
                facility_count = [0] * n_facilities
                for client_fac in assignment:
                    facility_count[client_fac] += 1

                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    delta = 0
                    delta -= assign_costs[old_fac][j]
                    delta += assign_costs[new_fac][j]

                    if facility_count[old_fac] == 1:
                        delta -= opening_costs[old_fac]
                    if facility_count[new_fac] == 0:
                        delta += opening_costs[new_fac]

                    if delta < 0:
                        assignment[j] = new_fac
                        improved = True
                        break

                if improved:
                    break

        return assignment

    def greedy_nearest(seed):
        """Assign each client to cheapest facility."""
        random.seed(seed)
        assignment = [None] * n_clients
        for j in range(n_clients):
            best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
            assignment[j] = best_fac
        return one_opt_search(assignment)

    def facility_first_init(seed):
        """Open facilities in order of cost, assign clients greedily."""
        random.seed(seed)
        sorted_facs = sorted(range(n_facilities), key=lambda i: opening_costs[i])
        assignment = [None] * n_clients
        open_facs = set()
        for fac in sorted_facs[:max(1, n_facilities // 2)]:
            open_facs.add(fac)
        for j in range(n_clients):
            best_fac = min(open_facs, key=lambda i: assign_costs[i][j])
            assignment[j] = best_fac
        return one_opt_search(assignment)

    def load_balanced_init(seed):
        """Distribute clients evenly across facilities."""
        random.seed(seed)
        assignment = [None] * n_clients
        facility_load = [0] * n_facilities
        client_order = sorted(range(n_clients),
                            key=lambda j: min(assign_costs[i][j] for i in range(n_facilities)))
        for j in client_order:
            best_fac = min(range(n_facilities),
                         key=lambda i: (opening_costs[i] + assign_costs[i][j]) / (facility_load[i] + 1))
            assignment[j] = best_fac
            facility_load[best_fac] += 1
        return one_opt_search(assignment)

    def cost_weighted_init(seed, weight=0.5):
        """Greedy with cost-aware weight."""
        random.seed(seed)
        assignment = [None] * n_clients
        for j in range(n_clients):
            best_fac = min(range(n_facilities),
                         key=lambda i: weight * (opening_costs[i] * n_facilities / n_clients) +
                                     (1 - weight) * assign_costs[i][j])
            assignment[j] = best_fac
        return one_opt_search(assignment)

    def cluster_based_init(seed):
        """Cluster-based initialization."""
        random.seed(seed)
        assignment = [None] * n_clients
        client_primary_fac = [min(range(n_facilities), key=lambda i: assign_costs[i][j])
                             for j in range(n_clients)]
        clusters = [[] for _ in range(n_facilities)]
        for j in range(n_clients):
            clusters[client_primary_fac[j]].append(j)
        cluster_assignment = {}
        cluster_order = sorted(range(n_facilities),
                              key=lambda fac: len(clusters[fac]),
                              reverse=True)
        for cluster_fac in cluster_order:
            if not clusters[cluster_fac]:
                continue
            best_target = min(range(n_facilities),
                            key=lambda target: sum(assign_costs[target][j] for j in clusters[cluster_fac]))
            cluster_assignment[cluster_fac] = best_target
        for fac_id, cluster_clients in enumerate(clusters):
            target_fac = cluster_assignment.get(fac_id, fac_id)
            for j in cluster_clients:
                assignment[j] = target_fac
        return one_opt_search(assignment)

    def facility_closing_phase(assignment):
        """Try closing facilities."""
        facility_count = [0] * n_facilities
        for fac in assignment:
            facility_count[fac] += 1
        improved = True
        max_iterations = 20
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            for close_fac in range(n_facilities):
                if facility_count[close_fac] == 0:
                    continue
                delta = -opening_costs[close_fac]
                best_reassignment = {}
                valid = True
                for j in range(n_clients):
                    if assignment[j] != close_fac:
                        continue
                    best_new_fac = None
                    best_delta = 0
                    for new_fac in range(n_facilities):
                        if new_fac == close_fac:
                            continue
                        move_delta = assign_costs[new_fac][j] - assign_costs[close_fac][j]
                        if facility_count[new_fac] == 0:
                            move_delta += opening_costs[new_fac]
                        if best_new_fac is None or move_delta < best_delta:
                            best_new_fac = new_fac
                            best_delta = move_delta
                    if best_new_fac is None:
                        valid = False
                        break
                    best_reassignment[j] = best_new_fac
                    delta += best_delta
                if valid and delta < 0:
                    for j, new_fac in best_reassignment.items():
                        assignment[j] = new_fac
                        facility_count[close_fac] -= 1
                        facility_count[new_fac] += 1
                    improved = True
                    break
        return assignment

    def client_2opt_exchange(assignment, max_iterations=None):
        """2-opt on clients."""
        if max_iterations is None:
            max_iterations = 25 if n_clients < 60 else 15
        improved = True
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            for j1 in range(n_clients):
                for j2 in range(j1 + 1, n_clients):
                    fac1 = assignment[j1]
                    fac2 = assignment[j2]
                    if fac1 == fac2:
                        continue
                    delta = 0
                    delta -= assign_costs[fac1][j1]
                    delta += assign_costs[fac2][j1]
                    delta -= assign_costs[fac2][j2]
                    delta += assign_costs[fac1][j2]
                    facility_count = [0] * n_facilities
                    for client_fac in assignment:
                        facility_count[client_fac] += 1
                    if facility_count[fac1] == 1:
                        delta -= opening_costs[fac1]
                    if facility_count[fac2] == 1:
                        delta -= opening_costs[fac2]
                    if delta < 0:
                        assignment[j1] = fac2
                        assignment[j2] = fac1
                        improved = True
                        break
                if improved:
                    break
        return assignment

    def perturbation(assignment, k):
        """Perturb k clients."""
        perturbed = assignment[:]
        client_indices = list(range(n_clients))
        random.shuffle(client_indices)
        for j in client_indices[:k]:
            new_fac = random.randint(0, n_facilities - 1)
            perturbed[j] = new_fac
        return perturbed

    def ils_search(initial_assignment, num_perturbations=None):
        """ILS: perturb and re-optimize."""
        if num_perturbations is None:
            num_perturbations = 6 if n_clients < 60 else 3
        best_assignment = initial_assignment[:]
        best_cost = calc_cost(best_assignment)
        for iteration in range(num_perturbations):
            k = max(1, n_clients // 20)
            perturbed = perturbation(best_assignment, k)
            optimized = one_opt_search(perturbed)
            optimized = facility_closing_phase(optimized)
            cost = calc_cost(optimized)
            if cost < best_cost:
                best_cost = cost
                best_assignment = optimized
        return best_assignment

    # Multi-start
    best_assignment = None
    best_cost = float('inf')

    if n_clients < 60:
        seeds = [1, 42, 123, 456, 789, 999, 2024, 333, 777, 2025, 555, 111, 888, 3333]
        initializers = [greedy_nearest, facility_first_init, load_balanced_init, cluster_based_init]
    else:
        seeds = [1, 42, 123, 456, 789, 999, 2024]
        initializers = [greedy_nearest, facility_first_init, load_balanced_init]

    weights = [0.2, 0.4, 0.6, 0.8]

    for seed in seeds:
        for init_func in initializers:
            assignment = init_func(seed)
            assignment = facility_closing_phase(assignment)
            assignment = client_2opt_exchange(assignment)
            assignment = ils_search(assignment)
            cost = calc_cost(assignment)
            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment

        for weight in weights:
            assignment = cost_weighted_init(seed, weight)
            assignment = facility_closing_phase(assignment)
            assignment = client_2opt_exchange(assignment)
            assignment = ils_search(assignment)
            cost = calc_cost(assignment)
            if cost < best_cost:
                best_cost = cost
                best_assignment = assignment

    return best_assignment
