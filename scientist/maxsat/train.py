"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: GSAT with random restarts.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


def count_unsatisfied(assignment: list[bool], clauses: list[list[int]]) -> int:
    """Count the number of unsatisfied clauses."""
    unsatisfied = 0
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            if var_idx < len(assignment):
                if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                    satisfied = True
                    break
        if not satisfied:
            unsatisfied += 1
    return unsatisfied


def walksat(n_vars: int, clauses: list[list[int]], max_flips: int = 50, noise: float = 0.15) -> list[bool]:
    """WalkSAT: local search with noise to escape local optima."""
    assignment = [random.choice([True, False]) for _ in range(n_vars)]
    best_assignment = assignment[:]
    best_unsatisfied = count_unsatisfied(assignment, clauses)

    for _ in range(max_flips):
        current_unsatisfied = count_unsatisfied(assignment, clauses)

        if current_unsatisfied == 0:
            return assignment

        if current_unsatisfied < best_unsatisfied:
            best_unsatisfied = current_unsatisfied
            best_assignment = assignment[:]

        # With probability noise, pick an unsatisfied clause and flip a variable in it
        if random.random() < noise and current_unsatisfied > 0:
            # Find unsatisfied clauses
            unsatisfied_clauses = []
            for clause in clauses:
                satisfied = False
                for lit in clause:
                    var_idx = abs(lit) - 1
                    if var_idx < len(assignment):
                        if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                            satisfied = True
                            break
                if not satisfied:
                    unsatisfied_clauses.append(clause)

            if unsatisfied_clauses:
                # Pick random unsatisfied clause and flip a random variable in it
                clause = random.choice(unsatisfied_clauses)
                var_to_flip = abs(random.choice(clause)) - 1
                assignment[var_to_flip] = not assignment[var_to_flip]
        else:
            # GSAT: only evaluate variables in unsatisfied clauses for speed
            unsatisfied_clauses = []
            candidate_vars = set()
            for clause in clauses:
                satisfied = False
                for lit in clause:
                    var_idx = abs(lit) - 1
                    if var_idx < len(assignment):
                        if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                            satisfied = True
                            break
                if not satisfied:
                    unsatisfied_clauses.append(clause)
                    for lit in clause:
                        candidate_vars.add(abs(lit) - 1)

            if not candidate_vars:
                break

            best_flip = -1
            best_reduction = -1
            for var_idx in candidate_vars:
                assignment[var_idx] = not assignment[var_idx]
                new_unsatisfied = count_unsatisfied(assignment, clauses)
                reduction = current_unsatisfied - new_unsatisfied
                if reduction > best_reduction:
                    best_reduction = reduction
                    best_flip = var_idx
                assignment[var_idx] = not assignment[var_idx]

            if best_flip == -1:
                break
            assignment[best_flip] = not assignment[best_flip]

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

    best_assignment = None
    best_unsatisfied = float('inf')

    # WalkSAT with multiple restarts
    num_restarts = min(5, max(2, 100 // (n_vars + 1)))
    for _ in range(num_restarts):
        assignment = walksat(n_vars, clauses, max_flips=50, noise=0.15)
        unsatisfied = count_unsatisfied(assignment, clauses)
        if unsatisfied < best_unsatisfied:
            best_unsatisfied = unsatisfied
            best_assignment = assignment

    return best_assignment
