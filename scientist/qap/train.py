"""
train.py — QAP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(flow, distance)` that takes two square
matrices and returns an assignment as a list of location indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


import random
import time


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
    n = len(flow)
    if n == 0:
        return []
    if n == 1:
        return [0]

    start_time = time.time()
    time_limit = 55  # Leave 5s margin before hard 60s limit

    def compute_cost(assignment):
        """Compute QAP objective."""
        cost = 0
        for i in range(n):
            pi = assignment[i]
            for j in range(n):
                cost += flow[i][j] * distance[pi][assignment[j]]
        return cost

    def nearest_neighbor(start_facility=0, randomized=False):
        """Greedy nearest neighbor construction with optional randomization."""
        assignment = [-1] * n
        unassigned_locations = set(range(n))
        assignment[start_facility] = unassigned_locations.pop()
        assigned_facilities = {start_facility}

        while len(assigned_facilities) < n:
            # Find candidates: facilities with high flow to assigned facilities
            candidates = []
            max_score = -1
            for f in range(n):
                if f in assigned_facilities:
                    continue
                score = sum(flow[f][g] for g in assigned_facilities)
                candidates.append((score, f))
                if score > max_score:
                    max_score = score

            if randomized and len(candidates) > 1:
                # In randomized mode, consider top candidates (within 20% of best)
                threshold = max_score * 0.8
                top_candidates = [f for s, f in candidates if s >= threshold]
                best_facility = random.choice(top_candidates) if top_candidates else candidates[0][1]
            else:
                best_facility = max(candidates, key=lambda x: x[0])[1]

            # Find location that minimizes cost to assigned locations
            best_location = -1
            best_cost = float('inf')
            for loc in unassigned_locations:
                cost = sum(flow[best_facility][g] * distance[loc][assignment[g]]
                          for g in assigned_facilities)
                if cost < best_cost:
                    best_cost = cost
                    best_location = loc

            assignment[best_facility] = best_location
            unassigned_locations.remove(best_location)
            assigned_facilities.add(best_facility)

        return assignment

    def two_opt(assignment):
        """2-opt local search with first-improvement strategy (faster exploration)."""
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            current_cost = compute_cost(assignment)

            for i in range(n):
                for j in range(i + 2, n):
                    # Swap and compute cost change
                    assignment[i], assignment[j] = assignment[j], assignment[i]
                    new_cost = compute_cost(assignment)
                    assignment[i], assignment[j] = assignment[j], assignment[i]

                    if new_cost < current_cost:
                        # Accept first improvement found
                        assignment[i], assignment[j] = assignment[j], assignment[i]
                        improved = True
                        break

                if improved:
                    break

        return assignment

    # Multi-start: try multiple randomized nearest neighbor constructions
    best_assignment = None
    best_cost = float('inf')
    num_starts = 6

    for start_idx in range(num_starts):
        if time.time() - start_time >= time_limit:
            break

        # Use randomized NN for diversity
        candidate = nearest_neighbor(start_facility=start_idx % n, randomized=True)
        candidate = two_opt(candidate)

        cost = compute_cost(candidate)
        if cost < best_cost:
            best_cost = cost
            best_assignment = candidate

    return best_assignment if best_assignment is not None else nearest_neighbor(start_facility=0, randomized=False)
