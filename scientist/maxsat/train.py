"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: Smart WalkSAT with greedy init and local search.
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


def simulated_annealing_intensify(assignment, clauses, n_vars, time_limit_start, time_limit):
    """Simulated annealing intensification on best solution."""
    best_assignment = assignment[:]
    best_unsat = count_unsatisfied(best_assignment, clauses)
    current_assignment = assignment[:]
    current_unsat = best_unsat

    # SA parameters (stable from Trial 48: 97.92%)
    initial_temp = 16.0
    final_temp = 0.08
    cooling_rate = 0.992
    temp = initial_temp

    sa_iterations = 0
    max_sa_iterations = 5000

    while temp > final_temp and time.time() - time_limit_start < time_limit - 0.5 and sa_iterations < max_sa_iterations:
        sa_iterations += 1

        # Random move: flip one variable
        var_idx = random.randint(0, n_vars - 1)
        current_assignment[var_idx] = not current_assignment[var_idx]
        new_unsat = count_unsatisfied(current_assignment, clauses)

        # SA acceptance criterion
        if new_unsat < current_unsat:
            # Accept improvement
            current_unsat = new_unsat
            if current_unsat < best_unsat:
                best_unsat = current_unsat
                best_assignment = current_assignment[:]
        else:
            # Accept worse move with probability
            delta = new_unsat - current_unsat
            if random.random() < (2.718 ** (-delta / max(temp, 0.01))):
                # Accept
                current_unsat = new_unsat
            else:
                # Reject: revert the flip
                current_assignment[var_idx] = not current_assignment[var_idx]

        # Cool down
        temp *= cooling_rate

    return best_assignment if best_unsat < count_unsatisfied(assignment, clauses) else assignment


def solve(n_vars: int, clauses: list[list[int]]) -> list[bool]:
    """Solve MAX-SAT using Smart WalkSAT + 1-opt + 2-opt + Simulated Annealing."""
    if n_vars == 0:
        return []

    start_time = time.time()
    time_limit = 55.0  # 55s budget with 5s margin

    best_assignment = None
    best_unsat = float('inf')

    # Multi-start: try multiple random initializations
    for restart in range(35):
        if time.time() - start_time > time_limit:
            break

        # Initialize: random assignment
        assignment = [random.choice([True, False]) for _ in range(n_vars)]
        current_unsat = count_unsatisfied(assignment, clauses)

        # Smart WalkSAT main loop
        max_flips = 18000
        random_walk_prob = 0.3

        for flip_count in range(max_flips):
            if time.time() - start_time > time_limit:
                break

            unsatisfied = get_unsatisfied_clauses(assignment, clauses)
            if not unsatisfied:
                # All clauses satisfied
                return assignment

            if current_unsat < best_unsat:
                best_unsat = current_unsat
                best_assignment = assignment[:]

            # Pick random unsatisfied clause
            clause = clauses[unsatisfied[random.randint(0, len(unsatisfied) - 1)]]

            # Decide: smart move or random walk
            if random.random() < random_walk_prob:
                # Random walk: pick random variable from clause
                var_idx = abs(clause[random.randint(0, 2)]) - 1
            else:
                # Smart move: pick variable with best flip impact
                best_var_idx = abs(clause[0]) - 1
                best_impact = evaluate_flip(assignment, clauses, best_var_idx)

                for lit in clause[1:]:
                    var_idx = abs(lit) - 1
                    impact = evaluate_flip(assignment, clauses, var_idx)
                    if impact < best_impact:
                        best_impact = impact
                        best_var_idx = var_idx

                var_idx = best_var_idx

            # Flip the variable
            assignment[var_idx] = not assignment[var_idx]
            current_unsat = count_unsatisfied(assignment, clauses)

        # After WalkSAT, apply 1-opt local search
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            for var_idx in range(n_vars):
                new_unsat = evaluate_flip(assignment, clauses, var_idx)
                if new_unsat < current_unsat:
                    assignment[var_idx] = not assignment[var_idx]
                    current_unsat = new_unsat
                    improved = True
                    if current_unsat < best_unsat:
                        best_unsat = current_unsat
                        best_assignment = assignment[:]

        # Apply 2-opt local search if time allows
        if time.time() - start_time < time_limit - 1:
            improved = True
            max_2opt_passes = 3
            passes = 0
            while improved and passes < max_2opt_passes and time.time() - start_time < time_limit - 0.5:
                improved = False
                passes += 1
                for i in range(n_vars - 1):
                    if time.time() - start_time > time_limit - 0.5:
                        break
                    for j in range(i + 1, min(i + 50, n_vars)):
                        # Try flipping both variables
                        assignment[i] = not assignment[i]
                        assignment[j] = not assignment[j]
                        new_unsat = count_unsatisfied(assignment, clauses)

                        if new_unsat < current_unsat:
                            current_unsat = new_unsat
                            improved = True
                            if current_unsat < best_unsat:
                                best_unsat = current_unsat
                                best_assignment = assignment[:]
                        else:
                            # Revert if no improvement
                            assignment[i] = not assignment[i]
                            assignment[j] = not assignment[j]

    # Final simulated annealing intensification on best solution
    if best_assignment is not None and time.time() - start_time < time_limit - 0.5:
        best_assignment = simulated_annealing_intensify(best_assignment, clauses, n_vars, start_time, time_limit)

    return best_assignment if best_assignment is not None else assignment
