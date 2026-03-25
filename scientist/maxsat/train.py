"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: WalkSAT with greedy initialization.
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
    """Initialize using greedy assignment."""
    assignment = [False] * n_vars

    for var_idx in range(n_vars):
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


def get_unsat_clauses(assignment: list[bool], clauses: list[list[int]]) -> list[int]:
    """Return indices of unsatisfied clauses."""
    unsat = []
    for i, clause in enumerate(clauses):
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            var_val = assignment[var_idx]
            if (lit > 0 and var_val) or (lit < 0 and not var_val):
                satisfied = True
                break
        if not satisfied:
            unsat.append(i)
    return unsat


def local_search_1opt(assignment: list[bool], clauses: list[list[int]], time_limit: float) -> list[bool]:
    """One-step look-ahead local search: use best-improvement strategy."""
    best_assignment = assignment.copy()
    best_unsat = count_unsat(best_assignment, clauses)

    start_time = time.time()
    improved = True

    while improved and time.time() - start_time < time_limit:
        improved = False
        best_var_improvement = -1  # Track which variable gives best improvement
        best_var_unsat = best_unsat

        for var_idx in range(len(best_assignment)):
            if time.time() - start_time >= time_limit:
                break

            # Test flipping this variable
            test_assignment = best_assignment.copy()
            test_assignment[var_idx] = not test_assignment[var_idx]
            test_unsat = count_unsat(test_assignment, clauses)

            if test_unsat < best_var_unsat:
                best_var_unsat = test_unsat
                best_var_improvement = var_idx
                improved = True

        # Apply the best move found in this iteration
        if improved:
            best_assignment[best_var_improvement] = not best_assignment[best_var_improvement]
            best_unsat = best_var_unsat

    return best_assignment


def walksat_search(assignment: list[bool], clauses: list[list[int]], time_limit: float) -> list[bool]:
    """Smart WalkSAT: prefer beneficial moves, with random exploration."""
    best_assignment = assignment.copy()
    best_unsat = count_unsat(best_assignment, clauses)
    current_assignment = assignment.copy()

    start_time = time.time()
    check_interval = max(100, len(clauses) // 10)
    iteration = 0
    walk_prob = 0.3  # Probability of random move (vs smart move)

    while time.time() - start_time < time_limit:
        unsat_indices = get_unsat_clauses(current_assignment, clauses)

        if not unsat_indices:
            best_assignment = current_assignment.copy()
            best_unsat = 0
            return best_assignment

        # Pick a random unsatisfied clause
        clause = clauses[random.choice(unsat_indices)]

        # Decide: smart move or random move?
        if random.random() < walk_prob:
            # Random move for exploration
            var_idx = abs(random.choice(clause)) - 1
        else:
            # Smart move: pick variable that reduces unsatisfied clauses most
            best_var_idx = None
            best_impact = float('inf')

            for lit in clause:
                var_idx = abs(lit) - 1
                # Test flipping this variable
                test_assignment = current_assignment.copy()
                test_assignment[var_idx] = not test_assignment[var_idx]
                impact = count_unsat(test_assignment, clauses)

                if impact < best_impact:
                    best_impact = impact
                    best_var_idx = var_idx

            var_idx = best_var_idx if best_var_idx is not None else abs(random.choice(clause)) - 1

        current_assignment[var_idx] = not current_assignment[var_idx]

        # Track best solution periodically
        iteration += 1
        if iteration % check_interval == 0:
            current_unsat = count_unsat(current_assignment, clauses)
            if current_unsat < best_unsat:
                best_unsat = current_unsat
                best_assignment = current_assignment.copy()

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

    # Try greedy initialization + WalkSAT + local search
    greedy_assignment = greedy_init(n_vars, clauses)
    improved = walksat_search(greedy_assignment, clauses, 4.0)
    improved = local_search_1opt(improved, clauses, 1.0)
    unsat_count = count_unsat(improved, clauses)
    if unsat_count < best_unsat:
        best_unsat = unsat_count
        best_solution = improved

    # Try random restarts with WalkSAT
    num_restarts = max(1, min(10, int((time_limit - (time.time() - start_time) - 2.0) / 3.0)))
    time_per_restart = (time_limit - (time.time() - start_time) - 2.0) / max(1, num_restarts)

    for _ in range(num_restarts):
        if time.time() - start_time >= time_limit - 2.0:
            break

        # Random initialization
        random_assignment = [random.choice([True, False]) for _ in range(n_vars)]
        improved = walksat_search(random_assignment, clauses, max(0.5, time_per_restart * 0.9))
        improved = local_search_1opt(improved, clauses, max(0.1, time_per_restart * 0.1))
        unsat_count = count_unsat(improved, clauses)

        if unsat_count < best_unsat:
            best_unsat = unsat_count
            best_solution = improved

    return best_solution if best_solution is not None else greedy_init(n_vars, clauses)
