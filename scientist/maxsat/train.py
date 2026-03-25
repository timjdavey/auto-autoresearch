"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: greedy sequential assignment (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


import random
import time


def solve(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """
    Solve the Maximum Satisfiability Problem (MAX-SAT).

    Smart WalkSAT with 1-opt local search.
    """
    if n_vars == 0:
        return []

    time_limit = 55  # Leave 5s margin
    start_time = time.time()

    def count_unsat(assignment):
        """Count unsatisfied clauses."""
        count = 0
        for clause in clauses:
            sat = False
            for lit in clause:
                var_idx = abs(lit) - 1
                if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                    sat = True
                    break
            if not sat:
                count += 1
        return count

    def get_unsat_clauses(assignment):
        """Get list of unsatisfied clause indices."""
        unsat = []
        for i, clause in enumerate(clauses):
            sat = False
            for lit in clause:
                var_idx = abs(lit) - 1
                if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                    sat = True
                    break
            if not sat:
                unsat.append(i)
        return unsat

    # Multi-start: try different random initializations
    best_assignment = None
    best_unsat = float('inf')

    for attempt in range(80):
        assignment = [random.random() < 0.5 for _ in range(n_vars)]
        current_unsat = count_unsat(assignment)

        # Smart WalkSAT with simulated annealing
        temperature = 10.0
        cooling_rate = 0.9995
        min_temperature = 0.01

        for iteration in range(1500):
            if time.time() - start_time > time_limit:
                break

            unsat = get_unsat_clauses(assignment)
            if not unsat:
                current_unsat = 0
                break

            # Pick random unsatisfied clause
            clause_idx = random.choice(unsat)
            clause = clauses[clause_idx]

            # Evaluate impact of flipping each variable in the clause
            flip_options = []

            for lit in clause:
                var_idx = abs(lit) - 1
                assignment[var_idx] = not assignment[var_idx]
                new_unsat = count_unsat(assignment)
                improvement = current_unsat - new_unsat
                flip_options.append((var_idx, improvement, new_unsat))
                assignment[var_idx] = not assignment[var_idx]

            # Choose with simulated annealing
            best_flip_var, best_improvement, best_unsat_after = max(flip_options, key=lambda x: x[1])

            # Accept non-best moves with probability based on temperature
            if best_improvement < 0 and temperature > min_temperature:
                if random.random() < (1.0 / (1.0 + abs(best_improvement) / max(temperature, 0.01))):
                    # Accept worse move with some probability
                    pass
                else:
                    # Reject and just pick best
                    best_flip_var, best_improvement, best_unsat_after = flip_options[0]

            # Apply flip
            assignment[best_flip_var] = not assignment[best_flip_var]
            current_unsat = best_unsat_after

            # Cool down temperature
            temperature *= cooling_rate

        # 1-opt local search (best improvement)
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            best_var = -1
            best_new_unsat = current_unsat

            for var_idx in range(n_vars):
                assignment[var_idx] = not assignment[var_idx]
                new_unsat = count_unsat(assignment)
                if new_unsat < best_new_unsat:
                    best_new_unsat = new_unsat
                    best_var = var_idx
                assignment[var_idx] = not assignment[var_idx]

            if best_var >= 0:
                assignment[best_var] = not assignment[best_var]
                current_unsat = best_new_unsat
                improved = True

        # 2-opt local search (flip pairs of variables from unsatisfied clauses)
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            best_i = -1
            best_j = -1
            best_new_unsat = current_unsat

            # Only consider variables in unsatisfied clauses
            unsat = get_unsat_clauses(assignment)
            if not unsat:
                break

            candidate_vars = set()
            for clause_idx in unsat:
                for lit in clauses[clause_idx]:
                    candidate_vars.add(abs(lit) - 1)

            candidate_vars = list(candidate_vars)

            # Try all pairs of candidate variables
            for i_idx in range(len(candidate_vars)):
                if time.time() - start_time > time_limit:
                    break
                i = candidate_vars[i_idx]
                for j_idx in range(i_idx + 1, len(candidate_vars)):
                    j = candidate_vars[j_idx]
                    assignment[i] = not assignment[i]
                    assignment[j] = not assignment[j]
                    new_unsat = count_unsat(assignment)
                    if new_unsat < best_new_unsat:
                        best_new_unsat = new_unsat
                        best_i = i
                        best_j = j
                    assignment[i] = not assignment[i]
                    assignment[j] = not assignment[j]

            if best_i >= 0:
                assignment[best_i] = not assignment[best_i]
                assignment[best_j] = not assignment[best_j]
                current_unsat = best_new_unsat
                improved = True

        if current_unsat < best_unsat:
            best_unsat = current_unsat
            best_assignment = assignment[:]

        if time.time() - start_time > time_limit:
            break

    return best_assignment if best_assignment else [False] * n_vars
