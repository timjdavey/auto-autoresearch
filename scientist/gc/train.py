"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR + 1-opt + Iterated Local Search with perturbations.
The agent should improve this to maximise avg_improvement across all instances.
"""

import time
import random


def _colour_dsatur(adj: list[list[int]], n_nodes: int) -> list[int]:
    """DSATUR with saturation-primary ordering."""
    colouring = [-1] * n_nodes
    uncolored = set(range(n_nodes))

    while uncolored:
        best_node = None
        best_sat = -1
        best_deg = -1

        for node in uncolored:
            sat = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            deg = len(adj[node])

            if sat > best_sat or (sat == best_sat and deg > best_deg):
                best_node = node
                best_sat = sat
                best_deg = deg

        used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour
        uncolored.remove(best_node)

    return colouring


def _local_search_1opt(adj: list[list[int]], colouring: list[int], n_nodes: int) -> list[int]:
    """1-opt local search: move nodes to lower colors."""
    colouring = colouring[:]  # copy
    improved = True

    while improved:
        improved = False
        max_colour = max(colouring) if colouring else 0

        for target_colour in range(max_colour, -1, -1):
            nodes_with_colour = [n for n in range(n_nodes) if colouring[n] == target_colour]

            for node in nodes_with_colour:
                used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
                for new_colour in range(target_colour):
                    if new_colour not in used:
                        colouring[node] = new_colour
                        improved = True
                        break

    # Final targeted pass on highest colors
    while True:
        max_colour = max(colouring)
        max_nodes = [n for n in range(n_nodes) if colouring[n] == max_colour]
        max_nodes.sort(key=lambda n: len(adj[n]))

        found_move = False
        for node in max_nodes:
            used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
            for new_colour in range(max_colour):
                if new_colour not in used:
                    colouring[node] = new_colour
                    found_move = True
                    break
            if found_move:
                break

        if not found_move:
            break

    return colouring


def _perturb(adj: list[list[int]], colouring: list[int], max_colour: int, num_flips: int) -> list[int]:
    """Perturb solution by re-coloring num_flips nodes greedily while maintaining validity."""
    perturbed = colouring[:]
    n = len(colouring)

    nodes_to_recolor = random.sample(range(n), min(num_flips, n))
    for node in nodes_to_recolor:
        # Find forbidden colors
        used = set(perturbed[nb] for nb in adj[node] if perturbed[nb] != -1)
        # Assign smallest valid color (greedy)
        colour = 0
        while colour in used:
            colour += 1
        perturbed[node] = colour

    return perturbed


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

    start_time = time.time()
    time_limit = 50.0  # Leave 10s buffer for safety

    # Initial solution with DSATUR
    best_colouring = _colour_dsatur(adj, n_nodes)
    best_colouring = _local_search_1opt(adj, best_colouring, n_nodes)
    best_colours = max(best_colouring) if best_colouring else 0

    # Iterated local search: perturb and re-optimize
    iteration = 0
    while time.time() - start_time < time_limit:
        iteration += 1

        # Perturbation strength scales with iteration
        num_flips = max(1, n_nodes // (10 + iteration))

        # Perturb
        current = _perturb(adj, best_colouring, best_colours, num_flips)

        # Re-optimize with 1-opt
        current = _local_search_1opt(adj, current, n_nodes)
        current_colours = max(current) if current else 0

        # Accept if better
        if current_colours < best_colours:
            best_colouring = current
            best_colours = current_colours

    return best_colouring
