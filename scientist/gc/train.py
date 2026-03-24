"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: greedy colouring with natural vertex ordering (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""


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

    # --- Greedy colouring with natural ordering ---
    colouring = [-1] * n_nodes
    for node in range(n_nodes):
        used = set()
        for neighbour in adj[node]:
            if colouring[neighbour] != -1:
                used.add(colouring[neighbour])
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring
