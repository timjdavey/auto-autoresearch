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
    time_limit = 55  # seconds, leaving margin for overhead

    def score(perm):
        """Compute LOP objective: sum of matrix[perm[i]][perm[j]] for i < j."""
        s = 0
        for i in range(n):
            pi = perm[i]
            for j in range(i + 1, n):
                s += matrix[pi][perm[j]]
        return s

    def greedy_init(seed=None):
        """Greedy construction: order nodes by descending sum of outgoing weights."""
        # Compute sum of outgoing weights for each node
        row_sums = [sum(matrix[i]) for i in range(n)]
        # Sort nodes by row sum (descending), with tie-breaking by seed for diversity
        nodes = sorted(range(n), key=lambda i: (row_sums[i], random.random() if seed else 0), reverse=True)
        return nodes

    def local_search(perm):
        """First-improvement 1-opt local search."""
        current_score = score(perm)
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            for i in range(n - 1):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 1, n):
                    # Try swapping positions i and j
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)
                    if new_score > current_score:
                        # Accept first improvement and restart
                        current_score = new_score
                        improved = True
                        break
                    # Revert swap
                    perm[i], perm[j] = perm[j], perm[i]
                if improved:
                    break
        return perm, current_score

    # Multi-start: run from different initializations
    best_perm = None
    best_score = -1
    num_restarts = max(1, int((time_limit - 5) / (time_limit / 3)))  # Allocate time for 2-3 starts

    for restart in range(num_restarts):
        if time.time() - start_time >= time_limit:
            break
        random.seed(restart)
        perm = greedy_init(seed=restart)
        perm, curr_score = local_search(perm)
        if curr_score > best_score:
            best_score = curr_score
            best_perm = perm

    return best_perm if best_perm else list(range(n))
