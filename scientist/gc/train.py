"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR with time-budgeted multi-start and adaptive local search.
The agent should improve this to maximise avg_improvement across all instances.
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

    # --- DSATUR with time-budgeted multi-start and adaptive complexity ---
    start_time = time.time()
    time_budget = 52.0  # Leave 8s margin for safety

    # Determine complexity level based on graph size and density
    use_multistart = n_nodes <= 350
    use_local_search = n_nodes <= 350

    # Determine multi-start runs: increase since time budget is ample
    density = n_edges / (n_nodes * (n_nodes - 1) / 2) if n_nodes > 1 else 0
    if density > 0.3:  # Dense graphs
        num_runs = 4 if use_multistart else 1
        local_search_iters = 40
    else:  # Sparse/medium graphs
        num_runs = 5 if use_multistart else 1
        local_search_iters = 60

    best_colouring = None
    best_colours = float('inf')

    # Multi-start DSATUR with time budgeting
    for run_idx in range(num_runs):
        if time.time() - start_time > time_budget:
            break

        randomize = (run_idx > 0) and use_multistart
        colouring = _dsatur_color(adj, n_nodes, randomize_ties=randomize)

        # Apply 1-opt local search if enabled and time permits
        if use_local_search and time.time() - start_time < time_budget - 3:
            colouring = _one_opt_improve_limited(adj, colouring, n_nodes, max_iterations=local_search_iters)

        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring[:]

    # Try greedy with random ordering as additional diversifier
    if n_nodes > 50 and time.time() - start_time < time_budget - 5:
        for seed_offset in [42, 123]:  # Multiple random seeds
            colouring = _greedy_random_color(adj, n_nodes, seed=seed_offset)
            if use_local_search and time.time() - start_time < time_budget - 3:
                colouring = _one_opt_improve_limited(adj, colouring, n_nodes, max_iterations=40)
            num_colours = max(colouring) + 1 if colouring else 0
            if num_colours < best_colours:
                best_colours = num_colours
                best_colouring = colouring[:]

            if time.time() - start_time > time_budget:
                break

    # Try Welsh-Powell (degree-based) for additional diversity if time permits
    if n_nodes > 50 and time.time() - start_time < time_budget - 4:
        colouring = _welsh_powell_color(adj, n_nodes)
        if use_local_search and time.time() - start_time < time_budget - 2:
            colouring = _one_opt_improve_limited(adj, colouring, n_nodes, max_iterations=35)
        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring[:]

    return best_colouring


def _greedy_random_color(adj: list[list[int]], n_nodes: int, seed: int = 42) -> list[int]:
    """Greedy coloring with random node ordering.

    Provides diversity by exploring a different search direction than DSATUR.
    """
    random.seed(seed)
    nodes = list(range(n_nodes))
    random.shuffle(nodes)

    colouring = [-1] * n_nodes
    for node in nodes:
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _welsh_powell_color(adj: list[list[int]], n_nodes: int) -> list[int]:
    """Welsh-Powell: greedy coloring with nodes ordered by decreasing degree.

    Provides alternative construction to DSATUR for diversity.
    """
    # Sort nodes by degree (descending)
    nodes_by_degree = sorted(range(n_nodes), key=lambda n: len(adj[n]), reverse=True)

    colouring = [-1] * n_nodes
    for node in nodes_by_degree:
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _dsatur_color(adj: list[list[int]], n_nodes: int, randomize_ties: bool = False) -> list[int]:
    """DSATUR algorithm: Dynamic Saturation-based selection.

    Args:
        adj: adjacency list
        n_nodes: number of nodes
        randomize_ties: if True, randomly choose among tied nodes for diversity
    """
    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        # Compute saturation degree for each uncoloured node
        candidates = []  # (saturation, degree, node)

        for node in uncoloured:
            # Saturation degree = number of distinct colors in neighborhood
            saturation = len(set(
                colouring[nb] for nb in adj[node]
                if colouring[nb] != -1
            ))

            # Node degree (for tiebreaker)
            degree = len(adj[node])
            candidates.append((saturation, degree, node))

        # Find best node(s) by saturation and degree
        candidates.sort(reverse=True)
        best_saturation, best_degree, _ = candidates[0]

        # Get all nodes tied for best
        tied_nodes = [node for sat, deg, node in candidates
                      if sat == best_saturation and deg == best_degree]

        # Choose best node: deterministic or randomized selection
        if randomize_ties and len(tied_nodes) > 1:
            best_node = random.choice(tied_nodes)  # Random choice among tied nodes
        else:
            best_node = min(tied_nodes)  # Use min for stable, deterministic tie-breaking

        # Assign smallest available color to best_node
        used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour
        uncoloured.remove(best_node)

    return colouring


def _one_opt_improve(adj: list[list[int]], colouring: list[int], n_nodes: int) -> list[int]:
    """1-opt local search: try to reassign each node to a better color using first-improvement."""
    return _one_opt_improve_limited(adj, colouring, n_nodes, max_iterations=100)


def _one_opt_improve_limited(adj: list[list[int]], colouring: list[int], n_nodes: int, max_iterations: int = 50) -> list[int]:
    """1-opt local search with configurable iteration limit.

    Tries to improve the coloring by reassigning nodes to lower colors.
    Uses first-improvement strategy for efficiency.
    """
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Iterate through nodes; shuffle after first half to add randomness
        nodes = list(range(n_nodes))
        if iterations > max_iterations // 2:
            random.shuffle(nodes)

        for node in nodes:
            current_color = colouring[node]
            if current_color == 0:
                continue

            used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)

            # Try all colors lower than current
            for colour in range(current_color):
                if colour not in used:
                    colouring[node] = colour
                    improved = True
                    break

    return colouring


