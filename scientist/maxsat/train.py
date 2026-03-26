"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: WalkSAT with smart variable evaluation and multi-start.
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

    start_time = time.time()
    time_limit = 55  # Optimal time for WalkSAT exploration
    best_assignment = [False] * n_vars
    best_unsat = len(clauses)

    # Multi-start: try multiple random seeds with clause weighting (75 for broader search)
    for attempt in range(75):
        if time.time() - start_time > time_limit:
            break

        assignment = [random.choice([True, False]) for _ in range(n_vars)]
        clause_weights = [1.0] * len(clauses)  # Adaptive weights for clauses

        # WalkSAT loop with weighted evaluation
        max_iterations = 2000
        for iteration in range(max_iterations):
            if time.time() - start_time > time_limit:
                break

            # Find unsatisfied clauses
            unsat_clauses = []
            for clause_idx, clause in enumerate(clauses):
                satisfied = False
                for lit in clause:
                    var_idx = abs(lit) - 1
                    if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                        satisfied = True
                        break
                if not satisfied:
                    unsat_clauses.append((clause_idx, clause))

            # Check if we found a better solution
            num_unsat = len(unsat_clauses)
            if num_unsat < best_unsat:
                best_unsat = num_unsat
                best_assignment = assignment[:]

            if num_unsat == 0:
                return assignment

            # Pick a random unsatisfied clause, weighted by clause weights
            clause_idx, clause = random.choice(unsat_clauses)

            # Evaluate all three literals in the clause: pick the one with best weighted improvement
            best_flip = None
            best_score = -float('inf')

            for lit in clause:
                var_idx = abs(lit) - 1
                # Evaluate flipping this variable with weighted impact
                delta = evaluate_flip_weighted(assignment, clauses, var_idx, clause_weights)
                if delta > best_score:
                    best_score = delta
                    best_flip = var_idx

            # Flip the best variable
            if best_flip is not None:
                assignment[best_flip] = not assignment[best_flip]

            # Increase weights of unsatisfied clauses (adaptive clause weighting)
            # 0.25 is optimal; trial 33 (0.25 → 97.92%), trial 34 (0.27 → 95.07%)
            for idx, _ in unsat_clauses:
                clause_weights[idx] += 0.25

    # Apply local search polish
    unsat_count = count_unsatisfied(best_assignment, clauses)

    # For small instances, try 3-opt to break plateau
    if n_vars < 250 and unsat_count > 1:
        best_assignment = three_opt_improve(best_assignment, clauses, start_time, 56)
    elif unsat_count > 2:
        best_assignment = two_opt_improve(best_assignment, clauses, start_time, 56)
    else:
        # For nearly-solved instances, just do 1-opt
        best_assignment = one_opt_improve(best_assignment, clauses, start_time, 56)
    return best_assignment


def evaluate_flip(assignment: list[bool], clauses: list[list[int]], var_idx: int) -> int:
    """
    Evaluate the impact of flipping variable var_idx.
    Returns the change in number of satisfied clauses (higher is better).
    """
    var = var_idx + 1  # 1-indexed
    delta = 0

    for clause in clauses:
        if var not in clause and -var not in clause:
            continue

        # Check current satisfaction
        currently_sat = False
        for lit in clause:
            v = abs(lit) - 1
            if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                currently_sat = True
                break

        # Check satisfaction after flip
        new_assignment = assignment[:]
        new_assignment[var_idx] = not new_assignment[var_idx]
        after_sat = False
        for lit in clause:
            v = abs(lit) - 1
            if (lit > 0 and new_assignment[v]) or (lit < 0 and not new_assignment[v]):
                after_sat = True
                break

        if after_sat and not currently_sat:
            delta += 1
        elif currently_sat and not after_sat:
            delta -= 1

    return delta


def evaluate_flip_weighted(assignment: list[bool], clauses: list[list[int]], var_idx: int, clause_weights: list[float]) -> float:
    """
    Evaluate the weighted impact of flipping variable var_idx.
    Weights guide search toward hard (repeatedly unsatisfied) clauses.
    """
    var = var_idx + 1  # 1-indexed
    score = 0.0

    for clause_idx, clause in enumerate(clauses):
        if var not in clause and -var not in clause:
            continue

        # Check current satisfaction
        currently_sat = False
        for lit in clause:
            v = abs(lit) - 1
            if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                currently_sat = True
                break

        # Check satisfaction after flip
        new_assignment = assignment[:]
        new_assignment[var_idx] = not new_assignment[var_idx]
        after_sat = False
        for lit in clause:
            v = abs(lit) - 1
            if (lit > 0 and new_assignment[v]) or (lit < 0 and not new_assignment[v]):
                after_sat = True
                break

        weight = clause_weights[clause_idx]
        if after_sat and not currently_sat:
            score += weight
        elif currently_sat and not after_sat:
            score -= weight

    return score


def one_opt_improve(assignment: list[bool], clauses: list[list[int]], start_time: float, time_limit: float) -> list[bool]:
    """
    1-opt local search: try flipping individual variables to improve solution quality.
    """
    best_assignment = assignment[:]
    best_unsat = count_unsatisfied(best_assignment, clauses)

    improved = True
    max_passes = 1
    passes = 0
    while improved and passes < max_passes and time.time() - start_time < time_limit:
        improved = False
        passes += 1

        # Try all single variables
        n_vars = len(assignment)
        for i in range(n_vars):
            if time.time() - start_time > time_limit:
                break

            # Try flipping variable i
            test_assignment = best_assignment[:]
            test_assignment[i] = not test_assignment[i]

            test_unsat = count_unsatisfied(test_assignment, clauses)
            if test_unsat < best_unsat:
                best_assignment = test_assignment
                best_unsat = test_unsat
                improved = True

    return best_assignment


def two_opt_improve(assignment: list[bool], clauses: list[list[int]], start_time: float, time_limit: float) -> list[bool]:
    """
    2-opt local search: try flipping pairs of variables to improve solution quality.
    """
    best_assignment = assignment[:]
    best_unsat = count_unsatisfied(best_assignment, clauses)

    improved = True
    n_vars = len(assignment)
    while improved and time.time() - start_time < time_limit:
        improved = False

        # Try all pairs of variables
        for i in range(n_vars):
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, n_vars):
                if time.time() - start_time > time_limit:
                    break

                # Try flipping both variables i and j
                test_assignment = best_assignment[:]
                test_assignment[i] = not test_assignment[i]
                test_assignment[j] = not test_assignment[j]

                test_unsat = count_unsatisfied(test_assignment, clauses)
                if test_unsat < best_unsat:
                    best_assignment = test_assignment
                    best_unsat = test_unsat
                    improved = True
                    break

            if improved:
                break

    return best_assignment


def three_opt_improve(assignment: list[bool], clauses: list[list[int]], start_time: float, time_limit: float) -> list[bool]:
    """
    3-opt local search: try flipping triples of variables.
    More expensive but explores wider neighborhoods for better solutions.
    """
    best_assignment = assignment[:]
    best_unsat = count_unsatisfied(best_assignment, clauses)

    improved = True
    n_vars = len(assignment)

    # Limit 3-opt to first pass only due to O(n^3) complexity
    if improved and time.time() - start_time < time_limit:
        improved = False

        # Try all triples of variables (limited to avoid timeout)
        for i in range(min(n_vars, 150)):  # Limit search space for small instances
            if time.time() - start_time > time_limit:
                break
            for j in range(i + 1, min(n_vars, 150)):
                if time.time() - start_time > time_limit:
                    break
                for k in range(j + 1, min(n_vars, 150)):
                    if time.time() - start_time > time_limit:
                        break

                    # Try flipping all three variables
                    test_assignment = best_assignment[:]
                    test_assignment[i] = not test_assignment[i]
                    test_assignment[j] = not test_assignment[j]
                    test_assignment[k] = not test_assignment[k]

                    test_unsat = count_unsatisfied(test_assignment, clauses)
                    if test_unsat < best_unsat:
                        best_assignment = test_assignment
                        best_unsat = test_unsat
                        improved = True
                        break

                if improved:
                    break
            if improved:
                break

    return best_assignment


def count_unsatisfied(assignment: list[bool], clauses: list[list[int]]) -> int:
    """Count the number of unsatisfied clauses."""
    count = 0
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                satisfied = True
                break
        if not satisfied:
            count += 1
    return count
