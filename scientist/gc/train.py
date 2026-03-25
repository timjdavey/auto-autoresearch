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


def _random_greedy(adj: list[list[int]], n_nodes: int, seed: int = 0) -> list[int]:
    """Random greedy coloring: shuffle node order, assign colors greedily."""
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    rng = random.Random(seed)
    node_order = list(range(n_nodes))
    rng.shuffle(node_order)

    colouring = [-1] * n_nodes
    for node in node_order:
        used_colors = set()
        for neighbour in adj[node]:
            if colouring[neighbour] != -1:
                used_colors.add(colouring[neighbour])

        color = 0
        while color in used_colors:
            color += 1
        colouring[node] = color

    return colouring


def _anti_dsatur(adj: list[list[int]], n_nodes: int, seed: int = 0) -> list[int]:
    """Anti-DSATUR: prioritize LOW saturation + HIGH degree (explore different basin)."""
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    rng = random.Random(seed)
    colouring = [-1] * n_nodes
    degrees = [len(adj[i]) for i in range(n_nodes)]

    for _ in range(n_nodes):
        best_nodes = []
        best_score = (float('inf'), -1)  # Minimize saturation, maximize degree for tiebreak

        for node in range(n_nodes):
            if colouring[node] != -1:
                continue

            used_colors = set()
            for neighbour in adj[node]:
                if colouring[neighbour] != -1:
                    used_colors.add(colouring[neighbour])
            saturation = len(used_colors)
            degree = -degrees[node]  # Negate to maximize degree in tuple comparison
            score = (saturation, degree)

            if score < best_score:  # Minimize saturation, then maximize degree
                best_score = score
                best_nodes = [node]
            elif score == best_score:
                best_nodes.append(node)

        if not best_nodes:
            break

        best_node = rng.choice(best_nodes) if len(best_nodes) > 1 else best_nodes[0]

        used = set()
        for neighbour in adj[best_node]:
            if colouring[neighbour] != -1:
                used.add(colouring[neighbour])

        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour

    return colouring


def _dsatur_single(adj: list[list[int]], n_nodes: int, seed: int = 0) -> list[int]:
    """Single DSATUR run with random tie-breaking for diversity."""
    if n_nodes == 0:
        return []
    if n_nodes == 1:
        return [0]

    rng = random.Random(seed)
    colouring = [-1] * n_nodes
    degrees = [len(adj[i]) for i in range(n_nodes)]

    for _ in range(n_nodes):
        best_nodes = []
        best_score = (-1, -1)

        for node in range(n_nodes):
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

        # Random tie-breaking for diversity
        best_node = rng.choice(best_nodes) if len(best_nodes) > 1 else best_nodes[0]

        used = set()
        for neighbour in adj[best_node]:
            if colouring[neighbour] != -1:
                used.add(colouring[neighbour])

        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour

    return colouring


def _optimize_coloring(adj: list[list[int]], colouring: list[int], n_nodes: int, seed: int = 0) -> list[int]:
    """Apply iterative 1-opt + color merging to reduce chromatic number."""
    max_passes = 20
    for _ in range(max_passes):
        improved = False
        for node in range(n_nodes):
            neighbors_colors = set(colouring[n] for n in adj[node])
            best_color = 0
            while best_color in neighbors_colors:
                best_color += 1
            if best_color < colouring[node]:
                colouring[node] = best_color
                improved = True
        if not improved:
            break

    # Color merging: try to merge colors if no conflict
    max_color = max(colouring) if colouring else 0
    for color_to_merge in range(max_color, 0, -1):
        # Find nodes with color_to_merge
        nodes_with_color = [i for i in range(n_nodes) if colouring[i] == color_to_merge]
        if not nodes_with_color:
            continue

        # Try to merge into lowest possible color
        for target_color in range(color_to_merge):
            can_merge = True
            for node in nodes_with_color:
                if target_color in set(colouring[n] for n in adj[node]):
                    can_merge = False
                    break
            if can_merge:
                for node in nodes_with_color:
                    colouring[node] = target_color
                break

    return colouring


def _perturb_and_recolor(adj: list[list[int]], colouring: list[int], n_nodes: int, perturbation_rate: float, seed: int) -> list[int]:
    """
    Perturbation for ILS: randomly uncolor nodes, then recolor with greedy.

    Args:
        perturbation_rate: fraction of nodes to uncolor (e.g., 0.1 for 10%)
    """
    rng = random.Random(seed)
    perturbed = colouring.copy()
    num_to_uncolor = max(1, int(n_nodes * perturbation_rate))
    nodes_to_uncolor = rng.sample(range(n_nodes), num_to_uncolor)

    for node in nodes_to_uncolor:
        perturbed[node] = -1

    # Greedily recolor uncolored nodes
    for node in range(n_nodes):
        if perturbed[node] == -1:
            used_colors = set()
            for neighbor in adj[node]:
                if perturbed[neighbor] != -1:
                    used_colors.add(perturbed[neighbor])
            color = 0
            while color in used_colors:
                color += 1
            perturbed[node] = color

    return perturbed




def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using as few colours as possible.
    Uses multi-strategy approach: DSATUR, Anti-DSATUR, Welsh-Powell with ILS refinement.

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

    # Strategy 1: DSATUR (high saturation first)
    for seed in range(3):
        colouring = _dsatur_single(adj, n_nodes, seed)
        colouring = _optimize_coloring(adj, colouring, n_nodes, seed)
        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring

    # Strategy 2: Anti-DSATUR (low saturation first) — different basin
    if n_nodes <= 350:
        for seed in range(3):
            colouring = _anti_dsatur(adj, n_nodes, seed)
            colouring = _optimize_coloring(adj, colouring, n_nodes, seed + 10)
            num_colours = max(colouring) + 1 if colouring else 0
            if num_colours < best_colours:
                best_colours = num_colours
                best_colouring = colouring

    # Strategy 3: Welsh-Powell (degree-based ordering)
    if n_nodes <= 350:
        colouring = _welsh_powell(adj, n_nodes)
        colouring = _optimize_coloring(adj, colouring, n_nodes, seed=100)
        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring

    # Strategy 4: Iterated Local Search (ILS) on DSATUR
    # Start with best initial solution, perturb and re-optimize to escape local optima
    if best_colouring is not None and n_nodes <= 350:
        ils_solution = best_colouring.copy()
        for ils_iteration in range(5):
            # Perturb: randomly uncolor 10% of nodes for aggressive diversification
            perturbed = _perturb_and_recolor(adj, ils_solution, n_nodes, perturbation_rate=0.10, seed=200 + ils_iteration)
            # Re-optimize
            perturbed = _optimize_coloring(adj, perturbed, n_nodes, seed=300 + ils_iteration)
            num_colours = max(perturbed) + 1 if perturbed else 0
            # Accept if better
            if num_colours < best_colours:
                best_colours = num_colours
                best_colouring = perturbed
                ils_solution = perturbed

    return best_colouring if best_colouring is not None else _dsatur_single(adj, n_nodes, 0)
