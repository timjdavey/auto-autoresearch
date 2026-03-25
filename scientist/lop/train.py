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

    n = len(matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    def score(perm):
        """Compute total score for a permutation."""
        total = 0
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                total += matrix[perm[i]][perm[j]]
        return total

    def swap_delta(perm, i, j):
        """Compute score change if positions i and j are swapped (i < j)."""
        delta = 0
        pi, pj = perm[i], perm[j]

        # Contribution change from pairs between i and j
        for k in range(i + 1, j):
            pk = perm[k]
            delta += (matrix[pj][pk] - matrix[pi][pk]) + (matrix[pk][pi] - matrix[pk][pj])

        # Contribution change from direct pair (i, j)
        delta += matrix[pj][pi] - matrix[pi][pj]

        return delta

    # Try multiple initializations and keep the best
    initializations = []

    # Greedy by row sum
    row_sums = [sum(matrix[i]) for i in range(n)]
    perm_row = sorted(range(n), key=lambda i: row_sums[i], reverse=True)
    initializations.append(perm_row)

    # Greedy by column sum
    col_sums = [sum(matrix[i][j] for i in range(n)) for j in range(n)]
    perm_col = sorted(range(n), key=lambda i: col_sums[i], reverse=True)
    initializations.append(perm_col)

    # Greedy by combined (row + col)
    combined_sums = [row_sums[i] + col_sums[i] for i in range(n)]
    perm_combined = sorted(range(n), key=lambda i: combined_sums[i], reverse=True)
    initializations.append(perm_combined)

    best_perm = None
    best_score_val = -1

    start_time = time.time()
    time_limit = 50  # Leave 10s margin for safety

    for init_perm in initializations:
        if time.time() - start_time >= time_limit:
            break

        perm = init_perm[:]

        # Local search: 1-opt with first-improvement
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            for i in range(n):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 1, n):
                    delta = swap_delta(perm, i, j)
                    if delta > 0:
                        improved = True
                        perm[i], perm[j] = perm[j], perm[i]
                        break
                if improved:
                    break

        current_score = score(perm)
        if current_score > best_score_val:
            best_score_val = current_score
            best_perm = perm

    return best_perm

    return perm
