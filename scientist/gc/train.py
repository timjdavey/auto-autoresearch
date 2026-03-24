"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR (Degree of Saturation) greedy colouring.
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

    colouring = [-1] * n_nodes
    uncolored = set(range(n_nodes))

    # DSATUR: order nodes by saturation degree (colors used by neighbors)
    while uncolored:
        best_node = None
        best_sat_degree = -1
        best_degree = -1

        for node in uncolored:
            # Saturation degree: distinct colors used by neighbors
            neighbor_colors = set()
            for nb in adj[node]:
                if colouring[nb] != -1:
                    neighbor_colors.add(colouring[nb])
            sat_degree = len(neighbor_colors)

            # Degree in full graph
            degree = len(adj[node])

            # Select by saturation, then by degree
            if sat_degree > best_sat_degree or (sat_degree == best_sat_degree and degree > best_degree):
                best_sat_degree = sat_degree
                best_degree = degree
                best_node = node

        # Assign minimum available color
        neighbor_colors = set()
        for nb in adj[best_node]:
            if colouring[nb] != -1:
                neighbor_colors.add(colouring[nb])

        color = 0
        while color in neighbor_colors:
            color += 1

        colouring[best_node] = color
        uncolored.remove(best_node)

    return colouring
