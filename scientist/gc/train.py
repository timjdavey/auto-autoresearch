"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR (Degree of Saturation) heuristic with
multi-start greedy initialization and 1-opt local search optimization.
"""

import random


def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using DSATUR heuristic with multi-start and local search.

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

    # Try 45 runs for balance between exploration and post-processing
    num_runs = 45

    best_colouring = None
    best_colours = float('inf')

    for _ in range(num_runs):
        # DSATUR: Degree of Saturation heuristic
        colouring = [-1] * n_nodes
        uncoloured = set(range(n_nodes))

        while uncoloured:
            # Calculate saturation degree for each uncoloured vertex
            candidates = []
            max_sat = -1
            max_degree = -1

            for node in uncoloured:
                # Saturation degree: number of different colours used by neighbours
                neighbour_colours = set()
                for neighbour in adj[node]:
                    if colouring[neighbour] != -1:
                        neighbour_colours.add(colouring[neighbour])
                saturation = len(neighbour_colours)

                # Degree: number of neighbours (within uncoloured for tie-breaking)
                degree = sum(1 for n in adj[node] if n in uncoloured)

                # Track best saturation and degree
                if saturation > max_sat or (saturation == max_sat and degree > max_degree):
                    max_sat = saturation
                    max_degree = degree
                    candidates = [node]
                elif saturation == max_sat and degree == max_degree:
                    candidates.append(node)

            # Random tie-breaking among candidates with same saturation and degree
            chosen = random.choice(candidates)

            # Assign smallest available colour to chosen node
            used = set()
            for neighbour in adj[chosen]:
                if colouring[neighbour] != -1:
                    used.add(colouring[neighbour])

            # Find available colours
            available = []
            max_colour = max(colouring) if any(c != -1 for c in colouring) else -1
            for colour in range(max_colour + 2):
                if colour not in used:
                    available.append(colour)

            # Pick smallest available colour (deterministic, good for DSATUR)
            colouring[chosen] = available[0]
            uncoloured.remove(chosen)

        # Post-process: improved 1-opt local search
        # First, recolor vertices with high colors to lower colors
        for target_color in range(max(colouring), 0, -1):
            nodes_with_target = [n for n in range(n_nodes) if colouring[n] == target_color]
            for node in nodes_with_target:
                # Try to recolor this node to a lower color
                for new_color in range(target_color):
                    valid = True
                    for neighbor in adj[node]:
                        if colouring[neighbor] == new_color:
                            valid = False
                            break
                    if valid:
                        colouring[node] = new_color
                        break

        # Second pass: iterative improvement on high-color nodes (greedy local search)
        max_color = max(colouring) if colouring else -1
        for _ in range(min(20, max_color)):  # Optimal: 20 iterations
            improved = False
            for node in range(n_nodes):
                current_color = colouring[node]
                # Try all colors from 0 to current color
                for new_color in range(current_color):
                    valid = all(colouring[n] != new_color for n in adj[node])
                    if valid:
                        colouring[node] = new_color
                        improved = True
                        break
            if not improved:
                break

        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring[:]

    return best_colouring
