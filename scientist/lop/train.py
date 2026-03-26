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
    time_limit = 55  # Leave 5s margin

    def score(perm):
        """Score of a permutation (sum of upper triangle)."""
        s = 0
        for i in range(len(perm)):
            pi = perm[i]
            for j in range(i + 1, len(perm)):
                s += matrix[pi][perm[j]]
        return s

    def greedy_construct(seed=None, randomized=False):
        """Greedy construction: build permutation element by element."""
        if seed is not None:
            random.seed(seed)

        perm = []
        remaining = set(range(n))

        while remaining:
            if time.time() - start_time > time_limit:
                perm.extend(sorted(remaining))
                break

            # Find element that maximizes incremental contribution
            candidates = []
            best_gain = -float('inf')

            for idx in remaining:
                # Calculate gain from adding idx at the end
                gain = sum(matrix[perm[i]][idx] for i in range(len(perm)))
                candidates.append((gain, idx))
                if gain > best_gain:
                    best_gain = gain

            # If randomized, pick from top candidates
            if randomized and len(candidates) > 1:
                # Pick from top 30% of candidates
                candidates.sort(reverse=True)
                top_k = max(1, len(candidates) // 3)
                best_idx = candidates[random.randint(0, top_k - 1)][1]
            else:
                # Pick best
                best_idx = max(candidates, key=lambda x: x[0])[1]

            perm.append(best_idx)
            remaining.remove(best_idx)

        return perm

    def insertion_construct(seed=None):
        """Insertion-based greedy: insert each element at best position."""
        if seed is not None:
            random.seed(seed)

        perm = []
        remaining = set(range(n))

        # Start with a random element
        if remaining:
            start_idx = random.choice(list(remaining))
            perm.append(start_idx)
            remaining.remove(start_idx)

        while remaining:
            if time.time() - start_time > time_limit:
                perm.extend(sorted(remaining))
                break

            # Find element and position that maximizes contribution
            best_idx = None
            best_pos = 0
            best_gain = -float('inf')

            for idx in remaining:
                # Try inserting at each position
                for pos in range(len(perm) + 1):
                    # Calculate gain from inserting idx at position pos
                    gain = 0
                    # Contribution from elements before pos
                    for i in range(pos):
                        gain += matrix[perm[i]][idx]
                    # Contribution from elements after pos
                    for j in range(pos, len(perm)):
                        gain += matrix[idx][perm[j]]

                    if gain > best_gain:
                        best_gain = gain
                        best_idx = idx
                        best_pos = pos

            if best_idx is not None:
                perm.insert(best_pos, best_idx)
                remaining.remove(best_idx)

        return perm

    def row_sum_construct(seed=None):
        """Row-sum based ordering: order elements by total weight."""
        if seed is not None:
            random.seed(seed)

        # Calculate row sums (sum of outgoing weights)
        row_sums = [sum(matrix[i]) for i in range(n)]

        # Order elements by descending row sum with randomization
        indices = list(range(n))
        indices.sort(key=lambda i: row_sums[i], reverse=True)

        # Add some randomization to avoid deterministic ordering
        if random.random() < 0.5:
            # Reverse half the time
            indices = indices[:n//2] + indices[n//2:][::-1]

        return indices

    def local_search_1opt(perm):
        """Best-improvement 1-opt: try all adjacent swaps, take best."""
        improved = True
        iterations = 0
        while improved and time.time() - start_time < time_limit:
            improved = False
            base_score = score(perm)
            best_swap = None
            best_new_score = base_score

            # Try all adjacent swaps
            for i in range(n - 1):
                perm[i], perm[i+1] = perm[i+1], perm[i]
                new_score = score(perm)

                if new_score > best_new_score:
                    best_new_score = new_score
                    best_swap = i
                    improved = True

                perm[i], perm[i+1] = perm[i+1], perm[i]

            # Apply best swap if found
            if best_swap is not None:
                perm[best_swap], perm[best_swap+1] = perm[best_swap+1], perm[best_swap]
                iterations += 1

        return perm

    def local_search_2opt(perm, max_iterations=100):
        """2-opt with best-improvement."""
        improved = True
        iterations = 0
        while improved and iterations < max_iterations and time.time() - start_time < time_limit:
            improved = False
            base_score = score(perm)
            best_swap = None
            best_new_score = base_score

            # Try all pairs (i, j) with i < j
            for i in range(n):
                for j in range(i + 2, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)

                    if new_score > best_new_score:
                        best_new_score = new_score
                        best_swap = (i, j)
                        improved = True

                    perm[i], perm[j] = perm[j], perm[i]

            # Apply best swap if found
            if best_swap is not None:
                i, j = best_swap
                perm[i], perm[j] = perm[j], perm[i]
                iterations += 1

        return perm

    def local_search_2opt_first_improvement(perm, max_iterations=100):
        """2-opt with first-improvement (take first improving move)."""
        improved = True
        iterations = 0
        while improved and iterations < max_iterations and time.time() - start_time < time_limit:
            improved = False
            base_score = score(perm)

            # Try all pairs (i, j) with i < j, take first improvement
            for i in range(n):
                for j in range(i + 2, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)

                    if new_score > base_score:
                        # First improvement found, take it and restart
                        improved = True
                        break
                    else:
                        perm[i], perm[j] = perm[j], perm[i]

                if improved:
                    break

            iterations += 1

        return perm

# Multi-start with perturbation-based diversification
    best_perm = None
    best_score = -float('inf')

    # Multi-starts for diversification
    if n <= 75:
        num_starts = 7
    elif n <= 100:
        num_starts = 5
    else:
        num_starts = 3

    for start in range(num_starts):
        if time.time() - start_time > time_limit:
            break

        # Alternate: insertion construction (60%) and greedy (40%)
        if start % 5 < 3:
            # Insertion-based (60% of starts)
            perm = insertion_construct(seed=100 + start)
        else:
            # Greedy (40% of starts): alternate between deterministic and randomized
            randomized = (start % 2 == 1)
            perm = greedy_construct(seed=100 + start, randomized=randomized)

        # Apply 2-opt first: alternate between best-improvement and first-improvement for diversity
        if time.time() - start_time < time_limit - 3:
            if start % 2 == 0:
                perm = local_search_2opt(perm, max_iterations=100)
            else:
                perm = local_search_2opt_first_improvement(perm, max_iterations=100)

        # Then apply 1-opt for fine-tuning
        perm = local_search_1opt(perm)

        new_score = score(perm)
        if new_score > best_score:
            best_score = new_score
            best_perm = perm

    # Perturbation-based refinement: try perturbing best solution and re-optimizing
    if best_perm is not None and time.time() - start_time < time_limit - 2:
        random.seed(42)
        num_perturbations = 5 if n <= 75 else 3  # More attempts on small instances
        for perturb in range(num_perturbations):  # Try multiple perturbations
            if time.time() - start_time > time_limit:
                break

            # Apply random swaps to perturb the best solution — more aggressive
            perm = best_perm.copy()
            num_swaps = max(2, n // 4)  # Swap ~25% of elements (was 10%)
            for _ in range(num_swaps):
                i, j = random.sample(range(n), 2)
                perm[i], perm[j] = perm[j], perm[i]

            # Re-optimize from perturbed solution: 2-opt before 1-opt
            if time.time() - start_time < time_limit - 2:
                perm = local_search_2opt(perm, max_iterations=80)
            perm = local_search_1opt(perm)

            new_score = score(perm)
            if new_score > best_score:
                best_score = new_score
                best_perm = perm

    return best_perm if best_perm is not None else list(range(n))
