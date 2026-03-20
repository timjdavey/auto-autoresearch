"""
train.py — TSP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(coords)` that takes a list of (x, y)
coordinates and returns a tour as a list of city indices.

Current implementation: nearest-neighbour heuristic (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import math


def solve(coords: list[tuple[int, int]]) -> list[int]:
    """
    Solve TSP for the given coordinates.

    Args:
        coords: list of (x, y) tuples, one per city

    Returns:
        tour: list of city indices (permutation of 0..n-1)
    """
    n = len(coords)
    if n == 0:
        return []
    if n == 1:
        return [0]

    # --- Nearest-neighbour heuristic ---
    visited = [False] * n
    tour = [0]
    visited[0] = True

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