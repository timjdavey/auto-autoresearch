"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: Smart WalkSAT + 1-opt + 2-opt local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time


def count_unsatisfied(assignment, clauses):
    """Count the number of unsatisfied clauses."""
    count = 0
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            val = assignment[var_idx]
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break
        if not satisfied:
            count += 1
    return count


def get_unsatisfied_clauses(assignment, clauses):
    """Get list of unsatisfied clause indices."""
    unsat = []
    for i, clause in enumerate(clauses):
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            val = assignment[var_idx]
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break
        if not satisfied:
            unsat.append(i)
    return unsat


def evaluate_flip(assignment, clauses, var_idx):
    """Evaluate impact of flipping a variable."""
    original = assignment[var_idx]
    assignment[var_idx] = not assignment[var_idx]
    impact = count_unsatisfied(assignment, clauses)
    assignment[var_idx] = original
    return impact


def solve(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """
    Solve MAX-SAT using Smart WalkSAT + 1-opt + 2-opt local search.
    """
    if n_vars == 0:
        return []

    start_time = time.time()
    time_limit = 55.0  # 55s budget

    best_assignment = None
    best_unsat = float('inf')

    # Multi-start: try multiple random initializations
    for restart in range(25):
        if time.time() - start_time > time_limit:
            break

        # Initialize: random assignment
        assignment = [random.choice([True, False]) for _ in range(n_vars)]
        current_unsat = count_unsatisfied(assignment, clauses)

        # Smart WalkSAT: evaluate flip impact before deciding
        # Balanced decay: later restarts get meaningful search depth
        max_flips = int(22000 / (1 + 0.8 * (restart / 25)))
        random_walk_prob = 0.2 + 0.1 * (restart % 3)  # Vary from 0.2 to 0.4

        for iteration in range(max_flips):
            if time.time() - start_time > time_limit:
                break

            unsat_clauses = get_unsatisfied_clauses(assignment, clauses)
            if not unsat_clauses:
                return assignment

            # Pick random unsatisfied clause
            clause_idx = random.choice(unsat_clauses)
            clause = clauses[clause_idx]

            # Smart flip: evaluate all variables in clause, pick best
            best_flip_var = None
            best_flip_impact = current_unsat

            for lit in clause:
                var_idx = abs(lit) - 1
                impact = evaluate_flip(assignment, clauses, var_idx)
                if impact < best_flip_impact:
                    best_flip_var = var_idx
                    best_flip_impact = impact

            if best_flip_var is not None:
                # Flip the best variable
                assignment[best_flip_var] = not assignment[best_flip_var]
                current_unsat = best_flip_impact
            else:
                # No improving flip, do random walk
                if random.random() < random_walk_prob:
                    var_idx = random.choice([abs(lit) - 1 for lit in clause])
                    assignment[var_idx] = not assignment[var_idx]
                    current_unsat = count_unsatisfied(assignment, clauses)

            if current_unsat < best_unsat:
                best_unsat = current_unsat
                best_assignment = assignment[:]

        # Quick 1-opt + 2-opt refinement
        assignment = best_assignment[:] if best_assignment else assignment

        # First-improvement 1-opt
        improved = True
        passes = 0
        while improved and time.time() - start_time < time_limit and passes < 3:
            improved = False
            passes += 1
            for var_idx in range(n_vars):
                assignment[var_idx] = not assignment[var_idx]
                unsat_count = count_unsatisfied(assignment, clauses)
                if unsat_count < best_unsat:
                    best_unsat = unsat_count
                    best_assignment = assignment[:]
                    improved = True
                    break
                else:
                    assignment[var_idx] = not assignment[var_idx]

        # Simple 2-opt: 100 random pair flips
        for _ in range(100):
            if time.time() - start_time > time_limit:
                break
            var1 = random.randint(0, n_vars - 1)
            var2 = random.randint(0, n_vars - 1)
            if var1 == var2:
                continue

            assignment[var1] = not assignment[var1]
            assignment[var2] = not assignment[var2]
            unsat_count = count_unsatisfied(assignment, clauses)
            if unsat_count < best_unsat:
                best_unsat = unsat_count
                best_assignment = assignment[:]
            else:
                assignment[var1] = not assignment[var1]
                assignment[var2] = not assignment[var2]

        # Selective 3-opt for small instances with few unsat clauses
        if n_vars <= 270 and best_unsat <= 6 and time.time() - start_time < time_limit - 2:
            for _ in range(min(50, 150 - best_unsat * 15)):
                if time.time() - start_time > time_limit:
                    break
                var1, var2, var3 = random.sample(range(n_vars), 3)
                assignment[var1] = not assignment[var1]
                assignment[var2] = not assignment[var2]
                assignment[var3] = not assignment[var3]
                unsat_count = count_unsatisfied(assignment, clauses)
                if unsat_count < best_unsat:
                    best_unsat = unsat_count
                    best_assignment = assignment[:]
                else:
                    assignment[var1] = not assignment[var1]
                    assignment[var2] = not assignment[var2]
                    assignment[var3] = not assignment[var3]

    return best_assignment if best_assignment is not None else assignment
