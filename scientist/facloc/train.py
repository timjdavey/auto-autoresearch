"""
train.py — Facility location solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(opening_costs, assign_costs)` that takes
facility opening costs and an assignment cost matrix, and returns an assignment
of clients to facilities.

Current implementation: greedy nearest (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time


def _solve_single(opening_costs: list[int], assign_costs: list[list[int]]) -> list[int]:
    """Single solver run with current randomness state."""
    start_total = time.time()
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0

    if n_clients == 0:
        return []
    if n_facilities == 1:
        return [0] * n_clients

    # Timing accumulators
    time_opening = 0
    time_search = 0
    time_closing = 0

    def calc_cost(assign):
        cost = 0
        open_facilities = set(assign)
        for fac in open_facilities:
            cost += opening_costs[fac]
        for j, fac in enumerate(assign):
            cost += assign_costs[fac][j]
        return cost

    # Facility-opening heuristic: incrementally open facilities
    # Start with random facility, then greedily add facilities that reduce cost most
    best_assignment = None
    best_cost = float('inf')

    # Try multiple starting facilities (explore breadth over depth)
    num_starts = min(n_facilities * 2, 100)  # Doubled from 50
    # Order facilities by opening cost (cheaper first) to explore cost-aware starting points
    facility_order = sorted(range(n_facilities), key=lambda f: opening_costs[f])
    for start_idx in range(num_starts):
        start_fac = facility_order[start_idx % n_facilities]
        assignment = [start_fac] * n_clients

        # Phase 1: Incrementally open facilities with marginal cost-benefit analysis
        phase1_start = time.time()
        open_facilities = {start_fac}
        improved = True
        open_iterations = 0

        while improved and open_iterations < 50:
            improved = False
            open_iterations += 1
            current_cost = calc_cost(assignment)

            best_delta = 0
            best_fac = None

            # Evaluate all closed facilities
            for new_fac in range(n_facilities):
                if new_fac in open_facilities:
                    continue
                # Assign clients that benefit from this facility
                temp_assignment = assignment[:]
                affected_clients = 0
                for j in range(n_clients):
                    if assign_costs[new_fac][j] < assign_costs[assignment[j]][j]:
                        temp_assignment[j] = new_fac
                        affected_clients += 1

                new_cost = calc_cost(temp_assignment)
                delta = current_cost - new_cost

                # Pick by best delta divided by opening cost (favor high-impact, low-cost facilities)
                if opening_costs[new_fac] > 0:
                    score = delta / opening_costs[new_fac]
                else:
                    score = delta  # If cost is 0, just use delta

                if score > best_delta:
                    best_delta = score
                    best_fac = new_fac

            if best_fac is not None:
                # Apply best facility
                for j in range(n_clients):
                    if assign_costs[best_fac][j] < assign_costs[assignment[j]][j]:
                        assignment[j] = best_fac

                open_facilities.add(best_fac)
                improved = True

        time_opening += time.time() - phase1_start

        # Phase 2: 1-opt local search (reduced iterations for more starts)
        phase2_start = time.time()
        improved = True
        iterations = 0
        max_iterations = 1000  # Reduced from 2000 to balance more starts

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            current_cost = calc_cost(assignment)

            for j in range(n_clients):
                old_fac = assignment[j]
                for new_fac in range(n_facilities):
                    if new_fac == old_fac:
                        continue

                    assignment[j] = new_fac
                    new_cost = calc_cost(assignment)

                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                        break
                    else:
                        assignment[j] = old_fac

        time_search += time.time() - phase2_start

        # Phase 3: Facility closing
        phase3_start = time.time()
        improved = True
        close_iterations = 0

        while improved and close_iterations < 50:
            improved = False
            close_iterations += 1
            current_cost = calc_cost(assignment)
            open_facilities = set(assignment)

            sorted_facilities = sorted(open_facilities, key=lambda f: -opening_costs[f])

            for fac_to_close in sorted_facilities:
                temp_assignment = assignment[:]
                reassigned = False

                for j in range(n_clients):
                    if temp_assignment[j] == fac_to_close:
                        best_fac = min(
                            (f for f in range(n_facilities) if f != fac_to_close),
                            key=lambda f: assign_costs[f][j],
                        )
                        temp_assignment[j] = best_fac
                        reassigned = True

                if reassigned:
                    new_cost = calc_cost(temp_assignment)
                    if new_cost < current_cost:
                        assignment = temp_assignment
                        current_cost = new_cost
                        improved = True
                        break

        final_cost = calc_cost(assignment)
        if final_cost < best_cost:
            best_cost = final_cost
            best_assignment = assignment

        time_closing += time.time() - phase3_start

    # Print timing summary for first instance (for profiling)
    total_time = time.time() - start_total
    if n_clients > 0:
        print(f"[TIMING] opening={time_opening:.2f}s search={time_search:.2f}s closing={time_closing:.2f}s total={total_time:.2f}s")

    return best_assignment if best_assignment else [0] * n_clients


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
    return _solve_single(opening_costs, assign_costs)
