"""
train.py — LOP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(matrix)` that takes a square weight matrix
and returns a permutation of row/column indices.

Current implementation: Greedy initialization + Simulated Annealing.
The agent should improve this to maximise avg_improvement across all instances.
"""


import time
import random
import math

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
    time_limit = 55  # Leave 5s buffer before hard 60s limit

    # Helper: calculate score for a permutation
    def score(p):
        s = 0
        for i in range(n):
            for j in range(i+1, n):
                s += matrix[p[i]][p[j]]
        return s

    def run_sa_polish(init_perm):
        """Run SA followed by limited 1-opt polish. Return (best_perm, best_score)."""
        perm = init_perm[:]
        best_score = score(perm)
        best_perm = perm[:]

        # Adaptive SA parameters based on instance size
        if n <= 75:
            temperature = max(best_score * 0.2, 200)
            cooling_rate = 0.9995
            min_temp = 0.0001
            num_swaps_factor = 5  # Good balance: cooling vs quality
        else:
            # For large instances, faster cooling to preserve time for polish
            temperature = max(best_score * 0.15, 150)
            cooling_rate = 0.998
            min_temp = 0.001
            num_swaps_factor = 6  # Good balance: cooling vs quality

        while temperature > min_temp and time.time() - start_time < time_limit:
            num_swaps = max(1, n // num_swaps_factor)
            for _ in range(num_swaps):
                if time.time() - start_time >= time_limit:
                    break

                i = random.randint(0, n-1)
                j = random.randint(0, n-1)
                if i == j:
                    continue

                if i > j:
                    i, j = j, i

                perm[i], perm[j] = perm[j], perm[i]
                new_score = score(perm)
                delta = new_score - best_score

                if delta > 0 or random.random() < math.exp(delta / temperature):
                    best_score = new_score
                    best_perm = perm[:]
                else:
                    perm[i], perm[j] = perm[j], perm[i]

            temperature *= cooling_rate

        # Limited 1-opt polish: max 15 passes to allow more restarts
        perm = best_perm[:]
        max_passes = 15
        pass_count = 0
        improved = True

        while improved and pass_count < max_passes and time.time() - start_time < time_limit:
            improved = False
            pass_count += 1

            # First-improvement: stop after first improvement found
            for i in range(n):
                if time.time() - start_time >= time_limit:
                    break
                for j in range(i+1, n):
                    perm[i], perm[j] = perm[j], perm[i]
                    new_score = score(perm)

                    if new_score > best_score:
                        best_score = new_score
                        improved = True
                        break  # First improvement found, move to next pass

                    perm[i], perm[j] = perm[j], perm[i]

                if improved:
                    break  # Move to next pass after first improvement

        return best_perm, best_score

    def perturb(perm, intensity=0.1):
        """Perturb permutation by random swaps. Intensity = fraction of swaps."""
        p = perm[:]
        num_swaps = max(1, int(n * intensity))
        for _ in range(num_swaps):
            i = random.randint(0, n-1)
            j = random.randint(0, n-1)
            if i != j:
                p[i], p[j] = p[j], p[i]
        return p

    # Greedy initialization
    row_sums = [sum(row) for row in matrix]
    init_perm = sorted(range(n), key=lambda i: -row_sums[i])

    # First run
    best_perm, best_score = run_sa_polish(init_perm)
    overall_best_perm = best_perm[:]
    overall_best_score = best_score

    # Multi-restart with perturbation (4 additional restarts if time allows)
    for restart_idx in range(4):
        if time.time() - start_time >= time_limit:
            break

        # Perturb previous best and run SA + polish again
        perturbed = perturb(overall_best_perm, intensity=0.2)
        perm, score_val = run_sa_polish(perturbed)

        if score_val > overall_best_score:
            overall_best_perm = perm
            overall_best_score = score_val

    return overall_best_perm
