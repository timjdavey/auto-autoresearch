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
    import random

    n = len(matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]

    def score(perm):
        """Compute the LOP score for a permutation."""
        s = 0
        for i in range(n):
            pi = perm[i]
            for j in range(i + 1, n):
                s += matrix[pi][perm[j]]
        return s

    def greedy_construct(shuffle_prob=0.0):
        """Build permutation greedily by best marginal contribution, with optional randomization."""
        used = [False] * n
        perm = []
        for _ in range(n):
            best_idx = -1
            best_gain = -1
            candidates = []
            for idx in range(n):
                if used[idx]:
                    continue
                gain = 0
                for j in range(len(perm)):
                    gain += matrix[perm[j]][idx]
                candidates.append((gain, idx))
                if gain > best_gain:
                    best_gain = gain
                    best_idx = idx
            # With small probability, pick a near-best solution instead of the best
            if random.random() < shuffle_prob and len(candidates) > 1:
                candidates.sort(reverse=True)
                # Pick from top 2-3 candidates
                idx_to_use = candidates[min(1, len(candidates)-1)][1]
            else:
                idx_to_use = best_idx
            used[idx_to_use] = True
            perm.append(idx_to_use)
        return perm

    def local_search_1opt(perm, max_iters=None):
        """First-improvement 1-opt local search."""
        if max_iters is None:
            max_iters = float('inf')
        iteration = 0
        improved = True
        while improved and iteration < max_iters:
            improved = False
            current_score = score(perm)
            for i in range(n):
                for j in range(i + 1, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)
                    if new_score > current_score:
                        improved = True
                        iteration += 1
                        break
                    else:
                        perm[i], perm[j] = perm[j], perm[i]
                if improved:
                    break
            if not improved:
                break

    def local_search_2opt(perm, max_iters=5):
        """Limited 2-opt local search: try swapping pairs of non-adjacent elements."""
        for iteration in range(max_iters):
            current_score = score(perm)
            best_i, best_j = -1, -1
            best_score = current_score

            for i in range(n):
                for j in range(i + 2, n):  # Skip adjacent pairs
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)
                    if new_score > best_score:
                        best_score = new_score
                        best_i, best_j = i, j
                    perm[i], perm[j] = perm[j], perm[i]

            if best_i != -1:
                perm[best_i], perm[best_j] = perm[best_j], perm[best_i]
            else:
                break

    def local_search_3opt(perm, max_iters=3):
        """Simple 3-opt: try reversing contiguous subsequences."""
        for iteration in range(max_iters):
            current_score = score(perm)
            best_i, best_j = -1, -1
            best_score = current_score

            for i in range(n):
                for j in range(i + 2, n + 1):  # Subsequence [i:j]
                    perm[i:j] = perm[i:j][::-1]
                    new_score = score(perm)
                    if new_score > best_score:
                        best_score = new_score
                        best_i, best_j = i, j
                    perm[i:j] = perm[i:j][::-1]  # Reverse back

            if best_i != -1:
                perm[best_i:best_j] = perm[best_i:best_j][::-1]
            else:
                break


    if n <= 75:
        # Small: greedy + best-improvement 1-opt
        perm = greedy_construct()
        improved = True
        while improved:
            improved = False
            current_score = score(perm)
            best_i, best_j = -1, -1
            best_score = current_score

            for i in range(n):
                for j in range(i + 1, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)
                    if new_score > best_score:
                        best_score = new_score
                        best_i, best_j = i, j
                        improved = True
                    perm[i], perm[j] = perm[j], perm[i]

            if improved:
                perm[best_i], perm[best_j] = perm[best_j], perm[best_i]
    else:
        # Medium/Large: Greedy + aggressive 1-opt + 2-opt + 3-opt
        perm = greedy_construct(shuffle_prob=0.05)  # Slight randomization
        local_search_1opt(perm, max_iters=50)  # 1-opt iterations
        local_search_2opt(perm, max_iters=20)  # 2-opt iterations
        local_search_3opt(perm, max_iters=10)  # 3-opt iterations

    return perm
