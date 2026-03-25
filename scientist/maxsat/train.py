"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: greedy initialization + WalkSAT local search.
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

    # Precompute which clauses contain each variable
    var_to_clauses = [[] for _ in range(n_vars)]
    for clause_idx, clause in enumerate(clauses):
        for lit in clause:
            var_idx = abs(lit) - 1
            var_to_clauses[var_idx].append(clause_idx)

    def count_unsat(assign):
        unsat = 0
        for clause in clauses:
            sat = any((lit > 0 and assign[abs(lit) - 1]) or (lit < 0 and not assign[abs(lit) - 1]) for lit in clause)
            if not sat:
                unsat += 1
        return unsat

    def get_unsat_clauses(assign):
        unsat = []
        for i, clause in enumerate(clauses):
            sat = any((lit > 0 and assign[abs(lit) - 1]) or (lit < 0 and not assign[abs(lit) - 1]) for lit in clause)
            if not sat:
                unsat.append(i)
        return unsat

    def eval_flip_cost(assign, var_idx):
        """Efficiently calculate change in unsat clauses if we flip var_idx."""
        cost = 0
        for clause_idx in var_to_clauses[var_idx]:
            clause = clauses[clause_idx]
            sat_before = any((lit > 0 and assign[abs(lit) - 1]) or (lit < 0 and not assign[abs(lit) - 1]) for lit in clause)
            # After flip
            assign[var_idx] = not assign[var_idx]
            sat_after = any((lit > 0 and assign[abs(lit) - 1]) or (lit < 0 and not assign[abs(lit) - 1]) for lit in clause)
            assign[var_idx] = not assign[var_idx]

            if sat_before and not sat_after:
                cost += 1
            elif not sat_before and sat_after:
                cost -= 1
        return cost

    # --- Greedy sequential initialization ---
    best_assignment = [False] * n_vars
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
                    if (lit > 0 and best_assignment[v]) or (lit < 0 and not best_assignment[v]):
                        already_sat = True
                        break
            if already_sat:
                continue
            if var in clause:
                count_true += 1
            if -var in clause:
                count_false += 1
        best_assignment[var_idx] = count_true >= count_false

    best_unsat = count_unsat(best_assignment)
    start_time = time.time()
    time_limit = 55.0  # Leave 5s buffer for safety

    # --- WalkSAT local search with restarts ---
    for restart in range(12):
        if time.time() - start_time > time_limit:
            break

        # Try WalkSAT iterations
        assignment = best_assignment[:]
        for iteration in range(35000):
            if time.time() - start_time > time_limit:
                break

            unsat_indices = get_unsat_clauses(assignment)
            if not unsat_indices:
                best_assignment = assignment[:]
                best_unsat = 0
                break

            # Pick random unsatisfied clause
            clause_idx = random.choice(unsat_indices)
            clause = clauses[clause_idx]

            # Evaluate cost of flipping each variable in the clause using deltas
            current_unsat = len(unsat_indices)
            costs = []
            for lit in clause:
                var_idx = abs(lit) - 1
                delta = eval_flip_cost(assignment, var_idx)
                costs.append(current_unsat + delta)

            # Choose variable: prefer flips that improve, else pick cheapest
            min_cost = min(costs)

            if min_cost < current_unsat:
                # Greedy: pick best variable
                best_idx = costs.index(min_cost)
            else:
                # Pick randomly with bias toward cheaper flips
                weights = [max(1.0, current_unsat - cost + 1) for cost in costs]
                best_idx = random.choices(range(len(weights)), weights=weights, k=1)[0]

            var_idx = abs(clause[best_idx]) - 1
            assignment[var_idx] = not assignment[var_idx]

            # Update best if improved
            new_unsat = count_unsat(assignment)
            if new_unsat < best_unsat:
                best_assignment = assignment[:]
                best_unsat = new_unsat

        # Smart restart: perturb best solution (keeps good assignments, flips ~10% to escape local optima)
        if restart < 6:
            assignment = best_assignment[:]
            for i in range(n_vars):
                if random.random() < 0.10:
                    assignment[i] = not assignment[i]

    return best_assignment
