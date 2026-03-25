"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR with multi-start.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


def _welsh_powell(adj: list[list[int]], n_nodes: int, seed: int = 0) -> list[int]:
    """Welsh-Powell greedy coloring: sort by degree, assign colors greedily."""
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    rng = random.Random(seed)
    # Sort nodes by degree (descending)
    nodes_by_degree = sorted(range(n_nodes), key=lambda i: len(adj[i]), reverse=True)

    colouring = [-1] * n_nodes
    for node in nodes_by_degree:
        used_colors = set()
        for neighbour in adj[node]:
            if colouring[neighbour] != -1:
                used_colors.add(colouring[neighbour])

        color = 0
        while color in used_colors:
            color += 1
        colouring[node] = color

    return colouring


def _dsatur_single(adj: list[list[int]], n_nodes: int, seed: int = 0) -> list[int]:
    """Single DSATUR run with optional randomization in tie-breaking and node ordering."""
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    rng = random.Random(seed)
    colouring = [-1] * n_nodes
    degrees = [len(adj[i]) for i in range(n_nodes)]

    # Randomize initial node ordering for diversity in multistart
    node_order = list(range(n_nodes))
    if seed > 0:
        rng.shuffle(node_order)

    for _ in range(n_nodes):
        best_nodes = []
        best_score = (-1, -1)

        for node in node_order:
            if colouring[node] != -1:
                continue

            used_colors = set()
            for neighbour in adj[node]:
                if colouring[neighbour] != -1:
                    used_colors.add(colouring[neighbour])
            saturation = len(used_colors)
            degree = degrees[node]
            score = (saturation, degree)

            if score > best_score:
                best_score = score
                best_nodes = [node]
            elif score == best_score:
                best_nodes.append(node)

        if not best_nodes:
            break

        best_node = rng.choice(best_nodes)

        used = set()
        for neighbour in adj[best_node]:
            if colouring[neighbour] != -1:
                used.add(colouring[neighbour])

        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour

    return colouring


def _optimize_coloring(adj: list[list[int]], colouring: list[int], n_nodes: int) -> list[int]:
    """Apply 1-opt local search: recolor each node with lowest available color."""
    improved = True
    while improved:
        improved = False

        # Try recoloring each node with its lowest available color
        for node in range(n_nodes):
            neighbors_colors = set(colouring[n] for n in adj[node])
            best_color = 0
            while best_color in neighbors_colors:
                best_color += 1

            if best_color < colouring[node]:
                colouring[node] = best_color
                improved = True
                # Continue checking all nodes in this pass for better recoloring

        # Also try swapping colors between adjacent nodes
        if not improved:
            for node in range(n_nodes):
                for neighbor in adj[node]:
                    if neighbor > node:  # Avoid duplicate pairs
                        color_node = colouring[node]
                        color_neighbor = colouring[neighbor]
                        if color_node == color_neighbor:
                            continue

                        # Try swapping
                        neighbors_colors_node = set(colouring[n] for n in adj[node] if n != neighbor)
                        neighbors_colors_neighbor = set(colouring[n] for n in adj[neighbor] if n != node)

                        # Check if swap is valid
                        if color_neighbor not in neighbors_colors_node and color_node not in neighbors_colors_neighbor:
                            # Swap reduces max color?
                            colouring[node] = color_neighbor
                            colouring[neighbor] = color_node
                            improved = True
                            break

                if improved:
                    break

    return colouring




def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using as few colours as possible.
    Uses multi-start DSATUR + local search optimization.

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

    best_colouring = None
    best_colours = float('inf')

    # Run DSATUR 3 times with different random seeds for better coverage
    for seed in range(3):
        colouring = _dsatur_single(adj, n_nodes, seed)
        # Apply local search optimization once (2-opt is more expensive)
        colouring = _optimize_coloring(adj, colouring, n_nodes)
        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring

    return best_colouring if best_colouring is not None else _dsatur_single(adj, n_nodes, 0)
