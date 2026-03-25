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
    time_limit = 55.0  # Leave 5s buffer before 60s hard limit

    timing = {}  # Track timing of each phase

    def score(perm):
        """Calculate score for a given permutation."""
        total = 0
        for i in range(len(perm)):
            for j in range(i + 1, len(perm)):
                total += matrix[perm[i]][perm[j]]
        return total

    def score_delta(perm, old_pos, new_pos, elem):
        """
        Calculate change in score when moving element from old_pos to new_pos.
        elem is the actual element value to move.
        """
        delta = 0
        if old_pos < new_pos:
            # Moving right: elem was above some, now below some
            for k in range(old_pos + 1, new_pos + 1):
                delta -= matrix[elem][perm[k]]
                delta += matrix[perm[k]][elem]
        else:
            # Moving left: elem was below some, now above some
            for k in range(new_pos, old_pos):
                delta += matrix[elem][perm[k]]
                delta -= matrix[perm[k]][elem]
        return delta

    # --- Greedy insertion with multiple random restarts ---
    init_start = time.time()
    best_perm = None
    best_score_init = -1

    # Try restarts with different element orderings
    num_restarts = max(2, n // 40)  # Conservative restarts to prevent timeouts
    for restart in range(num_restarts):
        if time.time() - start_time >= time_limit * 0.2:  # Use 20% of time for init
            break

        # Randomize element insertion order (except first element)
        if restart == 0:
            elem_order = list(range(n))
        else:
            elem_order = [0] + sorted(range(1, n), key=lambda x: random.random())

        # Greedy insertion
        perm = [elem_order[0]]
        current_score = 0

        for elem in elem_order[1:]:
            best_pos = 0
            best_score = current_score

            # Try inserting elem at each position
            for pos in range(len(perm) + 1):
                test_perm = perm[:pos] + [elem] + perm[pos:]
                test_score = score(test_perm)
                if test_score > best_score:
                    best_score = test_score
                    best_pos = pos

            perm.insert(best_pos, elem)
            current_score = best_score

        # Track best solution found
        if current_score > best_score_init:
            best_score_init = current_score
            best_perm = perm[:]

    timing['init'] = time.time() - init_start
    perm = best_perm
    current_score = best_score_init

    # --- 1-opt local search: best-improvement with time limit ---
    opt1_start = time.time()
    improved = True
    while improved and time.time() - start_time < time_limit:
        improved = False
        best_score = current_score
        best_move = None  # (i, j) or None

        for i in range(n):
            if time.time() - start_time >= time_limit:
                break
            elem = perm[i]
            for j in range(n):
                if i == j:
                    continue
                delta = score_delta(perm, i, j, elem)
                new_score = current_score + delta
                if new_score > best_score:
                    best_score = new_score
                    best_move = (i, j)

        if best_move is not None:
            i, j = best_move
            elem = perm[i]
            perm.pop(i)
            perm.insert(j, elem)
            current_score = best_score
            improved = True

    timing['opt1'] = time.time() - opt1_start

    # --- Or-opt: move pairs of consecutive elements ---
    orop_start = time.time()
    if time.time() - start_time < time_limit * 0.85:
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            best_score = current_score
            best_move = None  # (i, j) or None

            for i in range(n - 1):
                if time.time() - start_time >= time_limit:
                    break
                # Try moving pair [perm[i], perm[i+1]] to position j
                pair = [perm[i], perm[i+1]]
                for j in range(n):
                    if j == i or j == i + 1:
                        continue
                    # Remove pair from position i
                    test_perm = perm[:i] + perm[i+2:]
                    # Insert pair at position j (adjusted for removal)
                    if j > i:
                        test_perm = test_perm[:j-2] + pair + test_perm[j-2:]
                    else:
                        test_perm = test_perm[:j] + pair + test_perm[j:]
                    test_score = score(test_perm)
                    if test_score > best_score:
                        best_score = test_score
                        best_move = (i, j)

            if best_move is not None:
                i, j = best_move
                pair = [perm[i], perm[i+1]]
                perm = perm[:i] + perm[i+2:]
                if j > i:
                    perm = perm[:j-2] + pair + perm[j-2:]
                else:
                    perm = perm[:j] + pair + perm[j:]
                current_score = best_score
                improved = True

    timing['orop'] = time.time() - orop_start

    # --- 2-opt local search: best-improvement with time limit ---
    opt2_start = time.time()
    if n <= 100 and time.time() - start_time < time_limit * 0.8:
        improved = True
        while improved and time.time() - start_time < time_limit:
            improved = False
            best_score = current_score
            best_move = None  # (i, j) or None

            for i in range(n):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i + 2, n):
                    # Try reversing perm[i:j+1]
                    test_perm = perm[:i] + perm[i:j+1][::-1] + perm[j+1:]
                    test_score = score(test_perm)
                    if test_score > best_score:
                        best_score = test_score
                        best_move = (i, j)

            if best_move is not None:
                i, j = best_move
                perm = perm[:i] + perm[i:j+1][::-1] + perm[j+1:]
                current_score = best_score
                improved = True

    timing['opt2'] = time.time() - opt2_start
    total_time = time.time() - start_time

    # Debug timing info (uncomment to see where time is spent)
    # print(f"LOP solver timing (n={n}): init={timing.get('init', 0):.2f}s, opt1={timing.get('opt1', 0):.2f}s, opt2={timing.get('opt2', 0):.2f}s, total={total_time:.2f}s")

    return perm
