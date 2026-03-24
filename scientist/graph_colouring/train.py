"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: greedy colouring with natural vertex ordering (baseline).
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


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

    def dsatur(start_node):
        """Run DSATUR starting from a specific node."""
        colouring = [-1] * n_nodes
        uncolored = set(range(n_nodes))

        colouring[start_node] = 0
        uncolored.remove(start_node)

        while uncolored:
            best_node = None
            best_sat = -1
            best_deg = -1

            for node in uncolored:
                neighbor_colors = set()
                for neighbour in adj[node]:
                    if colouring[neighbour] != -1:
                        neighbor_colors.add(colouring[neighbour])

                sat_degree = len(neighbor_colors)
                degree = len(adj[node])

                if sat_degree > best_sat or (sat_degree == best_sat and degree > best_deg):
                    best_node = node
                    best_sat = sat_degree
                    best_deg = degree

            used = set()
            for neighbour in adj[best_node]:
                if colouring[neighbour] != -1:
                    used.add(colouring[neighbour])
            colour = 0
            while colour in used:
                colour += 1
            colouring[best_node] = colour
            uncolored.remove(best_node)

        return colouring

    def welsh_powell():
        """Greedy coloring with degree-ordered vertices."""
        colouring = [-1] * n_nodes
        # Sort nodes by degree (descending)
        ordered = sorted(range(n_nodes), key=lambda i: len(adj[i]), reverse=True)
        for node in ordered:
            neighbor_colors = set()
            for neighbour in adj[node]:
                if colouring[neighbour] != -1:
                    neighbor_colors.add(colouring[neighbour])
            colour = 0
            while colour in neighbor_colors:
                colour += 1
            colouring[node] = colour
        return colouring

    def reduce_colors(coloring):
        """Iterative color reduction with 1-swap moves."""
        # First: reassign to smallest available color
        changed = True
        passes = 0
        while changed and passes < 3:
            changed = False
            passes += 1
            for node in range(n_nodes):
                neighbor_colors = set()
                for neighbour in adj[node]:
                    neighbor_colors.add(coloring[neighbour])
                colour = 0
                while colour in neighbor_colors:
                    colour += 1
                if coloring[node] != colour:
                    coloring[node] = colour
                    changed = True

        # Second: try 1-swap moves to reduce max color
        improved = True
        while improved:
            improved = False
            max_color = max(coloring) if coloring else 0
            # Try to eliminate the highest color
            for node in range(n_nodes):
                if coloring[node] == max_color:
                    # Try assigning this node to colors 0..max_color-1
                    for target_color in range(max_color):
                        conflict = False
                        for neighbour in adj[node]:
                            if coloring[neighbour] == target_color:
                                conflict = True
                                break
                        if not conflict:
                            coloring[node] = target_color
                            improved = True
                            break

        return coloring


    best_coloring = None
    best_num_colors = float('inf')

    # Try Welsh-Powell first (fast baseline)
    coloring = welsh_powell()
    coloring = reduce_colors(coloring)
    num_colors = max(coloring) + 1 if coloring else 0
    if num_colors < best_num_colors:
        best_num_colors = num_colors
        best_coloring = coloring

    # Try DSATUR with limited multi-start
    sorted_nodes = sorted(range(n_nodes), key=lambda i: len(adj[i]), reverse=True)
    num_high_degree = min(12, n_nodes)
    candidates = sorted_nodes[:num_high_degree]

    # Add some random starting points for diversity
    remaining = [i for i in range(n_nodes) if i not in candidates]
    if remaining:
        random.seed(42)
        num_random = min(12, len(remaining))
        random_candidates = random.sample(remaining, num_random)
        candidates = candidates + random_candidates

    for start_node in candidates:
        coloring = dsatur(start_node)
        coloring = reduce_colors(coloring)
        num_colors = max(coloring) + 1 if coloring else 0
        if num_colors < best_num_colors:
            best_num_colors = num_colors
            best_coloring = coloring

    return best_coloring
