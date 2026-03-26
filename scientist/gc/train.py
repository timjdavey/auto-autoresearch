"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR (degree+saturation-based ordering) with
multi-start, 1-opt local search, and greedy post-processing.
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

    num_runs = 120 if n_nodes <= 350 else 70
    best_colouring = None
    best_num_colours = float('inf')

    for run in range(num_runs):
        colouring = dsatur(adj, n_nodes)
        colouring = local_search_1opt(adj, colouring)

        if n_nodes <= 350:
            colouring = local_search_2opt(adj, colouring, max_iterations=50)
            colouring = greedy_highest_color_removal(adj, colouring, max_passes=8)
            # For small graphs, try a perturbation + re-optimize on best solutions
            if run % 20 == 0 and best_colouring:
                perturbed = perturb_colouring(adj, best_colouring[:])
                perturbed = local_search_1opt(adj, perturbed)
                perturbed = local_search_2opt(adj, perturbed, max_iterations=50)
                num_colours_p = max(perturbed) + 1 if perturbed else 0
                if num_colours_p < best_num_colours:
                    colouring = perturbed
        else:
            colouring = local_search_2opt(adj, colouring, max_iterations=8)

        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_num_colours:
            best_num_colours = num_colours
            best_colouring = colouring[:]

    return best_colouring


def dsatur(adj: list[list[int]], n_nodes: int) -> list[int]:
    """DSATUR ordering: greedy colouring with saturation-primary heuristic."""
    colouring = [-1] * n_nodes

    for _ in range(n_nodes):
        candidates = []
        best_sat = -1

        for node in range(n_nodes):
            if colouring[node] != -1:
                continue
            sat = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            if sat > best_sat:
                best_sat = sat
                candidates = [node]
            elif sat == best_sat:
                candidates.append(node)

        if not candidates:
            break

        # Break ties with degree and randomization
        best_node = max(candidates, key=lambda n: (len(adj[n]), random.random()))

        # Assign smallest available colour
        used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour

    return colouring


def local_search_1opt(adj: list[list[int]], colouring: list[int]) -> list[int]:
    """1-opt local search: try recolouring each node to a lower colour."""
    colouring = list(colouring)
    improved = True

    while improved:
        improved = False
        for node in range(len(colouring)):
            used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
            best_colour = colouring[node]

            for colour in range(colouring[node]):
                if colour not in used:
                    best_colour = colour
                    improved = True
                    break

            colouring[node] = best_colour

    return colouring


def local_search_2opt(adj: list[list[int]], colouring: list[int], max_iterations: int = 50) -> list[int]:
    """2-opt local search: try to remove highest colours by reassigning nodes."""
    colouring = list(colouring)
    max_colour = max(colouring) if colouring else 0
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Try to remove the highest color by reassigning those nodes
        for colour_to_remove in range(max_colour, -1, -1):
            nodes_with_colour = [i for i in range(len(colouring)) if colouring[i] == colour_to_remove]

            for node in nodes_with_colour:
                used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
                new_colour = next((c for c in range(colour_to_remove) if c not in used), colour_to_remove)

                if new_colour < colour_to_remove:
                    colouring[node] = new_colour
                    improved = True

        if not improved:
            break

        max_colour = max(colouring)

    return colouring


def greedy_highest_color_removal(adj: list[list[int]], colouring: list[int], max_passes: int = 8) -> list[int]:
    """Greedy post-processing: try to remove highest colours by reassigning nodes."""
    colouring = list(colouring)

    for _ in range(max_passes):
        max_colour = max(colouring) if colouring else 0
        if max_colour == 0:
            break

        nodes_with_max = [i for i in range(len(colouring)) if colouring[i] == max_colour]
        removed_any = False
        newly_assigned = set()

        for node in nodes_with_max:
            used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
            used.update(newly_assigned)  # Avoid conflicts with other nodes reassigned in this pass
            best_colour = None
            for c in range(max_colour):
                if c not in used:
                    best_colour = c
                    break

            if best_colour is not None:
                colouring[node] = best_colour
                newly_assigned.add(best_colour)
                removed_any = True

        if not removed_any:
            break

    return colouring


def perturb_colouring(adj: list[list[int]], colouring: list[int]) -> list[int]:
    """Perturb a colouring by randomly reassigning a few nodes."""
    import random
    colouring = list(colouring)
    n_nodes = len(colouring)
    # Randomly flip 2-4 nodes to random colours to escape local optimum
    num_to_flip = random.randint(2, min(4, n_nodes // 10 + 1))
    for _ in range(num_to_flip):
        node = random.randint(0, n_nodes - 1)
        max_colour = max(colouring) + 1
        colouring[node] = random.randint(0, max_colour)
    return colouring
