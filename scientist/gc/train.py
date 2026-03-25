"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: greedy colouring with saturation+degree ordering and iterative recolouring.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random


def _colour_greedy(adj: list[list[int]], n_nodes: int, randomize_ties: bool = False) -> list[int]:
    """Greedy coloring with saturation+degree heuristic and recolouring."""
    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        # Select node with highest saturation (then highest degree as tiebreaker)
        candidates = []
        best_saturation = -1

        for node in uncoloured:
            saturation = len(set(
                colouring[neighbour] for neighbour in adj[node]
                if colouring[neighbour] != -1
            ))
            if saturation > best_saturation:
                best_saturation = saturation
                candidates = [node]
            elif saturation == best_saturation:
                candidates.append(node)

        # Among candidates with same saturation, pick by degree (or random if randomize_ties)
        if randomize_ties and len(candidates) > 1:
            node = random.choice(candidates)
        else:
            node = max(candidates, key=lambda n: len(adj[n]))

        uncoloured.remove(node)

        # Find the smallest colour not used by neighbours
        used = set(
            colouring[neighbour] for neighbour in adj[node]
            if colouring[neighbour] != -1
        )
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    # Post-processing: light iterative recolouring to reach local optimum
    if n_nodes > 0:
        improved = True
        passes = 0
        while improved and passes < 5:
            improved = False
            passes += 1
            for vertex in range(n_nodes):
                current_colour = colouring[vertex]
                used = set(
                    colouring[nb] for nb in adj[vertex]
                    if nb != vertex
                )
                for new_colour in range(current_colour):
                    if new_colour not in used:
                        colouring[vertex] = new_colour
                        improved = True
                        break

    return colouring


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

    # Deterministic + 2 randomized restarts, pick the best
    best_colouring = _colour_greedy(adj, n_nodes, randomize_ties=False)
    best_colours = max(best_colouring) + 1 if best_colouring else 0

    for _ in range(2):
        colouring = _colour_greedy(adj, n_nodes, randomize_ties=True)
        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colouring = colouring
            best_colours = num_colours

    return best_colouring
