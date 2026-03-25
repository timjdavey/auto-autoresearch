"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


def solve(matrix: list[list[int]]) -> list[int]:
    """
    Solve the Linear Ordering Problem.

    Find a permutation of indices to maximise the sum of elements strictly
    above the main diagonal of the reordered matrix:
        score = sum over all i < j of matrix[perm[i]][perm[j]]

    Args:
        matrix: n x n weight matrix. matrix[i][j] is the weight from i to j.
                Generally non-symmetric (matrix[i][j] != matrix[j][i]).

    Returns:
        perm: list of length n where perm is a permutation of 0..n-1.
              The permutation defines the row/column reordering.
    """
    import time
    import random

    n = len(matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    start_time = time.time()
    time_limit = 55.0

    def score(perm):
        """Compute LOP objective: sum of matrix[perm[i]][perm[j]] for i < j."""
        s = 0
        for i in range(n):
            pi = perm[i]
            for j in range(i + 1, n):
                s += matrix[pi][perm[j]]
        return s

    def greedy_init():
        """Greedy construction: order nodes by descending (row_sum + col_sum)."""
        row_sums = [sum(matrix[i]) for i in range(n)]
        col_sums = [sum(matrix[i][j] for i in range(n)) for j in range(n)]
        combined_sums = [row_sums[i] + col_sums[i] for i in range(n)]
        nodes = sorted(range(n), key=lambda i: (combined_sums[i], random.random()), reverse=True)
        return nodes

    def local_search(perm):
        """First-improvement local search: 1-opt then 2-opt."""
        current_score = score(perm)

        # Phase 1: 1-opt (swap two positions)
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            for i in range(n - 1):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 1, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)
                    if new_score > current_score:
                        current_score = new_score
                        improved = True
                        break
                    perm[i], perm[j] = perm[j], perm[i]
            if improved:
                break

        # Phase 2: 2-opt (reverse a segment)
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            for i in range(n - 2):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 2, n):
                    # Reverse segment [i+1, j]
                    perm[i+1:j+1] = perm[i+1:j+1][::-1]
                    new_score = score(perm)
                    if new_score > current_score:
                        current_score = new_score
                        improved = True
                        break
                    perm[i+1:j+1] = perm[i+1:j+1][::-1]
            if improved:
                break

        return score(perm)

    best_perm = None
    best_score = -float('inf')

    # Multi-start with 5 runs
    for restart in range(5):
        if time.time() - start_time >= time_limit:
            break

        random.seed(restart * 137)  # Deterministic but varied seeds
        perm = greedy_init()
        score_val = local_search(perm)

        if score_val > best_score:
            best_score = score_val
            best_perm = perm[:]

    return best_perm if best_perm is not None else list(range(n))
