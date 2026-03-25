"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""
import random


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

    n = len(matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    start_time = time.time()
    time_limit = 54.0  # Stop before hard 60s timeout

    def compute_score(perm):
        """Compute sum of upper-diagonal elements."""
        score = 0
        for i in range(n):
            for j in range(i + 1, n):
                score += matrix[perm[i]][perm[j]]
        return score

    def compute_score_fast(perm, i, j):
        """Compute score difference for swapping positions i and j."""
        # Score change from swapping i and j in permutation
        # Elements that change are those that compare (i,j) or (j,i) with other elements
        delta = 0

        # Elements between i and j
        for k in range(i + 1, j):
            # Before: perm[i] < perm[k] < perm[j]
            # After: perm[j] < perm[k] < perm[i]
            before = matrix[perm[i]][perm[k]] + matrix[perm[k]][perm[j]]
            after = matrix[perm[j]][perm[k]] + matrix[perm[k]][perm[i]]
            delta += after - before

        # Before position i
        for k in range(i):
            before = matrix[perm[k]][perm[i]] + matrix[perm[k]][perm[j]]
            after = matrix[perm[k]][perm[j]] + matrix[perm[k]][perm[i]]
            delta += after - before

        # After position j
        for k in range(j + 1, n):
            before = matrix[perm[i]][perm[k]] + matrix[perm[j]][perm[k]]
            after = matrix[perm[j]][perm[k]] + matrix[perm[i]][perm[k]]
            delta += after - before

        # i and j relationship
        before = matrix[perm[i]][perm[j]]
        after = matrix[perm[j]][perm[i]]
        delta += after - before

        return delta

    def optimize(perm):
        """Run first-improvement 1-opt local search with random 2-opt escape moves."""
        score = compute_score(perm)
        improved = True
        no_improve_count = 0

        # First-improvement 1-opt local search
        opt_limit = 50.0
        while improved and time.time() - start_time < opt_limit:
            improved = False
            for i in range(n):
                for j in range(i + 1, n):
                    if time.time() - start_time >= opt_limit:
                        return perm, score

                    delta = compute_score_fast(perm, i, j)
                    if delta > 0:
                        perm[i], perm[j] = perm[j], perm[i]
                        score += delta
                        improved = True
                        no_improve_count = 0
                        break

                if improved:
                    break

            if not improved:
                no_improve_count += 1
                # Try 5 random 2-opt moves to escape plateaus
                if no_improve_count <= 3 and time.time() - start_time < opt_limit - 1.0:
                    for _ in range(5):
                        i = random.randint(0, n - 3)
                        j = random.randint(i + 2, n - 1)
                        delta = compute_score_fast(perm, i, j)
                        if delta > 0:
                            perm[i], perm[j] = perm[j], perm[i]
                            score += delta
                            improved = True
                            no_improve_count = 0
                            break

        return perm, score

    best_perm = None
    best_score = -1

    # Try greedy initialization based on row sums (outgoing weights)
    row_sums = [sum(matrix[i]) for i in range(n)]
    perm = sorted(range(n), key=lambda i: row_sums[i], reverse=True)
    perm, score = optimize(perm[:])
    if score > best_score:
        best_score = score
        best_perm = perm

    # Try greedy initialization based on net weight (row_sum - col_sum)
    # Elements with high net weight prefer outgoing, should go early
    col_sums = [sum(matrix[i][j] for i in range(n)) for j in range(n)]
    net_weights = [row_sums[i] - col_sums[i] for i in range(n)]
    perm = sorted(range(n), key=lambda i: net_weights[i], reverse=True)
    perm, score = optimize(perm[:])
    if score > best_score:
        best_score = score
        best_perm = perm

    # Random restarts with time budget
    num_restarts = 3 if n <= 100 else 2
    for _ in range(num_restarts):
        if time.time() - start_time >= 51.0:
            break
        perm = list(range(n))
        random.shuffle(perm)
        perm, score = optimize(perm[:])
        if score > best_score:
            best_score = score
            best_perm = perm

    return best_perm if best_perm else list(range(n))
