"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR (5 seeds) + 1-opt local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


def _dsatur_single(adj: list[list[int]], n_nodes: int, seed: int = None) -> list[int]:
    """Single DSATUR run with optional seed."""
    if seed is not None:
        random.seed(seed)

    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        max_saturation = -1
        best_node = None

        for node in uncoloured:
            saturation = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            if saturation > max_saturation or (
                saturation == max_saturation and (best_node is None or len(adj[node]) > len(adj[best_node]))
            ):
                max_saturation = saturation
                best_node = node

        if best_node is None:
            best_node = uncoloured.pop()
        else:
            uncoloured.remove(best_node)

        used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour

    return colouring


def _count_colours(colouring: list[int]) -> int:
    """Count number of colours used."""
    if not colouring:
        return 0
    return max(colouring) + 1


def _one_opt_local_search(adj: list[list[int]], colouring: list[int], n_nodes: int) -> list[int]:
    """Apply 1-opt local search: reassign each node to best colour."""
    improved = True
    while improved:
        improved = False
        for node in range(n_nodes):
            neighbour_colours = set(colouring[nb] for nb in adj[node])
            current_colour = colouring[node]

            colour = 0
            while colour in neighbour_colours:
                colour += 1

            if colour < current_colour:
                colouring[node] = colour
                improved = True

    return colouring


def _iterated_perturbation(adj: list[list[int]], colouring: list[int], n_nodes: int) -> list[int]:
    """Apply iterated perturbation to escape local optima."""
    best_colouring = colouring.copy()
    best_colours = _count_colours(best_colouring)

    # Iteration count
    num_iterations = 30 if n_nodes <= 350 else 8

    for _ in range(num_iterations):
        # Randomly uncolor 10-20% of nodes
        uncolor_count = max(1, n_nodes // random.randint(5, 10))
        nodes_to_uncolor = random.sample(range(n_nodes), uncolor_count)

        perturbed = best_colouring.copy()
        for node in nodes_to_uncolor:
            perturbed[node] = -1

        # Recolor using DSATUR
        uncoloured = set(node for node in range(n_nodes) if perturbed[node] == -1)
        while uncoloured:
            max_saturation = -1
            best_node = None

            for node in uncoloured:
                saturation = len(set(perturbed[nb] for nb in adj[node] if perturbed[nb] != -1))
                if saturation > max_saturation or (
                    saturation == max_saturation and (best_node is None or len(adj[node]) > len(adj[best_node]))
                ):
                    max_saturation = saturation
                    best_node = node

            if best_node is None:
                best_node = uncoloured.pop()
            else:
                uncoloured.remove(best_node)

            used = set(perturbed[nb] for nb in adj[best_node] if perturbed[nb] != -1)
            colour = 0
            while colour in used:
                colour += 1
            perturbed[best_node] = colour

        # Apply 1-opt local search
        perturbed = _one_opt_local_search(adj, perturbed, n_nodes)

        # Keep if better
        num_colours = _count_colours(perturbed)
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = perturbed

    return best_colouring


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

    best_colouring = None
    best_colours = float('inf')

    # Multi-start DSATUR: run multiple times with different seeds, keep best
    # Increased seeds for better initial solution
    for seed in [1, 42, 123, 456, 789, 999, 2024, 555, 777, 888]:
        colouring = _dsatur_single(adj, n_nodes, seed)
        num_colours = _count_colours(colouring)
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring

    # Apply 1-opt local search
    best_colouring = _one_opt_local_search(adj, best_colouring, n_nodes)

    # Apply iterated perturbation to escape local optima
    best_colouring = _iterated_perturbation(adj, best_colouring, n_nodes)

    return best_colouring
