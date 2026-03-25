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
    time_limit = 55.0  # Leave 5s buffer

    def is_clause_sat(clause, assignment):
        """Check if a single clause is satisfied."""
        for lit in clause:
            var_idx = abs(lit) - 1
            if (lit > 0 and assignment[var_idx]) or (lit < 0 and not assignment[var_idx]):
                return True
        return False

    def count_unsat(assignment):
        """Count unsatisfied clauses."""
        count = 0
        for clause in clauses:
            if not is_clause_sat(clause, assignment):
                count += 1
        return count

    def get_unsat_clauses(assignment):
        """Get indices of unsatisfied clauses."""
        unsat = []
        for i, clause in enumerate(clauses):
            if not is_clause_sat(clause, assignment):
                unsat.append(i)
        return unsat

    # Better initialization: start with greedy assignment
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

    best_assignment = assignment[:]
    best_unsat = count_unsat(assignment)

    # Multi-start WalkSAT with smart move selection
    num_restarts = 3
    remaining_time = time_limit - (time.time() - start_time)
    per_restart_time = remaining_time / num_restarts

    for restart in range(num_restarts):
        restart_start = time.time()

        # Reinitialize from greedy or random for diversity
        if restart == 0:
            # Keep the greedy initialization from above
            pass
        else:
            # Random restart for exploration
            assignment = [random.random() < 0.5 for _ in range(n_vars)]

        current_unsat = count_unsat(assignment)
        local_best = current_unsat
        local_best_assignment = assignment[:]

        # WalkSAT loop for this restart
        iterations = 0
        max_iterations = 100000

        while iterations < max_iterations:
            if time.time() - start_time > time_limit - 1:
                break

            unsat_clauses = get_unsat_clauses(assignment)
            if not unsat_clauses:
                best_unsat = 0
                best_assignment = assignment[:]
                return best_assignment

            # Pick random unsatisfied clause
            clause_idx = random.choice(unsat_clauses)
            clause = clauses[clause_idx]

            # Evaluate impact of flipping each variable in the clause
            var_impacts = []
            for lit in clause:
                var_idx = abs(lit) - 1
                # Flip the variable
                assignment[var_idx] = not assignment[var_idx]
                impact = count_unsat(assignment)
                var_impacts.append((impact, var_idx))
                # Flip back
                assignment[var_idx] = not assignment[var_idx]

            # Sort by impact (fewer unsatisfied is better)
            var_impacts.sort(key=lambda x: x[0])

            # With 90% probability: pick best move. With 10%: pick random.
            if random.random() < 0.9:
                best_impact, best_var = var_impacts[0]
                assignment[best_var] = not assignment[best_var]
            else:
                _, random_var = random.choice(var_impacts)
                assignment[random_var] = not assignment[random_var]

            # Track best solution
            current_unsat = count_unsat(assignment)
            if current_unsat < local_best:
                local_best = current_unsat
                local_best_assignment = assignment[:]

            iterations += 1

        # Update global best if this restart found something better
        if local_best < best_unsat:
            best_unsat = local_best
            best_assignment = local_best_assignment[:]

    return best_assignment
