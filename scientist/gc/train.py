"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR with first-improvement 1-opt local search
and time budget tracking to ensure completion within 60s.
"""

import random
import time


def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using DSATUR with first-improvement 1-opt local search.

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

    start_time = time.time()
    time_limit = 55.0  # Leave 5s margin for cleanup

    # Initialize with DSATUR + local search
    colouring = _dsatur_randomized(adj, n_nodes, use_random_tiebreak=False)
    colouring = _one_opt_first_improvement(adj, colouring, n_nodes, start_time, time_limit)
    colouring = _greedy_colour_reduce(adj, colouring, n_nodes, start_time, time_limit)
    best_colouring = colouring
    best_count = max(colouring) + 1

    # Try one randomized restart if graph is small enough and time permits
    if n_nodes <= 350 and time.time() - start_time < time_limit * 0.7:
        colouring = _dsatur_randomized(adj, n_nodes, use_random_tiebreak=True)
        colouring = _one_opt_first_improvement(adj, colouring, n_nodes, start_time, time_limit)
        colouring = _greedy_colour_reduce(adj, colouring, n_nodes, start_time, time_limit)

        colour_count = max(colouring) + 1
        if colour_count < best_count:
            best_count = colour_count
            best_colouring = colouring

    return best_colouring

def _dsatur_randomized(adj: list[list[int]], n_nodes: int, use_random_tiebreak: bool = False) -> list[int]:
    """DSATUR algorithm with optional randomized tie-breaking."""
    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        # For each uncoloured node, compute saturation degree (num distinct colors in neighbors)
        candidates = []
        max_saturation = -1

        for node in uncoloured:
            saturation = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            degree = len(adj[node])

            if saturation > max_saturation:
                max_saturation = saturation
                candidates = [(node, degree)]
            elif saturation == max_saturation:
                candidates.append((node, degree))

        # Break ties
        if use_random_tiebreak and len(candidates) > 1:
            next_node = random.choice(candidates)[0]
        else:
            # Deterministic: choose node with highest degree among saturation ties
            next_node = max(candidates, key=lambda x: x[1])[0]

        # Color next_node with smallest available color
        used = set(colouring[nb] for nb in adj[next_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[next_node] = colour
        uncoloured.remove(next_node)

    return colouring


def _one_opt_first_improvement(adj: list[list[int]], colouring: list[int], n_nodes: int, start_time: float, time_limit: float) -> list[int]:
    """1-opt local search: recolor each node with the best valid color."""
    colouring = list(colouring)
    improved = True
    max_iterations = n_nodes * 2
    check_time_every = max(1, n_nodes // 10)  # Check time every 10% of nodes

    iteration = 0
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # Check time budget periodically to avoid overhead
        if iteration % check_time_every == 0 and time.time() - start_time > time_limit:
            break

        for node in range(n_nodes):
            used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
            # Find the lowest color not used by neighbors (always valid)
            best_colour = 0
            while best_colour in used:
                best_colour += 1
            # Recolor if current color is invalid, or if we find a better color
            if colouring[node] in used or best_colour < colouring[node]:
                colouring[node] = best_colour
                improved = True

    return colouring


def _greedy_colour_reduce(adj: list[list[int]], colouring: list[int], n_nodes: int, start_time: float, time_limit: float) -> list[int]:
    """Try to reduce total colours by reassigning high-colour nodes to lower colours."""
    colouring = list(colouring)
    max_colour = max(colouring)
    improved = True
    iterations = 0
    max_iterations = 5

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Check time budget
        if time.time() - start_time > time_limit:
            break

        # Try to reassign nodes with highest colours to lower colours
        for target_colour in range(max_colour, 0, -1):
            nodes_with_colour = [node for node in range(n_nodes) if colouring[node] == target_colour]

            for node in nodes_with_colour:
                used_by_neighbors = set(colouring[nb] for nb in adj[node])

                # Try to find a lower valid colour for this node
                for new_colour in range(target_colour):
                    if new_colour not in used_by_neighbors:
                        colouring[node] = new_colour
                        improved = True
                        break

        max_colour = max(colouring)

    return colouring


