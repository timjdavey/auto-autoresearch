"""
train.py — MAX-SAT solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(n_vars, clauses)` that takes a CNF formula
and returns a truth assignment as a list of bools.

Current implementation: greedy sequential assignment (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


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

    # --- Greedy sequential assignment ---
    # For each variable, pick the value that satisfies more currently-unsatisfied clauses.
    assignment = [False] * n_vars

    for var_idx in range(n_vars):
        var = var_idx + 1  # 1-indexed

        count_true = 0
        count_false = 0
        for clause in clauses:
            if var not in clause and -var not in clause:
                continue
            # Check if clause is already satisfied by previously assigned vars
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

    return assignment
