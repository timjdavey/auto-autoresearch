"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: greedy + 1-opt with multi-start.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time

TIME_LIMIT = 55  # seconds, leave margin for harness


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

    def delta_append(perm, elem):
        """Compute delta in score if elem is appended to perm."""
        delta = 0
        for i in range(len(perm)):
            delta += matrix[perm[i]][elem]
        return delta

    def delta_swap(perm, i, j):
        """Compute delta in score if positions i and j are swapped."""
        delta = 0
        ei, ej = perm[i], perm[j]
        for k in range(len(perm)):
            if k != i and k != j:
                if k < i:
                    delta -= matrix[perm[k]][ei]
                elif k > i:
                    delta -= matrix[ei][perm[k]]
                if k < j:
                    delta -= matrix[perm[k]][ej]
                elif k > j:
                    delta -= matrix[ej][perm[k]]
        for k in range(len(perm)):
            if k != i and k != j:
                if k < i:
                    delta += matrix[perm[k]][ej]
                elif k > i:
                    delta += matrix[ej][perm[k]]
                if k < j:
                    delta += matrix[perm[k]][ei]
                elif k > j:
                    delta += matrix[ei][perm[k]]
        if i < j:
            delta -= matrix[ei][ej]
            delta += matrix[ej][ei]
        else:
            delta -= matrix[ej][ei]
            delta += matrix[ei][ej]
        return delta

    def construct_from_rowsums():
        """Heuristic initialization based on row sums (out-going weight)."""
        row_sums = [sum(matrix[i]) for i in range(n)]
        perm = sorted(range(n), key=lambda i: -row_sums[i])  # Descending

        current_score = 0
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                current_score += matrix[perm[i]][perm[j]]

        return perm, current_score

    def greedy_construct():
        """Greedy construction with random tie-breaking."""
        perm = []
        current_score = 0
        available = set(range(n))

        while available:
            best_delta = -float('inf')
            candidates = []

            for elem in available:
                delta = delta_append(perm, elem)
                if delta > best_delta:
                    best_delta = delta
                    candidates = [elem]
                elif delta == best_delta:
                    candidates.append(elem)

            best_elem = random.choice(candidates)  # Tie-breaking with randomness
            perm.append(best_elem)
            current_score += best_delta
            available.remove(best_elem)

        return perm, current_score

    def local_search_1opt(perm, current_score):
        """1-opt local search (first improvement)."""
        improved = True
        while improved:
            improved = False

            for i in range(n):
                for j in range(i + 1, n):
                    delta = delta_swap(perm, i, j)
                    if delta > 0:
                        perm[i], perm[j] = perm[j], perm[i]
                        current_score += delta
                        improved = True
                        break

                if improved:
                    break

        return perm, current_score

    start_time = time.time()

    def compute_score(perm):
        """Compute full score of a permutation."""
        score = 0
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                score += matrix[perm[i]][perm[j]]
        return score

    def perturbation(perm, k):
        """Apply k random swaps to perturb solution."""
        perm = perm.copy()
        for _ in range(k):
            i, j = random.sample(range(n), 2)
            if i > j:
                i, j = j, i
            perm[i], perm[j] = perm[j], perm[i]
        return perm

    # --- Iterated Local Search ---
    # Try rowsum initialization first
    perm, current_score = construct_from_rowsums()
    perm, current_score = local_search_1opt(perm, current_score)

    best_perm = perm.copy()
    best_score = current_score

    # Try greedy initialization if time permits
    if (time.time() - start_time) < TIME_LIMIT * 0.1:
        perm, current_score = greedy_construct()
        perm, current_score = local_search_1opt(perm, current_score)
        if current_score > best_score:
            best_perm = perm.copy()
            best_score = current_score

    k = max(1, n // 20)  # Perturbation strength: ~5-6 swaps for large instances

    # ILS: perturb and restart local search, using remaining time
    while (time.time() - start_time) < TIME_LIMIT:
        # Perturb current best solution
        perm = perturbation(best_perm, k)
        perm_score = compute_score(perm)

        # Apply local search to perturbed solution
        perm, perm_score = local_search_1opt(perm, perm_score)

        # Accept if better than incumbent best
        if perm_score > best_score:
            best_perm = perm.copy()
            best_score = perm_score

    return best_perm
