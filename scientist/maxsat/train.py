"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: GSAT with greedy initialization + random restarts.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time


def count_unsat(assignment: list[bool], clauses: list[list[int]]) -> int:
    """Count the number of unsatisfied clauses."""
    unsat = 0
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            var_val = assignment[var_idx]
            if (lit > 0 and var_val) or (lit < 0 and not var_val):
                satisfied = True
                break
        if not satisfied:
            unsat += 1
    return unsat


def greedy_init(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """Initialize using greedy assignment with randomized variable order."""
    assignment = [False] * n_vars
    var_order = list(range(n_vars))
    random.shuffle(var_order)

    for var_idx in var_order:
        var = var_idx + 1  # 1-indexed

        count_true = 0
        count_false = 0
        for clause in clauses:
            if var not in clause and -var not in clause:
                continue
            already_sat = False
            for lit in clause:
                v = abs(lit) - 1
                if v < var_idx:
                    if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                        already_sat = True
                        break
            if already_sat:
                continue
            if var in clause:
                count_true += 1
            if -var in clause:
                count_false += 1

        assignment[var_idx] = count_true >= count_false

    return assignment


def gsat_local_search(assignment: list[bool], clauses: list[list[int]], time_limit: float) -> list[bool]:
    """Run GSAT-style local search: first-improvement with variable shuffling."""
    best_assignment = assignment.copy()
    best_unsat = count_unsat(best_assignment, clauses)
    current_assignment = assignment.copy()
    current_unsat = best_unsat

    start_time = time.time()
    stuck_count = 0
    n_vars = len(current_assignment)

    while time.time() - start_time < time_limit:
        # First-improvement: accept the first flip that improves unsat
        # Use shuffled variable order to help escape local optima
        found_improvement = False
        var_indices = list(range(n_vars))
        random.shuffle(var_indices)

        for var_idx in var_indices:
            # Try flipping this variable
            current_assignment[var_idx] = not current_assignment[var_idx]
            new_unsat = count_unsat(current_assignment, clauses)

            if new_unsat < current_unsat:
                # Accept the flip
                current_unsat = new_unsat
                found_improvement = True

                if current_unsat < best_unsat:
                    best_unsat = current_unsat
                    best_assignment = current_assignment.copy()
                    stuck_count = 0
                else:
                    stuck_count += 1
                break
            else:
                # Flip back if no improvement
                current_assignment[var_idx] = not current_assignment[var_idx]

        if not found_improvement:
            stuck_count += 1

        # Early exit if stuck (higher threshold allows more exploration)
        if stuck_count > 20:
            break

    return best_assignment


def solve(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """
    Solve the Maximum Satisfiability Problem (MAX-SAT).

    Find a truth assignment that satisfies as many clauses as possible in
    a CNF formula (3-SAT: each clause has exactly 3 literals).

    Args:
        n_vars: number of Boolean variables (variables are 1-indexed in clauses).
        clauses: list of clauses. Each clause is a list of 3 integers.
                 Positive integer k means variable k is True.
                 Negative integer -k means variable k is False.

    Returns:
        assignment: list of length n_vars where assignment[i] is the truth
                    value for variable (i+1). Must be a list of bools.
    """
    if n_vars == 0:
        return []

    start_time = time.time()
    time_limit = 59.0  # Leave margin for safety

    best_solution = None
    best_unsat = float('inf')

    # Try greedy initialization + local search
    greedy_init_assignment = greedy_init(n_vars, clauses)
    improved = gsat_local_search(greedy_init_assignment, clauses, 5.0)
    unsat_count = count_unsat(improved, clauses)
    if unsat_count < best_unsat:
        best_unsat = unsat_count
        best_solution = improved

    # Try random restarts
    num_restarts = max(1, min(8, int((time_limit - (time.time() - start_time) - 1.0) / 3.0)))
    time_per_restart = (time_limit - (time.time() - start_time) - 1.0) / max(1, num_restarts)

    for _ in range(num_restarts):
        if time.time() - start_time >= time_limit - 1.0:
            break

        # Random initialization
        random_assignment = [random.choice([True, False]) for _ in range(n_vars)]
        improved = gsat_local_search(random_assignment, clauses, time_per_restart)
        unsat_count = count_unsat(improved, clauses)

        if unsat_count < best_unsat:
            best_unsat = unsat_count
            best_solution = improved

    return best_solution if best_solution is not None else greedy_init_assignment
