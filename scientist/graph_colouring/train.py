"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: greedy colouring with natural vertex ordering (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


def improve_coloring(adj: list[int], colouring: list[int], n_nodes: int) -> list[int]:
    """Try to reduce the number of colors by reassigning nodes to lower colors."""
    improved = list(colouring)
    for _ in range(3):
        for node in range(n_nodes):
            used_by_neighbors = {improved[u] for u in adj[node] if improved[u] != -1}
            # Find the lowest color this node can take
            for color in range(max(improved) + 2):
                if color not in used_by_neighbors:
                    improved[node] = color
                    break
    return improved


def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using as few colours as possible.

    Args:
        adj: adjacency list. adj[i] is a sorted list of neighbours of node i.
        n_nodes: number of nodes (== len(adj))
        n_edges: number of edges

    Returns:
        colouring: list of length n_nodes where colouring[i] is the colour
                   assigned to node i. Colours are non-negative integers
                   starting from 0.
    """
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    def dsatur_coloring(use_randomness=False):
        """DSatur with optional randomness in tie-breaking."""
        colouring = [-1] * n_nodes
        uncolored = set(range(n_nodes))

        while uncolored:
            # Find all candidates with maximum saturation degree
            best_sat = -1
            candidates = []

            for v in uncolored:
                sat_degree = len({colouring[u] for u in adj[v] if colouring[u] != -1})
                if sat_degree > best_sat:
                    best_sat = sat_degree
                    candidates = [(v, len(adj[v]))]
                elif sat_degree == best_sat:
                    candidates.append((v, len(adj[v])))

            # Sort by degree (descending)
            candidates.sort(key=lambda x: x[1], reverse=True)

            if use_randomness and len(candidates) > 1:
                # With randomness, randomly pick from top candidates
                top_k = min(3, len(candidates))
                node = random.choice([c[0] for c in candidates[:top_k]])
            else:
                node = candidates[0][0]

            uncolored.remove(node)

            # Assign minimum available color
            used = {colouring[u] for u in adj[node] if colouring[u] != -1}
            colour = 0
            while colour in used:
                colour += 1
            colouring[node] = colour

        return colouring

    # Run DSatur with deterministic ordering
    best_colouring = dsatur_coloring(use_randomness=False)
    best_colouring = improve_coloring(adj, best_colouring, n_nodes)
    best_colors = max(best_colouring) + 1

    # Try different randomized variants with 16 iterations
    for i in range(16):
        random.seed(i)  # Deterministic seed for reproducibility
        colouring = dsatur_coloring(use_randomness=True)
        colouring = improve_coloring(adj, colouring, n_nodes)
        num_colors = max(colouring) + 1
        if num_colors < best_colors:
            best_colors = num_colors
            best_colouring = colouring

    return best_colouring
