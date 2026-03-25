"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: Smart WalkSAT with greedy initialization.
"""

import random
import time


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

    # --- Greedy initialization ---
    assignment = [False] * n_vars
    for var_idx in range(n_vars):
        var = var_idx + 1
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

    # --- Smart WalkSAT local search ---
    start_time = time.time()
    max_iterations = 5000
    time_limit = 55  # Leave 5s margin for other operations

    # Track best solution found
    best_solution = assignment[:]
    best_unsat_count = sum(
        1 for c in clauses
        if not any(
            (l > 0 and assignment[abs(l) - 1])
            or (l < 0 and not assignment[abs(l) - 1])
            for l in c
        )
    )

    for iteration in range(max_iterations):
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            break
        # Find unsatisfied clauses
        unsatisfied = []
        for clause in clauses:
            satisfied = False
            for lit in clause:
                var_idx = abs(lit) - 1
                if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                    satisfied = True
                    break
            if not satisfied:
                unsatisfied.append(clause)

        if not unsatisfied:
            break

        # Pick a random unsatisfied clause
        clause = random.choice(unsatisfied)

        # Evaluate impact of flipping each variable in the clause
        best_var = None
        best_move_unsat = len(unsatisfied)

        for lit in clause:
            var_idx = abs(lit) - 1
            # Test flip
            assignment[var_idx] = not assignment[var_idx]
            unsat_count = sum(
                1 for c in clauses
                if not any(
                    (l > 0 and assignment[abs(l) - 1])
                    or (l < 0 and not assignment[abs(l) - 1])
                    for l in c
                )
            )
            assignment[var_idx] = not assignment[var_idx]  # Flip back

            if unsat_count < best_move_unsat:
                best_move_unsat = unsat_count
                best_var = var_idx

        # With 90% probability, flip the best variable; 10% random
        if best_var is not None and random.random() < 0.9:
            assignment[best_var] = not assignment[best_var]
        else:
            lit = random.choice(clause)
            var_idx = abs(lit) - 1
            assignment[var_idx] = not assignment[var_idx]

        # Track best solution found
        current_unsat = sum(
            1 for c in clauses
            if not any(
                (l > 0 and assignment[abs(l) - 1])
                or (l < 0 and not assignment[abs(l) - 1])
                for l in c
            )
        )
        if current_unsat < best_unsat_count:
            best_unsat_count = current_unsat
            best_solution = assignment[:]

    return best_solution
