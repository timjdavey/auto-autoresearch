"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR with multi-start and local search.
"""

import random
import time


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

    def dsatur_coloring(adj, n_nodes, saturation_first=True):
        """DSATUR or degree-first coloring depending on saturation_first flag."""
        colouring = [-1] * n_nodes

        for _ in range(n_nodes):
            candidates = []

            if saturation_first:
                # DSATUR: order by saturation degree
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
            else:
                # Degree-first: order by node degree (uncolored with highest degree)
                best_deg = -1
                for node in range(n_nodes):
                    if colouring[node] != -1:
                        continue
                    deg = len(adj[node])
                    if deg > best_deg:
                        best_deg = deg
                        candidates = [node]
                    elif deg == best_deg:
                        candidates.append(node)

            if not candidates:
                break

            # Break ties with randomization
            best_node = max(candidates, key=lambda n: (len(adj[n]), random.random()))

            # Assign smallest available color
            used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
            colour = 0
            while colour in used:
                colour += 1
            colouring[best_node] = colour

        return colouring

    def one_opt_local_search(colouring, adj, n_nodes):
        """1-opt: try moving each node to a lower color."""
        improved = True
        while improved:
            improved = False
            for node in range(n_nodes):
                used = set(colouring[nb] for nb in adj[node])
                best_colour = colouring[node]

                for colour in range(colouring[node]):
                    if colour not in used:
                        best_colour = colour
                        improved = True
                        break

                colouring[node] = best_colour

        return colouring

    def two_opt_local_search(colouring, adj, n_nodes, max_iterations=80):
        """2-opt: try swapping colors between nodes to reduce total colors."""
        max_colour = max(colouring) if colouring else 0
        improved = True
        iterations = 0

        while improved and iterations < max_iterations:
            improved = False
            iterations += 1

            # Try to remove the highest color by reassigning those nodes
            for colour_to_remove in range(max_colour, -1, -1):
                nodes_with_colour = [i for i in range(n_nodes) if colouring[i] == colour_to_remove]

                for node in nodes_with_colour:
                    used = set(colouring[nb] for nb in adj[node])
                    new_colour = next((c for c in range(colour_to_remove) if c not in used), colour_to_remove)

                    if new_colour < colour_to_remove:
                        colouring[node] = new_colour
                        improved = True

            if not improved:
                break

            max_colour = max(colouring)

        return colouring

    def greedy_highest_color_removal(colouring, adj, n_nodes, max_passes=5):
        """Fast removal of highest colors by reassigning nodes greedily."""
        for _ in range(max_passes):
            max_colour = max(colouring) if colouring else 0
            if max_colour == 0:
                break

            nodes_with_max = [i for i in range(n_nodes) if colouring[i] == max_colour]
            removed_any = False

            for node in nodes_with_max:
                used = set(colouring[nb] for nb in adj[node])
                best_colour = None
                for c in range(max_colour):
                    if c not in used:
                        best_colour = c
                        break

                if best_colour is not None:
                    colouring[node] = best_colour
                    removed_any = True

            if not removed_any:
                break

        return colouring

    # Multi-start DSATUR
    start_time = time.time()
    num_runs = 88 if n_nodes <= 350 else 52
    best_colouring = None
    best_num_colours = float('inf')

    for run_idx in range(num_runs):
        colouring = dsatur_coloring(adj, n_nodes, saturation_first=True)

        # Apply local search
        colouring = one_opt_local_search(colouring, adj, n_nodes)
        if n_nodes <= 350:
            colouring = two_opt_local_search(colouring, adj, n_nodes, max_iterations=50)
            # Aggressive post-processing on small/medium graphs
            colouring = greedy_highest_color_removal(colouring, adj, n_nodes, max_passes=8)
        else:
            colouring = two_opt_local_search(colouring, adj, n_nodes, max_iterations=8)

        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_num_colours:
            best_num_colours = num_colours
            best_colouring = colouring[:]

    elapsed = time.time() - start_time
    print(f"GC: {n_nodes} nodes, {elapsed:.2f}s, {best_num_colours} colours")

    return best_colouring
