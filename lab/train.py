"""
train.py — TSP solver. THIS IS THE FILE THE AGENT MODIFIES.

Current implementation: ILS with 2-opt + Or-opt-2/3 (2 and 3-city segment relocation).
"""

import math
import random
import time


def _dist(coords, i, j):
    dx = coords[i][0] - coords[j][0]
    dy = coords[i][1] - coords[j][1]
    return math.sqrt(dx * dx + dy * dy)


def _nn_tour(coords, start):
    n = len(coords)
    visited = [False] * n
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        current = tour[-1]
        best_dist = float("inf")
        best_city = -1
        for j in range(n):
            if not visited[j]:
                dx = coords[current][0] - coords[j][0]
                dy = coords[current][1] - coords[j][1]
                d = math.sqrt(dx * dx + dy * dy)
                if d < best_dist:
                    best_dist = d
                    best_city = j
        tour.append(best_city)
        visited[best_city] = True
    return tour


def _tour_length(coords, tour):
    n = len(tour)
    total = 0.0
    for i in range(n):
        total += _dist(coords, tour[i], tour[(i + 1) % n])
    return total


def _two_opt(coords, tour):
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = (_dist(coords, a, c) + _dist(coords, b, d)
                         - _dist(coords, a, b) - _dist(coords, c, d))
                if delta < -1e-10:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    improved = True
    return tour


def _or_opt(coords, tour, k):
    """Or-opt: relocate segments of length k to better positions.
    Applies one best improvement per pass, restarts until no improvement.
    """
    n = len(tour)
    if n <= k + 1:
        return tour

    improved = True
    while improved:
        improved = False
        for i in range(n):
            # Segment: positions i, i+1, ..., i+k-1 (with wrap)
            seg_idx = [(i + s) % n for s in range(k)]
            seg = [tour[idx] for idx in seg_idx]
            prev = tour[(i - 1) % n]
            nxt = tour[(i + k) % n]

            # Skip if prev or nxt is in the segment (can happen for small n)
            if prev in seg or nxt in seg:
                continue

            # Savings from removing segment
            savings = (_dist(coords, prev, seg[0])
                       + _dist(coords, seg[-1], nxt)
                       - _dist(coords, prev, nxt))

            best_gain = 1e-10
            best_ins = -1
            best_rev = False

            for j in range(n):
                if j in seg_idx:
                    continue
                j_next = (j + 1) % n
                if j_next in seg_idx:
                    continue
                cj = tour[j]
                cj_next = tour[j_next]

                # Forward insertion
                d_ins = (_dist(coords, cj, seg[0]) + _dist(coords, seg[-1], cj_next)
                         - _dist(coords, cj, cj_next))
                gain = savings - d_ins
                if gain > best_gain:
                    best_gain = gain
                    best_ins = j
                    best_rev = False

                # Reversed insertion
                if k > 1:
                    d_ins_r = (_dist(coords, cj, seg[-1]) + _dist(coords, seg[0], cj_next)
                               - _dist(coords, cj, cj_next))
                    gain_r = savings - d_ins_r
                    if gain_r > best_gain:
                        best_gain = gain_r
                        best_ins = j
                        best_rev = True

            if best_ins >= 0:
                # Rebuild tour: remove segment, insert at best_ins
                seg_to_use = seg[::-1] if best_rev else seg
                seg_set = set(seg_idx)

                # Build non-segment tour in order (starting from i+k)
                non_seg = []
                idx = (i + k) % n
                while len(non_seg) < n - k:
                    non_seg.append(tour[idx])
                    idx = (idx + 1) % n

                # Find insertion position in non-seg
                ins_city = tour[best_ins]
                ins_pos = non_seg.index(ins_city)

                # Rebuild
                tour = non_seg[:ins_pos + 1] + seg_to_use + non_seg[ins_pos + 1:]
                improved = True
                break  # Start new pass

    return tour


def _double_bridge(tour, rng):
    n = len(tour)
    cuts = sorted(rng.sample(range(1, n), 4))
    a, b, c, d = cuts
    return tour[:a] + tour[c:d] + tour[b:c] + tour[a:b] + tour[d:]


def solve(coords: list[tuple[int, int]]) -> list[int]:
    n = len(coords)
    if n == 0:
        return []
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]

    deadline = time.time() + 28
    rng = random.Random(42)

    # Phase 1: multi-start NN
    best_tour = None
    best_len = float("inf")
    for start in range(n):
        tour = _nn_tour(coords, start)
        length = _tour_length(coords, tour)
        if length < best_len:
            best_len = length
            best_tour = tour[:]
        if time.time() > deadline:
            break

    # Phase 2: full local search on best initial tour
    best_tour = _two_opt(coords, best_tour)
    best_tour = _or_opt(coords, best_tour, 2)
    best_tour = _or_opt(coords, best_tour, 3)
    best_tour = _two_opt(coords, best_tour)
    best_len = _tour_length(coords, best_tour)

    # Phase 3: ILS with double-bridge
    current_tour = best_tour[:]
    while time.time() < deadline:
        perturbed = _double_bridge(current_tour, rng)
        perturbed = _two_opt(coords, perturbed)
        perturbed = _or_opt(coords, perturbed, 2)
        perturbed = _or_opt(coords, perturbed, 3)
        perturbed_len = _tour_length(coords, perturbed)

        if perturbed_len < best_len:
            best_len = perturbed_len
            best_tour = perturbed[:]
            current_tour = perturbed[:]
        else:
            current_tour = best_tour[:]

    return best_tour
