"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: WalkSAT algorithm.
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
            if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                satisfied = True
                break
        if not satisfied:
            unsat += 1
    return unsat


def count_breaks(var_idx: int, assignment: list[bool], clauses: list[list[int]]) -> int:
    """Count how many currently satisfied clauses would become unsatisfied if we flip var_idx."""
    breaks = 0
    for clause in clauses:
        # Check if clause is currently satisfied
        satisfied = False
        for lit in clause:
            v = abs(lit) - 1
            if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                satisfied = True
                break

        if not satisfied:
            continue

        # Check if flipping var_idx would break this clause
        var_in_clause = False
        for lit in clause:
            if abs(lit) - 1 == var_idx:
                var_in_clause = True
                # After flip, the literal becomes false
                if (lit > 0 and not assignment[var_idx]) or (lit < 0 and assignment[var_idx]):
                    # This literal is the only one satisfying the clause
                    break

        if var_in_clause:
            # Check if any other literal still satisfies
            still_satisfied = False
            for lit in clause:
                v = abs(lit) - 1
                if v == var_idx:
                    continue
                if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                    still_satisfied = True
                    break
            if not still_satisfied:
                breaks += 1

    return breaks


def solve(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """
    Solve the Maximum Satisfiability Problem (MAX-SAT) using WalkSAT.

    Args:
        n_vars: number of Boolean variables (variables are 1-indexed in clauses).
        clauses: list of clauses. Each clause is a list of 3 integers.

    Returns:
        assignment: list of length n_vars where assignment[i] is the truth
                    value for variable (i+1). Must be a list of bools.
    """
    if n_vars == 0:
        return []

    start_time = time.time()
    time_limit = 59.0
    walk_prob = 0.51  # Probability of random walk step

    best_assignment = None
    best_unsat = float('inf')

    # WalkSAT with random restarts
    for restart_iter in range(30):
        if time.time() - start_time > time_limit:
            break

        # Initial assignment: greedy on first restart, random on others
        if restart_iter == 0:
            # Greedy initialization: pick value that satisfies more unsatisfied clauses
            assignment = [False] * n_vars
            for var_idx in range(n_vars):
                var = var_idx + 1
                count_true = 0
                count_false = 0
                for clause in clauses:
                    # Check if clause is already satisfied by earlier variables
                    already_sat = False
                    for lit in clause:
                        v = abs(lit) - 1
                        if v < var_idx:
                            if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                                already_sat = True
                                break
                    if already_sat:
                        continue
                    # Count what setting this variable would do
                    if var in clause:
                        count_true += 1
                    if -var in clause:
                        count_false += 1
                assignment[var_idx] = count_true >= count_false
        else:
            # Random initial assignment for diversification
            assignment = [random.choice([True, False]) for _ in range(n_vars)]

        current_unsat = count_unsat(assignment, clauses)

        if current_unsat < best_unsat:
            best_unsat = current_unsat
            best_assignment = assignment[:]

        if current_unsat == 0:
            return assignment

        # Local search: WalkSAT
        no_improve_steps = 0
        max_no_improve = 400

        while no_improve_steps < max_no_improve and time.time() - start_time < time_limit:
            # Find an unsatisfied clause
            unsat_clause = None
            for clause in clauses:
                satisfied = False
                for lit in clause:
                    var_idx = abs(lit) - 1
                    if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                        satisfied = True
                        break
                if not satisfied:
                    unsat_clause = clause
                    break

            if unsat_clause is None:
                # All clauses satisfied
                if current_unsat < best_unsat:
                    best_unsat = 0
                    best_assignment = assignment[:]
                return assignment

            # Pick a variable from the unsatisfied clause
            if random.random() < walk_prob:
                # Random walk: flip a random variable from the clause
                var_idx = abs(random.choice(unsat_clause)) - 1
            else:
                # Greedy: flip the variable that breaks fewest clauses
                candidates = [abs(lit) - 1 for lit in unsat_clause]
                breaks_list = [(var, count_breaks(var, assignment, clauses)) for var in candidates]
                var_idx = min(breaks_list, key=lambda x: x[1])[0]

            assignment[var_idx] = not assignment[var_idx]
            new_unsat = count_unsat(assignment, clauses)

            if new_unsat < current_unsat:
                # Accept improvement
                current_unsat = new_unsat
                no_improve_steps = 0

                if current_unsat < best_unsat:
                    best_unsat = current_unsat
                    best_assignment = assignment[:]

                if current_unsat == 0:
                    return assignment
            else:
                no_improve_steps += 1

    return best_assignment if best_assignment is not None else [False] * n_vars
