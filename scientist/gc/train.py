"""
train.py — Graph colouring solver. THIS IS THE FILE THE AGENT MODIFIES.

Contains a single function `solve(adj, n_nodes, n_edges)` that takes an
adjacency list and returns a colouring as a list of colour assignments.

Current implementation: DSATUR with multi-start and local search.
The agent should improve this to maximise avg_improvement across all instances.
"""

import random
import time
from typing import Optional


def _dsatur_single(adj: list[list[int]], n_nodes: int, seed: Optional[int] = None, use_degree_order: bool = False) -> list[int]:
    """Single DSATUR run with optional randomization and ordering variant."""
    if seed is not None:
        random.seed(seed)

    colouring = [-1] * n_nodes
    uncoloured = set(range(n_nodes))

    # Vary starting node: use random start for diversity
    if random.random() < 0.5:
        # Start with random node
        start_node = random.choice(list(range(n_nodes)))
    else:
        # Start with highest degree node
        start_node = max(range(n_nodes), key=lambda i: len(adj[i]))
    colouring[start_node] = 0
    uncoloured.remove(start_node)

    while uncoloured:
        # For each uncoloured node, compute saturation and degree
        candidates = []
        for node in uncoloured:
            sat = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
            degree = len(adj[node])
            candidates.append((sat, degree, node))

        # Sort by different criteria based on use_degree_order
        if use_degree_order:
            # Degree-first ordering: prioritize degree over saturation
            candidates.sort(key=lambda x: (-x[1], -x[0], random.random()))
        else:
            # Saturation-first ordering (default DSATUR)
            candidates.sort(key=lambda x: (-x[0], -x[1], random.random()))
        best_node = candidates[0][2]

        # Assign colour to best_node
        used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[best_node] = colour
        uncoloured.remove(best_node)

    return colouring


def _random_greedy(adj: list[list[int]], n_nodes: int, seed: Optional[int] = None) -> list[int]:
    """Random greedy colouring: randomize node order, then greedily assign colours."""
    if seed is not None:
        random.seed(seed)

    colouring = [-1] * n_nodes
    nodes = list(range(n_nodes))
    random.shuffle(nodes)

    for node in nodes:
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _lowest_degree_first(adj: list[list[int]], n_nodes: int, seed: Optional[int] = None) -> list[int]:
    """Lowest-degree-first greedy: colour nodes in increasing degree order."""
    if seed is not None:
        random.seed(seed)

    colouring = [-1] * n_nodes
    nodes_by_degree = sorted(range(n_nodes), key=lambda i: len(adj[i]))

    for node in nodes_by_degree:
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _welsh_powell(adj: list[list[int]], n_nodes: int, seed: Optional[int] = None) -> list[int]:
    """Welsh-Powell: colour nodes in decreasing degree order (highest degree first)."""
    if seed is not None:
        random.seed(seed)

    colouring = [-1] * n_nodes
    nodes_by_degree = sorted(range(n_nodes), key=lambda i: -len(adj[i]))

    for node in nodes_by_degree:
        used = set(colouring[nb] for nb in adj[node] if colouring[nb] != -1)
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour

    return colouring


def _count_colours(colouring: list[int]) -> int:
    """Count number of colours used."""
    return max(colouring) + 1 if colouring else 0


def _local_search_1opt(adj: list[list[int]], colouring: list[int], use_2opt: bool = False, time_limit_2opt: float = 5.0) -> list[int]:
    """1-opt local search: try to reassign each node to lower colour if possible.

    Args:
        use_2opt: if True, also apply limited 2-opt after 1-opt
        time_limit_2opt: max time for 2-opt phase (seconds)
    """
    # 1-opt phase
    improved = True
    while improved:
        improved = False
        for node in range(len(colouring)):
            used = set(colouring[nb] for nb in adj[node] if nb != node)
            # Try to find lowest colour not in used
            for colour in range(_count_colours(colouring)):
                if colour not in used:
                    if colour < colouring[node]:
                        colouring[node] = colour
                        improved = True
                        break

    # Optional 2-opt phase for enhanced local search
    if use_2opt:
        colouring = _local_search_2opt(adj, colouring, max_time=time_limit_2opt)

    return colouring


def _local_search_2opt(adj: list[list[int]], colouring: list[int], max_time: Optional[float] = None) -> list[int]:
    """2-opt local search: try to swap colors of pairs of nodes to reduce total colours.

    Args:
        max_time: if provided, hard time limit in seconds for 2-opt execution
    """
    n_nodes = len(colouring)
    improved = True
    start_time = time.time() if max_time else None

    while improved:
        # Check time limit
        if start_time is not None and (time.time() - start_time) > max_time:
            break

        improved = False
        max_colour = _count_colours(colouring) - 1

        # Try swapping colors of pairs of nodes
        for i in range(n_nodes):
            # Check time limit in inner loop too
            if start_time is not None and (time.time() - start_time) > max_time:
                break

            for j in range(i + 1, n_nodes):
                # Check if swap is valid (nodes don't share an edge)
                if j not in adj[i]:
                    old_colour_i = colouring[i]
                    old_colour_j = colouring[j]

                    if old_colour_i != old_colour_j:
                        # Try swapping
                        colouring[i] = old_colour_j
                        colouring[j] = old_colour_i

                        # Check if this reduces total colours
                        new_colour_count = _count_colours(colouring)
                        old_colour_count = max_colour + 1

                        if new_colour_count < old_colour_count:
                            improved = True
                        else:
                            # Swap back if no improvement
                            colouring[i] = old_colour_i
                            colouring[j] = old_colour_j

    return colouring


def _greedy_highest_color_removal(adj: list[list[int]], colouring: list[int]) -> list[int]:
    """Remove nodes using highest colour(s) and reassign them optimally."""
    n_nodes = len(colouring)
    current_colours = _count_colours(colouring)
    max_colour = current_colours - 1

    # Only apply to small/medium graphs for efficiency
    if n_nodes > 350:
        return colouring

    # Try removing the highest colour and reassigning (more rounds for small graphs)
    num_removal_rounds = 4 if n_nodes <= 250 else 2
    for _ in range(num_removal_rounds):
        nodes_with_max = [i for i in range(n_nodes) if colouring[i] == max_colour]
        if not nodes_with_max:
            break

        # Uncolor the nodes with max colour
        for node in nodes_with_max:
            colouring[node] = -1

        # Reassign them with DSATUR
        uncoloured = set(nodes_with_max)
        while uncoloured:
            best_node = None
            best_sat = -1

            for node in uncoloured:
                sat = len(set(colouring[nb] for nb in adj[node] if colouring[nb] != -1))
                if sat > best_sat:
                    best_node = node
                    best_sat = sat

            used = set(colouring[nb] for nb in adj[best_node] if colouring[nb] != -1)
            colour = 0
            while colour in used:
                colour += 1
            colouring[best_node] = colour
            uncoloured.remove(best_node)

        max_colour = _count_colours(colouring) - 1

    return colouring


def _local_search_3opt(adj: list[list[int]], colouring: list[int], max_iterations: int = 10) -> list[int]:
    """3-opt local search: try to reassign 3 nodes together to reduce total colours.

    This targets nodes with high colors to see if reassigning them in groups helps.
    """
    n_nodes = len(colouring)
    best_count = _count_colours(colouring)

    for iteration in range(max_iterations):
        improved = False

        # Focus on nodes with high colors
        nodes_by_color = sorted(range(n_nodes), key=lambda i: -colouring[i])
        top_nodes = nodes_by_color[:min(50, n_nodes)]  # Consider top 50 highest colored nodes

        # Try reassigning triples of nodes
        for i in range(len(top_nodes)):
            for j in range(i + 1, min(i + 15, len(top_nodes))):  # Limit search scope
                for k in range(j + 1, min(j + 15, len(top_nodes))):
                    node_i, node_j, node_k = top_nodes[i], top_nodes[j], top_nodes[k]

                    # Skip if nodes are adjacent (would require same color conflict)
                    if (node_j in adj[node_i] or node_k in adj[node_i] or
                        node_k in adj[node_j]):
                        continue

                    # Try all permutations of color assignments for these 3 nodes
                    old_colors = (colouring[node_i], colouring[node_j], colouring[node_k])

                    for perm_colors in [(old_colors[1], old_colors[2], old_colors[0]),
                                       (old_colors[2], old_colors[0], old_colors[1])]:
                        colouring[node_i] = perm_colors[0]
                        colouring[node_j] = perm_colors[1]
                        colouring[node_k] = perm_colors[2]

                        new_count = _count_colours(colouring)
                        if new_count < best_count:
                            best_count = new_count
                            improved = True
                        else:
                            # Restore original
                            colouring[node_i] = old_colors[0]
                            colouring[node_j] = old_colors[1]
                            colouring[node_k] = old_colors[2]

        if not improved:
            break

    return colouring


def _simulated_annealing(adj: list[list[int]], colouring: list[int], n_nodes: int, max_iterations: int = 100, start_time: Optional[float] = None, time_limit: float = 60.0) -> list[int]:
    """Simulated Annealing: probabilistically accept worse solutions to escape local optima.

    Args:
        start_time: time.time() at start of solve() — used to check remaining budget
        time_limit: total time budget per solve (default 60s)
    """
    best_colouring = colouring[:]
    best_count = _count_colours(best_colouring)
    current_colouring = colouring[:]
    current_count = best_count

    # Temperature schedule: start high, cool down gradually
    initial_temp = 5.0
    final_temp = 0.1
    cooling_rate = (initial_temp - final_temp) / max_iterations

    safety_margin = 1.0

    for iteration in range(max_iterations):
        # Time-aware termination
        if start_time is not None:
            elapsed = time.time() - start_time
            if elapsed > time_limit - safety_margin:
                break

        # Current temperature
        temp = initial_temp - (cooling_rate * iteration)
        if temp < final_temp:
            temp = final_temp

        # Generate neighbor: reassign one random node to a different color
        node = random.randint(0, n_nodes - 1)
        used = set(current_colouring[nb] for nb in adj[node] if current_colouring[nb] != -1)

        # Find valid colors (at least one that's not used by neighbors)
        valid_colours = []
        for c in range(current_count + 1):  # Try current colors + one new color
            if c not in used:
                valid_colours.append(c)

        if not valid_colours:
            continue

        # Pick a random valid color
        new_colour = random.choice(valid_colours)
        old_colour = current_colouring[node]

        if new_colour == old_colour:
            continue

        # Try the move
        current_colouring[node] = new_colour
        new_count = _count_colours(current_colouring)
        delta = new_count - current_count

        # Metropolis acceptance: accept if improves OR with probability e^(-delta/T)
        if delta < 0 or random.random() < pow(2.718, -delta / max(temp, 0.01)):
            # Accept move
            current_count = new_count
            if new_count < best_count:
                best_colouring = current_colouring[:]
                best_count = new_count
        else:
            # Reject move
            current_colouring[node] = old_colour

    return best_colouring


def _iterated_perturbation(adj: list[list[int]], colouring: list[int], n_nodes: int, max_iterations: int = 20, start_time: Optional[float] = None, time_limit: float = 60.0, targeted: bool = False) -> list[int]:
    """Escape local optimum via perturbation and recoloring.

    Args:
        start_time: time.time() at start of solve() — used to check remaining budget
        time_limit: total time budget per solve (default 60s)
        targeted: if True, focus perturbation on high-colored nodes; if False, random perturbation
    """
    best_colouring = colouring[:]
    best_count = _count_colours(best_colouring)
    safety_margin = 1.0  # Reserve 1s for remaining phases

    for iteration in range(max_iterations):
        # Time-aware termination: stop if we're running out of budget
        if start_time is not None:
            elapsed = time.time() - start_time
            if elapsed > time_limit - safety_margin:
                break

        # Choose perturbation strategy based on iteration parity
        if targeted and iteration % 2 == 0:
            # Targeted: prioritize high-colored nodes (10-25% of nodes)
            current_colouring = colouring[:]
            max_colour = _count_colours(current_colouring) - 1
            nodes_by_colour = [(current_colouring[i], i) for i in range(n_nodes)]
            nodes_by_colour.sort(reverse=True)

            # Uncolor top 10-25% of nodes by colour
            perturb_ratio = random.uniform(0.1, 0.25)
            perturb_size = max(1, int(n_nodes * perturb_ratio))
            nodes_to_uncolor = [i for _, i in nodes_by_colour[:perturb_size]]
        else:
            # Random: uncolor a random subset of nodes (10-20% of nodes)
            perturb_size = max(1, n_nodes // random.randint(5, 10))
            nodes_to_uncolor = random.sample(range(n_nodes), perturb_size)
            current_colouring = colouring[:]

        for node in nodes_to_uncolor:
            current_colouring[node] = -1

        # Recolor the uncolored nodes using DSATUR
        uncoloured = set(nodes_to_uncolor)
        while uncoloured:
            best_node = None
            best_sat = -1

            for node in uncoloured:
                sat = len(set(current_colouring[nb] for nb in adj[node] if current_colouring[nb] != -1))
                if sat > best_sat:
                    best_node = node
                    best_sat = sat

            used = set(current_colouring[nb] for nb in adj[best_node] if current_colouring[nb] != -1)
            colour = 0
            while colour in used:
                colour += 1
            current_colouring[best_node] = colour
            uncoloured.remove(best_node)

        # Apply 1-opt to the recolored solution
        current_colouring = _local_search_1opt(adj, current_colouring)

        count = _count_colours(current_colouring)
        if count < best_count:
            best_colouring = current_colouring[:]
            best_count = count

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

    # Multi-start with DSATUR + Welsh-Powell for algorithm diversity
    # Try different algorithm families to escape DSATUR-only basin
    start_total = time.time()
    num_dsatur = 80 if n_nodes <= 350 else 3
    num_wp = 20 if n_nodes <= 350 else 0  # Welsh-Powell runs for diversity
    best_colouring = None
    best_count = float('inf')

    # Main DSATUR runs
    for seed in range(num_dsatur):
        # Alternate between saturation-first (default) and degree-first ordering
        use_degree = (seed % 4 == 0)

        colouring = _dsatur_single(adj, n_nodes, seed=seed, use_degree_order=use_degree)
        # Use 1-opt only (no 2-opt) to save time
        colouring = _local_search_1opt(adj, colouring, use_2opt=False)

        # Reduced perturbation with mixed algorithm runs
        elapsed = time.time() - start_total
        if elapsed > 50:
            perturbation_rounds = 0
        elif elapsed > 40:
            perturbation_rounds = 5
        elif elapsed > 30:
            perturbation_rounds = 8
        else:
            perturbation_rounds = 12

        if perturbation_rounds > 0:
            use_targeted = (seed % 2 == 0)
            colouring = _iterated_perturbation(adj, colouring, n_nodes, max_iterations=perturbation_rounds, start_time=start_total, time_limit=60.0, targeted=use_targeted)

        colouring = _greedy_highest_color_removal(adj, colouring)

        count = _count_colours(colouring)

        if count < best_count:
            best_count = count
            best_colouring = colouring[:]

    # Welsh-Powell runs: different algorithm family for basin escape
    for seed in range(num_wp):
        elapsed = time.time() - start_total
        if elapsed > 52:  # Leave time for wildcard
            break

        colouring = _welsh_powell(adj, n_nodes, seed=seed)
        colouring = _local_search_1opt(adj, colouring, use_2opt=False)

        # Light perturbation for WP runs
        elapsed = time.time() - start_total
        if elapsed <= 45:
            colouring = _iterated_perturbation(adj, colouring, n_nodes, max_iterations=5, start_time=start_total, time_limit=60.0, targeted=False)

        colouring = _greedy_highest_color_removal(adj, colouring)

        count = _count_colours(colouring)

        if count < best_count:
            best_count = count
            best_colouring = colouring[:]


    # Final 3-opt refinement on best solution: try to escape local optimum
    elapsed = time.time() - start_total
    remaining_time = 60.0 - elapsed
    if remaining_time > 2.0 and n_nodes <= 350:
        # Apply 3-opt to high-colored nodes (leave 1s safety margin)
        best_colouring = _local_search_3opt(adj, best_colouring, max_iterations=5)

    return best_colouring
