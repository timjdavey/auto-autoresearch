"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: identity permutation (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


import time
import random


def _compute_score(matrix, perm):
    """Compute score: sum of elements strictly above diagonal."""
    n = len(perm)
    score = 0
    for i in range(n):
        for j in range(i + 1, n):
            score += matrix[perm[i]][perm[j]]
    return score


def _greedy_init_outgoing(matrix):
    """Greedy initialization: order nodes by sum of outgoing weights."""
    n = len(matrix)
    outgoing = [sum(matrix[i]) for i in range(n)]
    indices = list(range(n))
    indices.sort(key=lambda i: outgoing[i], reverse=True)
    return indices


def _greedy_init_incoming(matrix):
    """Greedy initialization: order nodes by sum of incoming weights."""
    n = len(matrix)
    incoming = [sum(matrix[j][i] for j in range(n)) for i in range(n)]
    indices = list(range(n))
    indices.sort(key=lambda i: incoming[i], reverse=True)
    return indices


def _greedy_init_net(matrix):
    """Greedy initialization: order nodes by net weight (outgoing - incoming)."""
    n = len(matrix)
    outgoing = [sum(matrix[i]) for i in range(n)]
    incoming = [sum(matrix[j][i] for j in range(n)) for i in range(n)]
    indices = list(range(n))
    indices.sort(key=lambda i: outgoing[i] - incoming[i], reverse=True)
    return indices


def _greedy_init_by_edges(matrix):
    """Greedy initialization: prioritize nodes with highest-weight edges.

    Build ordering by greedily selecting node pairs with highest edge weights,
    ensuring nodes are placed to maximize contribution of important edges.
    """
    n = len(matrix)
    # Collect all edges with weights
    edges = []
    for i in range(n):
        for j in range(n):
            if i != j:
                edges.append((matrix[i][j], i, j))

    # Sort by weight descending
    edges.sort(reverse=True)

    # Greedily build ordering: prefer nodes from high-weight edges
    selected = set()
    ordering = []

    # First pass: add nodes from highest-weight edges
    for weight, src, dst in edges:
        if src not in selected:
            selected.add(src)
            ordering.append(src)
        if dst not in selected and len(selected) < n:
            selected.add(dst)
            ordering.append(dst)
        if len(selected) == n:
            break

    # Add any remaining nodes
    for i in range(n):
        if i not in selected:
            ordering.append(i)

    return ordering


def _random_init(matrix):
    """Random initialization: shuffle all indices."""
    n = len(matrix)
    indices = list(range(n))
    random.shuffle(indices)
    return indices


def _perturb_solution(perm, k=3):
    """Perturb a solution by making k random swaps."""
    perm = list(perm)  # Copy
    n = len(perm)
    for _ in range(k):
        i, j = random.sample(range(n), 2)
        if i > j:
            i, j = j, i
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def _score_delta_swap(matrix, perm, i, j):
    """Compute score delta for swapping positions i and j (i < j)."""
    pi, pj = perm[i], perm[j]
    delta = 0

    # Direct swap effect
    delta += matrix[pj][pi] - matrix[pi][pj]

    # Effects on intermediate positions i < k < j
    for k in range(i + 1, j):
        pk = perm[k]
        delta += matrix[pj][pk] - matrix[pi][pk]      # Edge from pi/pj to pk
        delta += matrix[pk][pi] - matrix[pk][pj]      # Edge from pk to pi/pj

    return delta


def _best_improvement_1opt(matrix, perm, time_limit=55):
    """Local search: best-improvement 1-opt with delta scoring."""
    start = time.time()
    n = len(perm)
    improved = True

    while improved and (time.time() - start) < time_limit:
        improved = False
        best_delta = 0
        best_i, best_j = -1, -1

        # Try all 1-opt swaps: find the best improvement
        for i in range(n):
            for j in range(i + 1, n):
                # Compute delta for this swap
                delta = _score_delta_swap(matrix, perm, i, j)

                if delta > best_delta:
                    best_delta = delta
                    best_i, best_j = i, j

        if best_delta > 0:
            # Apply best swap found
            perm[best_i], perm[best_j] = perm[best_j], perm[best_i]
            improved = True

    return perm


def _first_improvement_1opt(matrix, perm, time_limit=55):
    """Local search: first-improvement 1-opt with delta scoring."""
    start = time.time()
    n = len(perm)
    improved = True
    current_score = _compute_score(matrix, perm)

    while improved and (time.time() - start) < time_limit:
        improved = False

        # Try all 1-opt swaps: swap positions i and j
        for i in range(n):
            for j in range(i + 1, n):
                # Compute delta for this swap
                delta = _score_delta_swap(matrix, perm, i, j)

                if delta > 0:
                    # Swap and accept
                    perm[i], perm[j] = perm[j], perm[i]
                    current_score += delta
                    improved = True
                    break

            if improved:
                break

    return perm


def _first_improvement_2opt(matrix, perm, time_limit=5):
    """Local search: first-improvement 2-opt (segment reversal) with delta scoring."""
    start = time.time()
    n = len(perm)
    improved = True

    while improved and (time.time() - start) < time_limit:
        improved = False

        # Try all 2-opt moves: reverse segment [i, j]
        for i in range(n):
            for j in range(i + 2, n):  # Segment must be at least length 2
                # Compute delta for reversing segment [i+1, j]
                delta = 0
                for k in range(i + 1, j):
                    # Edges crossing the reversal
                    delta += matrix[perm[k]][perm[i]] - matrix[perm[i]][perm[k]]
                    delta += matrix[perm[j]][perm[k]] - matrix[perm[k]][perm[j]]

                # Also edges at boundaries
                delta += matrix[perm[j]][perm[i]] - matrix[perm[i]][perm[j]]

                if delta > 0:
                    # Reverse segment
                    perm[i+1:j+1] = reversed(perm[i+1:j+1])
                    improved = True
                    break

            if improved:
                break

    return perm




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

    best_perm = None
    best_score = -1
    start_time = time.time()
    total_time_limit = 55

    # Try multiple initialization strategies (greedy for diversity)
    init_strategies = [
        _greedy_init_outgoing,
        _greedy_init_incoming,
        _greedy_init_net,
    ]

    for init_func in init_strategies:
        if (time.time() - start_time) >= total_time_limit - 1.0:
            break

        # Initialize with this strategy
        perm = init_func(matrix)

        # Use best-improvement 1-opt for initial solutions to get higher quality starting points
        remaining_time = total_time_limit - (time.time() - start_time) - 2.0
        if remaining_time > 0:
            perm = _best_improvement_1opt(matrix, perm, time_limit=remaining_time)

        # Track best
        score = _compute_score(matrix, perm)
        if score > best_score:
            best_score = score
            best_perm = perm

    # Iterated Local Search (ILS): perturb best solution and re-optimize
    ils_iteration = 0
    while (time.time() - start_time) < total_time_limit - 2.0:
        if best_perm is None:
            break

        # Perturbation: make k random swaps to current best
        # Smaller magnitude allows more iterations within time budget
        perturbation_magnitude = max(5, n // 17)
        perm = _perturb_solution(best_perm, k=perturbation_magnitude)

        # 1-opt local search from perturbed solution
        remaining_time = total_time_limit - (time.time() - start_time) - 1.0
        if remaining_time <= 0.5:
            break

        one_opt_time = max(remaining_time * 0.7, 0.2)
        perm = _first_improvement_1opt(matrix, perm, time_limit=one_opt_time)

        # 2-opt local search to catch segment reversals
        remaining_time = total_time_limit - (time.time() - start_time) - 0.5
        if remaining_time > 0.2:
            two_opt_time = min(remaining_time * 0.2, 1.0)
            perm = _first_improvement_2opt(matrix, perm, time_limit=two_opt_time)

        # Track best
        score = _compute_score(matrix, perm)
        if score > best_score:
            best_score = score
            best_perm = perm

        ils_iteration += 1

    return best_perm if best_perm is not None else list(range(n))
