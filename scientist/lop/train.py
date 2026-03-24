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

    start_time = time.time()
    time_limit = 50  # Conservative margin for safety

    # Greedy initialization: sort by net outgoing weight
    scores = []
    for i in range(n):
        out_weight = sum(matrix[i])
        in_weight = sum(matrix[j][i] for j in range(n))
        net_weight = out_weight - in_weight
        scores.append((net_weight, i))

    scores.sort(reverse=True)
    perm = [idx for _, idx in scores]

    def score(perm):
        return sum(matrix[perm[i]][perm[j]] for i in range(n) for j in range(i + 1, n))

    # Phase 1: Adjacent 2-opt (fast, O(n) per iteration)
    current_score = score(perm)
    improved = True
    while improved and time.time() - start_time < time_limit * 0.4:
        improved = False
        for i in range(n - 1):
            perm[i], perm[i + 1] = perm[i + 1], perm[i]
            new_score = score(perm)
            if new_score > current_score:
                current_score = new_score
                improved = True
            else:
                perm[i], perm[i + 1] = perm[i + 1], perm[i]

    # Phase 2: Sliding window 2-opt (faster than full, smarter than adjacent)
    window_size = min(15, n // 5)  # Adaptive window: check nearby positions
    improved = True
    while improved and time.time() - start_time < time_limit:
        improved = False
        for i in range(n):
            if time.time() - start_time >= time_limit:
                break
            # Only try swaps within sliding window around position i
            for j in range(max(i + 2, i - window_size), min(n, i + window_size + 1)):
                if j <= i:
                    continue
                # Try swapping positions i and j
                perm[i], perm[j] = perm[j], perm[i]
                new_score = score(perm)
                if new_score > current_score:
                    current_score = new_score
                    improved = True
                else:
                    perm[i], perm[j] = perm[j], perm[i]

    return perm
