"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


import time
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
    n = len(matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    start_time = time.time()
    time_limit = 55.0  # Conservative limit to avoid timeout

    # Greedy initialization: order by sum of incoming weights
    col_sums = [sum(matrix[i][j] for i in range(n)) for j in range(n)]
    perm = sorted(range(n), key=lambda j: col_sums[j], reverse=True)
    current_score = _upper_triangle_sum(matrix, perm)

    # Best-improvement 1-opt local search
    improved = True
    while improved and (time.time() - start_time) < time_limit:
        improved = False
        best_move_delta = 0
        best_move_i = -1
        best_move_j = -1

        for i in range(n):
            if (time.time() - start_time) >= time_limit:
                break

            node = perm[i]

            # Evaluate all possible moves and pick the best
            for j in range(n):
                if j == i:
                    continue

                delta = _calculate_delta(matrix, perm, i, j)
                if delta > best_move_delta:
                    best_move_delta = delta
                    best_move_i = i
                    best_move_j = j

        if best_move_delta > 0:
            # Perform the best move
            node = perm[best_move_i]
            perm.pop(best_move_i)
            perm.insert(best_move_j, node)
            current_score += best_move_delta
            improved = True

    return perm


def _calculate_delta(matrix, perm, from_pos, to_pos):
    """
    Calculate score change for moving node at from_pos to to_pos.

    Returns the delta (new_score - old_score). Positive means improvement.
    Uses O(n) delta calculation instead of O(n²) full recalculation.
    """
    n = len(perm)
    node = perm[from_pos]
    delta = 0

    if from_pos < to_pos:
        # Moving right: nodes between from_pos+1 and to_pos shift left
        for pos in range(from_pos + 1, to_pos + 1):
            other = perm[pos]
            # Node moves right, so:
            # - loses contribution from being left of 'other' at position from_pos
            # - gains contribution from being right of 'other' at position to_pos
            delta -= matrix[node][other]
            delta += matrix[other][node]
    else:
        # Moving left: nodes between to_pos and from_pos-1 shift right
        for pos in range(to_pos, from_pos):
            other = perm[pos]
            # Node moves left, so:
            # - loses contribution from being right of 'other'
            # - gains contribution from being left of 'other'
            delta -= matrix[other][node]
            delta += matrix[node][other]

    return delta


def _upper_triangle_sum(matrix, perm):
    """Compute LOP objective: sum of matrix[perm[i]][perm[j]] for all i < j."""
    n = len(perm)
    score = 0
    for i in range(n):
        pi = perm[i]
        for j in range(i + 1, n):
            score += matrix[pi][perm[j]]
    return score
