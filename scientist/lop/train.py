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

    def compute_score(perm):
        """Compute the LOP objective score for a given permutation."""
        score = 0
        for i in range(n):
            for j in range(i + 1, n):
                score += matrix[perm[i]][perm[j]]
        return score

    def greedy_construction(randomize=False):
        """Greedy construction with optional randomization in tie-breaking."""
        perm = []
        remaining = set(range(n))

        while remaining:
            candidates = []
            best_score = float('-inf')

            for elem in remaining:
                # Compute the score gain from adding this element at the end
                score_gain = sum(matrix[perm[i]][elem] for i in range(len(perm)))

                if score_gain > best_score:
                    best_score = score_gain
                    candidates = [elem]
                elif score_gain == best_score:
                    candidates.append(elem)

            if randomize and len(candidates) > 1:
                best_elem = random.choice(candidates)
            else:
                best_elem = candidates[0]

            perm.append(best_elem)
            remaining.remove(best_elem)

        return perm

    # Multi-start: try multiple constructions
    num_starts = 15
    best_perm = None
    best_score = -1

    for start in range(num_starts):
        perm = greedy_construction(randomize=(start > 0))  # First start is deterministic

        # Apply 2-opt local search with time limit
        start_time = time.time()
        time_limit = 50.0 / num_starts  # Divide time budget among starts

        improved = True
        while improved:
            if time.time() - start_time > time_limit:
                break

            improved = False
            best_delta = 0
            best_i, best_j = -1, -1

            # 2-opt: try all pairs (i, j) where i < j and find best improvement
            for i in range(n - 1):
                for j in range(i + 1, n):
                    # Calculate score delta if we reverse the segment from i to j
                    delta = 0

                    # When we reverse segment [i, j], the affected edges change
                    # Edges between positions outside [i,j] and inside [i,j]
                    for k in range(i):
                        # k is before i
                        delta -= matrix[perm[k]][perm[i]]
                        delta += matrix[perm[k]][perm[j]]

                    for k in range(j + 1, n):
                        # k is after j
                        delta -= matrix[perm[j]][perm[k]]
                        delta += matrix[perm[i]][perm[k]]

                    # Edges within reversed segment change direction
                    for a in range(i, j):
                        for b in range(a + 1, j + 1):
                            delta -= matrix[perm[a]][perm[b]]
                            delta += matrix[perm[b]][perm[a]]

                    if delta > best_delta:
                        best_delta = delta
                        best_i, best_j = i, j

            if best_delta > 0:
                # Reverse the segment from best_i to best_j
                perm[best_i:best_j + 1] = reversed(perm[best_i:best_j + 1])
                improved = True

        # Track best solution across all starts
        score = compute_score(perm)
        if score > best_score:
            best_score = score
            best_perm = perm

    return best_perm
