"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR + 1-opt local search with adaptive complexity.
"""

import random


def _smallest_last_colouring(adj: list[list[int]], n_nodes: int) -> list[int]:
    """Smallest-Last heuristic: remove nodes with smallest degree first, then colour in reverse."""
    colouring = [-1] * n_nodes
    order = []
    remaining = set(range(n_nodes))
    degrees = [len(adj[i]) for i in range(n_nodes)]

    # Build removal order (smallest degree first)
    while remaining:
        node = min(remaining, key=lambda n: degrees[n])
        order.append(node)
        remaining.remove(node)
        # Update degrees for neighbours
        for neighbour in adj[node]:
            if neighbour in remaining:
                degrees[neighbour] -= 1

    # Colour in reverse order
    for node in reversed(order):
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _rlf_colouring(adj: list[list[int]], n_nodes: int) -> list[int]:
    """RLF (Recursive Large First) heuristic for graph colouring."""
    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        # Step 1: Start a new colour class with the highest-degree uncoloured node
        seed = max(uncoloured, key=lambda n: len([nb for nb in adj[n] if nb in uncoloured]))
        current_colour = max((colouring[i] for i in range(n_nodes) if colouring[i] != -1), default=-1) + 1

        colour_class = {seed}
        colouring[seed] = current_colour
        uncoloured.remove(seed)

        # Step 2: Greedily add nodes to the same colour class that don't conflict
        for node in list(uncoloured):
            # Check if node can be in the same colour class (no edges to colour_class members)
            if all(nb not in colour_class for nb in adj[node]):
                colour_class.add(node)
                colouring[node] = current_colour
                uncoloured.remove(node)

    return colouring


def _dsatur_colouring(adj: list[list[int]], n_nodes: int, with_random_tiebreak: bool = False) -> list[int]:
    """DSATUR heuristic: saturation-primary greedy ordering with optional randomization."""
    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    while uncoloured:
        # Saturation degree: number of distinct colours in neighbours
        max_sat = -1
        candidates = []
        for node in uncoloured:
            sat = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            if sat > max_sat:
                max_sat = sat
                candidates = [node]
            elif sat == max_sat:
                candidates.append(node)

        # Break ties: prefer high degree nodes, optionally random
        if with_random_tiebreak and len(candidates) > 1:
            selected = random.choice(candidates)
        else:
            selected = max(candidates, key=lambda n: len(adj[n]))

        # Colour the selected node
        used = set(colouring[nb] for nb in adj[selected] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[selected] = colour
        uncoloured.remove(selected)

    return colouring


def _one_opt_local_search(adj: list[list[int]], colouring: list[int], max_iterations: int = 1000) -> list[int]:
    """1-opt local search: greedily recolour nodes to minimize max colour."""
    n_nodes = len(colouring)
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        max_colour = max(colouring)

        # Focus on nodes with high colours to reduce overall max
        nodes_by_colour = sorted(range(n_nodes), key=lambda n: colouring[n], reverse=True)

        for node in nodes_by_colour:
            used = set(colouring[nb] for nb in adj[node])
            # Try to recolour to the lowest available colour
            for new_colour in range(max_colour + 1):
                if new_colour not in used:
                    if new_colour < colouring[node]:
                        colouring[node] = new_colour
                        improved = True
                    break
            iterations += 1
            if iterations >= max_iterations:
                break

    return colouring


def _perturbation(adj: list[list[int]], colouring: list[int], perturbation_strength: int = 3) -> list[int]:
    """Perturbation: flip colours of a few random nodes to escape local optima."""
    n_nodes = len(colouring)
    perturbed = colouring[:]

    # Randomly select a few nodes to recolour
    num_to_flip = min(perturbation_strength, max(1, n_nodes // 20))
    nodes_to_flip = random.sample(range(n_nodes), num_to_flip)

    for node in nodes_to_flip:
        # Recolour to a random available colour (or a new colour)
        used = set(perturbed[nb] for nb in adj[node])
        available = [c for c in range(max(perturbed) + 2) if c not in used]
        if available:
            perturbed[node] = random.choice(available)

    return perturbed


def _is_valid_swap(adj: list[list[int]], colouring: list[int], u: int, v: int) -> bool:
    """Check if swapping colours of u and v is valid."""
    # After swap: u gets old colour of v, v gets old colour of u
    u_colour, v_colour = colouring[u], colouring[v]

    # Check u's neighbours: they shouldn't have v_colour except v itself
    for nb in adj[u]:
        if nb != v and colouring[nb] == v_colour:
            return False

    # Check v's neighbours: they shouldn't have u_colour except u itself
    for nb in adj[v]:
        if nb != u and colouring[nb] == u_colour:
            return False

    return True


def _two_opt_swap(adj: list[list[int]], colouring: list[int], max_swaps: int = 500) -> list[int]:
    """2-opt local search: swap colour assignments between pairs of nodes."""
    n_nodes = len(colouring)
    swaps_made = 0

    for u in range(n_nodes):
        for v in range(u + 1, n_nodes):
            if swaps_made >= max_swaps:
                return colouring

            if _is_valid_swap(adj, colouring, u, v):
                colouring[u], colouring[v] = colouring[v], colouring[u]
                swaps_made += 1

    return colouring


def _two_opt_targeted(adj: list[list[int]], colouring: list[int], top_k: int = 50) -> list[int]:
    """2-opt targeting only highest-colour nodes to reduce max colour efficiently."""
    n_nodes = len(colouring)
    max_colour = max(colouring)

    # Only target nodes with colours >= max_colour - 2 (top colours)
    high_colour_nodes = sorted(
        [n for n in range(n_nodes) if colouring[n] >= max_colour - 2],
        key=lambda n: colouring[n],
        reverse=True
    )[:top_k]

    swaps_made = 0
    for u in high_colour_nodes:
        for v in range(n_nodes):
            if u == v:
                continue
            if _is_valid_swap(adj, colouring, u, v):
                colouring[u], colouring[v] = colouring[v], colouring[u]
                swaps_made += 1
                if swaps_made > 20:
                    return colouring

    return colouring


def solve(adj: list[list[int]], n_nodes: int, n_edges: int) -> list[int]:
    """
    Colour a graph using DSATUR + aggressive perturbation + multi-start with RLF.
    Adapts strategy based on graph density for better performance on dense instances.

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

    # Adaptive complexity: for large graphs, reduce iterations to avoid timeout
    use_local_search = n_nodes <= 350
    num_runs = 1 if n_nodes > 350 else 40
    ils_iterations = 0 if n_nodes > 350 else 10

    # Detect graph density and adjust strategy
    # Dense graphs benefit from more perturbation iterations and stronger perturbation
    density = 2 * n_edges / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0
    if density > 0.15:  # Dense graph
        ils_iterations = min(15, ils_iterations + 5)  # Increase ILS iterations
        perturbation_multiplier = 1.3  # Stronger perturbation for dense graphs
    else:
        perturbation_multiplier = 1.0

    best_colouring = None
    best_colours = float('inf')

    # Multiple runs alternating between DSATUR, Smallest-Last, and RLF for diversity
    for run in range(num_runs):
        # Systematic heuristic rotation for consistent diversity
        if run % 5 == 3:
            colouring = _smallest_last_colouring(adj, n_nodes)
        elif run % 5 == 4:
            colouring = _rlf_colouring(adj, n_nodes)
        else:
            colouring = _dsatur_colouring(adj, n_nodes, with_random_tiebreak=(run > 0))

        if use_local_search:
            # Apply 1-opt
            colouring = _one_opt_local_search(adj, colouring, max_iterations=500)

            # Iterated Local Search: aggressive perturbation then refinement
            for ils_iter in range(ils_iterations):
                # First iteration: massive kick to escape local optimum
                if ils_iter == 0:
                    strength = int(n_nodes // 12 * perturbation_multiplier)
                else:
                    strength = max(1, int((4 + (ils_iter // 3)) * perturbation_multiplier))

                perturbed = _perturbation(adj, colouring, perturbation_strength=strength)
                perturbed = _one_opt_local_search(adj, perturbed, max_iterations=200)

                num_colours = max(perturbed) + 1 if perturbed else 0
                if num_colours < max(colouring) + 1:
                    colouring = perturbed

        num_colours = max(colouring) + 1 if colouring else 0
        if num_colours < best_colours:
            best_colours = num_colours
            best_colouring = colouring[:]

    # Final refinement phase: apply 1-opt exhaustively on best solution
    if use_local_search and best_colouring:
        best_colouring = _one_opt_local_search(adj, best_colouring, max_iterations=1000)

    return best_colouring
