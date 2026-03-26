"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


def solve(flow: list[list[int]], distance: list[list[int]]) -> list[int]:
    """
    Solve the Quadratic Assignment Problem.

    Assign n facilities to n locations to minimise total cost:
        cost = sum over all (i,j) of flow[i][j] * distance[assignment[i]][assignment[j]]

    Args:
        flow: n x n symmetric matrix. flow[i][j] = flow between facility i and j.
        distance: n x n symmetric matrix. distance[k][l] = distance between location k and l.

    Returns:
        assignment: list of length n where assignment[i] = location assigned to
                    facility i. Must be a permutation of 0..n-1.
    """
    import random
    import math

    n = len(flow)
    if n == 0:
        return []
    if n == 1:
        return [0]

    def compute_cost(assignment):
        """Compute total QAP cost for an assignment."""
        return sum(
            flow[i][j] * distance[assignment[i]][assignment[j]]
            for i in range(n) for j in range(n)
        )

    def greedy_construct(facility_order, use_probabilistic=False):
        """Greedy construction with optional probabilistic tie-breaking."""
        assignment = [-1] * n
        available = set(range(n))

        for facility in facility_order:
            costs = {}

            for location in available:
                cost = 0
                for other_facility in range(n):
                    if assignment[other_facility] != -1:
                        other_location = assignment[other_facility]
                        cost += flow[facility][other_facility] * distance[location][other_location]
                        cost += flow[other_facility][facility] * distance[other_location][location]

                costs[location] = cost

            if use_probabilistic and len(available) > 1:
                # Softmax selection: transform costs to probabilities
                min_cost = min(costs.values())
                max_cost = max(costs.values())
                cost_range = max_cost - min_cost + 1e-9

                # Temperature controls exploration: higher temp = more random
                temp = cost_range / 3.0

                # Compute softmax probabilities (inverted: lower cost = higher prob)
                exp_scores = {}
                sum_exp = 0
                for loc, cost in costs.items():
                    # Invert: normalize to [0,1] and negate
                    normalized = (cost - min_cost) / cost_range
                    exp_val = math.exp(-normalized / temp)
                    exp_scores[loc] = exp_val
                    sum_exp += exp_val

                # Select location probabilistically
                r = random.random() * sum_exp
                cumsum = 0
                best_location = min(costs, key=costs.get)  # fallback
                for loc, exp_val in exp_scores.items():
                    cumsum += exp_val
                    if cumsum >= r:
                        best_location = loc
                        break
            else:
                # Deterministic: pick best location
                best_location = min(costs, key=costs.get)

            assignment[facility] = best_location
            available.remove(best_location)

        return assignment

    def local_search_2opt(assignment):
        """2-opt local search with delta cost calculation."""
        def cost_delta(i, j, assignment):
            loc_i = assignment[i]
            loc_j = assignment[j]
            delta = 0

            for k in range(n):
                if k != i and k != j:
                    loc_k = assignment[k]
                    delta += flow[i][k] * (distance[loc_j][loc_k] - distance[loc_i][loc_k])
                    delta += flow[k][i] * (distance[loc_k][loc_j] - distance[loc_k][loc_i])
                    delta += flow[j][k] * (distance[loc_i][loc_k] - distance[loc_j][loc_k])
                    delta += flow[k][j] * (distance[loc_k][loc_i] - distance[loc_k][loc_j])

            delta += flow[i][j] * (distance[loc_j][loc_i] - distance[loc_i][loc_j])
            delta += flow[j][i] * (distance[loc_i][loc_j] - distance[loc_j][loc_i])

            return delta

        improved = True
        # Size-aware iteration limit: increase slightly to use freed time budget
        if n > 60:
            max_iterations = 4000  # Was 3000, now 4000 (time freed from reduced perturbation)
        elif n > 50:
            max_iterations = 5500  # Was 5000, now 5500
        else:
            max_iterations = 5500  # Was 5000, now 5500
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(n):
                for j in range(i + 1, n):
                    delta = cost_delta(i, j, assignment)
                    if delta < 0:
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        improved = True

        return assignment

    def simulated_annealing(initial_assignment, initial_temp=1000.0, cooling_rate=0.995, iterations=5000):
        """Simulated annealing for QAP."""
        current = initial_assignment[:]
        current_cost = compute_cost(current)
        best = current[:]
        best_cost = current_cost

        temp = initial_temp
        iteration = 0

        while temp > 0.01 and iteration < iterations:
            # Random 2-opt move
            i, j = random.sample(range(n), 2)
            current[i], current[j] = current[j], current[i]
            new_cost = compute_cost(current)
            delta = new_cost - current_cost

            # Metropolis criterion
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current_cost = new_cost
                if new_cost < best_cost:
                    best = current[:]
                    best_cost = new_cost
            else:
                # Revert move
                current[i], current[j] = current[j], current[i]

            temp *= cooling_rate
            iteration += 1

        return best

    def local_search_3opt(assignment, max_iterations=10):
        """3-opt local search: try swapping three facilities. Limited to small instances."""
        # Only apply 3-opt on small instances where it's affordable
        if n > 50:
            return assignment

        def cost_delta_3opt(i, j, k, assignment):
            """Compute cost change for 3-way swap of facilities i, j, k."""
            loc_i, loc_j, loc_k = assignment[i], assignment[j], assignment[k]
            delta = 0

            # Try all 6 permutations (actually 3! = 6 rearrangements)
            # Current: i→loc_i, j→loc_j, k→loc_k
            # New permutation: i→loc_j, j→loc_k, k→loc_i
            new_locs = [loc_j, loc_k, loc_i]  # indices: [i, j, k]

            for a in range(n):
                if a not in [i, j, k]:
                    loc_a = assignment[a]
                    # Old cost
                    delta -= flow[i][a] * distance[loc_i][loc_a]
                    delta -= flow[a][i] * distance[loc_a][loc_i]
                    delta -= flow[j][a] * distance[loc_j][loc_a]
                    delta -= flow[a][j] * distance[loc_a][loc_j]
                    delta -= flow[k][a] * distance[loc_k][loc_a]
                    delta -= flow[a][k] * distance[loc_a][loc_k]
                    # New cost
                    delta += flow[i][a] * distance[new_locs[0]][loc_a]
                    delta += flow[a][i] * distance[loc_a][new_locs[0]]
                    delta += flow[j][a] * distance[new_locs[1]][loc_a]
                    delta += flow[a][j] * distance[loc_a][new_locs[1]]
                    delta += flow[k][a] * distance[new_locs[2]][loc_a]
                    delta += flow[a][k] * distance[loc_a][new_locs[2]]

            # Internal costs
            delta -= flow[i][j] * distance[loc_i][loc_j]
            delta -= flow[j][i] * distance[loc_j][loc_i]
            delta -= flow[j][k] * distance[loc_j][loc_k]
            delta -= flow[k][j] * distance[loc_k][loc_j]
            delta -= flow[i][k] * distance[loc_i][loc_k]
            delta -= flow[k][i] * distance[loc_k][loc_i]

            delta += flow[i][j] * distance[new_locs[0]][new_locs[1]]
            delta += flow[j][i] * distance[new_locs[1]][new_locs[0]]
            delta += flow[j][k] * distance[new_locs[1]][new_locs[2]]
            delta += flow[k][j] * distance[new_locs[2]][new_locs[1]]
            delta += flow[i][k] * distance[new_locs[0]][new_locs[2]]
            delta += flow[k][i] * distance[new_locs[2]][new_locs[0]]

            return delta

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(n):
                for j in range(i + 1, n):
                    for k in range(j + 1, n):
                        delta = cost_delta_3opt(i, j, k, assignment)
                        if delta < 0:
                            # Apply swap: i→loc_j, j→loc_k, k→loc_i
                            assignment[i], assignment[j], assignment[k] = assignment[j], assignment[k], assignment[i]
                            improved = True

        return assignment

    # Multi-start with size-aware perturbation
    best_assignment = None
    best_cost = float('inf')

    # Size-aware: adjust number of starts and perturbation based on problem size
    # Small instances (n≤50): more starts, strong perturbation
    # Large instances (n>60): same starts but fewer perturbation rounds to stay in time budget
    if n <= 50:
        num_starts = 60
        perturbation_rounds = 3
        perturbation_strength = max(3, n // 20)
    elif n <= 60:
        num_starts = 60
        perturbation_rounds = 2
        perturbation_strength = max(3, n // 20)
    else:
        num_starts = 60  # Keep all starts
        perturbation_rounds = 1  # Reduced from 2 to 1 for large instances
        perturbation_strength = max(1, n // 30)

    for start in range(num_starts):
        facility_order = list(range(n))
        random.shuffle(facility_order)
        # Use probabilistic construction for 80% of starts (more diverse), deterministic for 20% (baseline)
        use_prob = random.random() < 0.8
        assignment = greedy_construct(facility_order, use_probabilistic=use_prob)
        assignment = local_search_2opt(assignment)

        cost = compute_cost(assignment)

        if cost < best_cost:
            best_cost = cost
            best_assignment = assignment[:]

        # Size-aware perturbation: smaller swaps for large instances, more for small
        for perturbation_round in range(perturbation_rounds):
            perturbed = best_assignment[:]
            strength = perturbation_strength * (perturbation_round + 1)
            for _ in range(min(strength, n // 3)):  # Cap at n/3 swaps
                i, j = random.sample(range(n), 2)
                perturbed[i], perturbed[j] = perturbed[j], perturbed[i]

            perturbed = local_search_2opt(perturbed)
            cost_perturbed = compute_cost(perturbed)

            if cost_perturbed < best_cost:
                best_cost = cost_perturbed
                best_assignment = perturbed[:]

    return best_assignment
