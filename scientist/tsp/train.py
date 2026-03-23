"""
train.py — TSP solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(coords)` that takes a list of (x, y)
coordinates and returns a tour as a list of city indices.

Current implementation: trivial index-order tour.
The agent should improve this to maximise avg_improvement across all instances.
"""


def solve(coords: list[tuple[int, int]]) -> list[int]:
    """
    Solve TSP for the given coordinates.

    Args:
        coords: list of (x, y) tuples, one per city

    Returns:
        tour: list of city indices (permutation of 0..n-1)
    """
    return list(range(len(coords)))