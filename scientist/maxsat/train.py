"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: Smart WalkSAT with timeout safeguards.
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
    time_limit = 55.0  # 55 seconds per solve to stay under 60s limit

    best_assignment = [False] * n_vars
    best_unsat_count = count_unsatisfied(clauses, best_assignment)

    # Multi-start WalkSAT: try multiple random initializations
    # Balance runs and iterations: more iterations per run for large instances
    if n_vars > 250:
        num_runs = 45  # Keep good diversity for large instances
    else:
        num_runs = max(1, 400 // (n_vars // 50 + 1))

    for run in range(num_runs):
        if time.time() - start_time > time_limit:
            break

        # Random initialization
        assignment = [random.choice([True, False]) for _ in range(n_vars)]

        # Initialize clause weights for dynamic selection
        clause_weights = [1.0] * len(clauses)

        # WalkSAT iterations - more for large instances to use freed time
        if n_vars > 250:
            max_iterations = min(1000000, 300000 + n_vars * 500)
        else:
            max_iterations = min(1000000, 100000 + n_vars * 200)

        no_improve_count = 0
        last_improvement_unsat = count_unsatisfied(clauses, assignment)

        for iteration in range(max_iterations):
            if time.time() - start_time > time_limit:
                break

            unsat_clauses = get_unsatisfied_clauses(clauses, assignment)
            if not unsat_clauses:
                return assignment  # All satisfied

            # Escape moves: if stuck for 5000 iterations, do a perturbation
            if iteration % 5000 == 0 and iteration > 0:
                current_unsat = count_unsatisfied(clauses, assignment)
                if current_unsat >= last_improvement_unsat:
                    # Stuck - flip 3-5 random variables to escape
                    num_flips = random.randint(3, 5)
                    for _ in range(num_flips):
                        var_idx = random.randint(0, n_vars - 1)
                        assignment[var_idx] = not assignment[var_idx]
                else:
                    last_improvement_unsat = current_unsat

            # Weighted selection: pick unsatisfied clause based on weights
            unsat_indices = [i for i, clause in enumerate(clauses) if not is_satisfied(clause, assignment)]
            unsat_weights = [clause_weights[i] for i in unsat_indices]
            total_weight = sum(unsat_weights)

            # Pick clause proportional to weight
            rand_val = random.uniform(0, total_weight)
            cum_weight = 0
            clause_idx = unsat_indices[0]
            for idx, weight in zip(unsat_indices, unsat_weights):
                cum_weight += weight
                if rand_val <= cum_weight:
                    clause_idx = idx
                    break

            clause = clauses[clause_idx]

            # WalkSAT: with probability p_walk, pick random variable; else pick best
            # Higher walk probability for large instances to escape local optima
            if n_vars > 250:
                p_walk = 0.6 if iteration < max_iterations // 4 else (0.4 if iteration < 3 * max_iterations // 4 else 0.2)
            else:
                p_walk = 0.45 if iteration < max_iterations // 4 else (0.25 if iteration < 3 * max_iterations // 4 else 0.1)

            if random.random() < p_walk:
                # Random walk: pick random variable from the clause
                var_idx = abs(random.choice(clause)) - 1
                assignment[var_idx] = not assignment[var_idx]
            else:
                # Greedy: evaluate impact and pick best
                best_var = None
                best_impact = None

                for lit in clause:
                    var_idx = abs(lit) - 1
                    # Calculate impact of flipping this variable
                    impact = evaluate_flip_impact(clauses, assignment, var_idx)

                    if best_impact is None or impact > best_impact:
                        best_impact = impact
                        best_var = var_idx

                if best_var is not None:
                    assignment[best_var] = not assignment[best_var]

                unsat_count = count_unsatisfied(clauses, assignment)
                if unsat_count < best_unsat_count:
                    best_unsat_count = unsat_count
                    best_assignment = assignment[:]

            # Update clause weights: unsatisfied clauses increase in weight
            for i in range(len(clauses)):
                if not is_satisfied(clauses[i], assignment):
                    clause_weights[i] += 0.02
                else:
                    clause_weights[i] = max(1.0, clause_weights[i] - 0.005)  # Decay satisfied clauses

        # Post-processing: pure greedy 1-opt refinement on all variables
        improved = True
        passes = 0
        max_passes = 2
        while improved and passes < max_passes and time.time() - start_time < time_limit - 1.0:
            improved = False
            passes += 1
            for var_idx in range(n_vars):
                impact = evaluate_flip_impact(clauses, assignment, var_idx)
                if impact > 0:
                    assignment[var_idx] = not assignment[var_idx]
                    unsat_count = count_unsatisfied(clauses, assignment)
                    if unsat_count < best_unsat_count:
                        best_unsat_count = unsat_count
                        best_assignment = assignment[:]
                        improved = True
                    else:
                        assignment[var_idx] = not assignment[var_idx]  # Revert

        # 2-opt refinement: try swapping pairs of variables (limited to avoid timeout)
        # Focus on variables that appear in unsatisfied clauses for efficiency
        # Skip 2-opt for very large instances to save time
        if time.time() - start_time < time_limit - 1.0 and best_unsat_count > 0 and n_vars <= 250:
            unsat_indices = [i for i, clause in enumerate(clauses) if not is_satisfied(clause, best_assignment)]
            if unsat_indices:
                # Collect variables in unsatisfied clauses
                vars_in_unsat = set()
                for idx in unsat_indices[:min(100, len(unsat_indices))]:  # Limit to first 100 unsatisfied
                    for lit in clauses[idx]:
                        vars_in_unsat.add(abs(lit) - 1)

                vars_to_try = list(vars_in_unsat)[:min(50, len(vars_in_unsat))]  # Limit pairs

                for i in range(len(vars_to_try)):
                    if time.time() - start_time > time_limit - 0.5:
                        break
                    for j in range(i + 1, len(vars_to_try)):
                        var_i = vars_to_try[i]
                        var_j = vars_to_try[j]

                        # Try flipping both variables
                        assignment[var_i] = not assignment[var_i]
                        assignment[var_j] = not assignment[var_j]
                        unsat_count = count_unsatisfied(clauses, assignment)

                        if unsat_count < best_unsat_count:
                            best_unsat_count = unsat_count
                            best_assignment = assignment[:]
                        else:
                            # Revert
                            assignment[var_i] = not assignment[var_i]
                            assignment[var_j] = not assignment[var_j]

        # Ultra-fast 3-opt: only on smallest subset of critical variables, skip for large instances
        if time.time() - start_time < time_limit - 0.5 and best_unsat_count > 0 and n_vars <= 250:
            unsat_indices = [i for i, clause in enumerate(clauses) if not is_satisfied(clause, best_assignment)]
            if unsat_indices:
                # Get only TOP critical variables (those appearing in most unsatisfied clauses)
                var_freq = {}
                for idx in unsat_indices[:min(20, len(unsat_indices))]:
                    for lit in clauses[idx]:
                        v = abs(lit) - 1
                        var_freq[v] = var_freq.get(v, 0) + 1

                # Take only top 3 most critical variables
                critical_vars = sorted(var_freq.keys(), key=lambda v: var_freq[v], reverse=True)[:min(3, len(var_freq))]

                # Try all triplets of these 3 variables (only 1 triplet if exactly 3)
                for i in range(len(critical_vars)):
                    if time.time() - start_time > time_limit - 0.1:
                        break
                    for j in range(i + 1, len(critical_vars)):
                        for k in range(j + 1, len(critical_vars)):
                            var_i = critical_vars[i]
                            var_j = critical_vars[j]
                            var_k = critical_vars[k]

                            # Try flipping all three variables
                            best_assignment[var_i] = not best_assignment[var_i]
                            best_assignment[var_j] = not best_assignment[var_j]
                            best_assignment[var_k] = not best_assignment[var_k]
                            unsat_count = count_unsatisfied(clauses, best_assignment)

                            if unsat_count < best_unsat_count:
                                best_unsat_count = unsat_count
                            else:
                                # Revert
                                best_assignment[var_i] = not best_assignment[var_i]
                                best_assignment[var_j] = not best_assignment[var_j]
                                best_assignment[var_k] = not best_assignment[var_k]

    return best_assignment


def get_unsatisfied_clauses(clauses: list[list[int]], assignment: list[bool]) -> list[list[int]]:
    """Get all currently unsatisfied clauses."""
    unsat = []
    for clause in clauses:
        if not is_satisfied(clause, assignment):
            unsat.append(clause)
    return unsat


def is_satisfied(clause: list[int], assignment: list[bool]) -> bool:
    """Check if a clause is satisfied by the assignment."""
    for lit in clause:
        var_idx = abs(lit) - 1
        if lit > 0 and assignment[var_idx]:
            return True
        if lit < 0 and not assignment[var_idx]:
            return True
    return False


def count_unsatisfied(clauses: list[list[int]], assignment: list[bool]) -> int:
    """Count unsatisfied clauses."""
    return sum(1 for clause in clauses if not is_satisfied(clause, assignment))


def evaluate_flip_impact(clauses: list[list[int]], assignment: list[bool], var_idx: int) -> int:
    """
    Evaluate the impact of flipping variable var_idx.
    Returns a score: positive means improvement, negative means worse.
    """
    score = 0
    for clause in clauses:
        was_sat = is_satisfied(clause, assignment)
        # Temporarily flip to evaluate
        assignment[var_idx] = not assignment[var_idx]
        now_sat = is_satisfied(clause, assignment)
        assignment[var_idx] = not assignment[var_idx]  # Flip back

        if was_sat and not now_sat:
            score -= 1  # Loses a satisfied clause
        elif not was_sat and now_sat:
            score += 1  # Gains a satisfied clause

    return score
