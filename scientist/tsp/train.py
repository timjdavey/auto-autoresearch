# train.py - TSP solver: ILS + 2-opt + or-opt(1-5) + Held-Karp for small n
# Adds random-reinsertion LNI as diversification to escape deep local optima

import time
import random
import numpy as np
from numba import njit


@njit(cache=True)
def _held_karp(dist, n):
    INF = 1e18
    size = 1 << n
    dp = np.full((size, n), INF)
    parent = np.full((size, n), -1, dtype=np.int64)
    dp[1][0] = 0.0
    for S in range(1, size):
        if not (S & 1): continue
        for last in range(n):
            if not (S >> last & 1): continue
            if dp[S][last] >= INF: continue
            for nxt in range(n):
                if S >> nxt & 1: continue
                S2 = S | (1 << nxt)
                nc = dp[S][last] + dist[last, nxt]
                if nc < dp[S2][nxt]:
                    dp[S2][nxt] = nc
                    parent[S2][nxt] = last
    full = size - 1
    bl = INF; bl2 = 0
    for i in range(1, n):
        tot = dp[full][i] + dist[i, 0]
        if tot < bl: bl = tot; bl2 = i
    tour = np.empty(n, dtype=np.int64)
    S = full; cur = bl2
    for p in range(n - 1, 0, -1):
        tour[p] = cur
        prev = parent[S][cur]
        S = S ^ (1 << cur)
        cur = prev
    tour[0] = 0
    return tour


@njit(cache=True)
def _nn_tour(dist, n, start):
    visited = np.zeros(n, dtype=np.bool_)
    tour = np.empty(n, dtype=np.int64)
    tour[0] = start; visited[start] = True
    for step in range(1, n):
        cur = tour[step - 1]; best = 0; best_d = 1e18
        for j in range(n):
            if not visited[j] and dist[cur, j] < best_d:
                best_d = dist[cur, j]; best = j
        tour[step] = best; visited[best] = True
    return tour


@njit(cache=True)
def _tour_length(tour, dist, n):
    total = 0.0
    for i in range(n): total += dist[tour[i], tour[(i + 1) % n]]
    return total


@njit(cache=True)
def _build_neighbors(dist, n, k):
    neighbors = np.empty((n, k), dtype=np.int64)
    for i in range(n):
        row = dist[i].copy(); row[i] = 1e18
        sj = np.argsort(row)
        for ki in range(k): neighbors[i, ki] = sj[ki]
    return neighbors


@njit(cache=True)
def _rebuild_pos(tour, pos, n):
    for i in range(n): pos[tour[i]] = i


@njit(cache=True)
def _two_opt_nn(tour, pos, dist, neighbors, n, k):
    _rebuild_pos(tour, pos, n)
    dnl = np.zeros(n, dtype=np.bool_)
    improved = True
    while improved:
        improved = False
        for idx in range(n):
            t1 = tour[idx]
            if dnl[t1]: continue
            t2 = tour[(idx + 1) % n]; d12 = dist[t1, t2]; found = False
            for ki in range(k):
                t3 = neighbors[t1, ki]; d13 = dist[t1, t3]
                if d13 >= d12: break
                j = pos[t3]; t4 = tour[(j + 1) % n]
                if t4 == t1 or t3 == t2: continue
                gain = d12 + dist[t3, t4] - d13 - dist[t2, t4]
                if gain > 1e-10:
                    if idx < j: l, r = idx + 1, j
                    else: l, r = j + 1, idx
                    while l < r:
                        pos[tour[l]] = r; pos[tour[r]] = l
                        tour[l], tour[r] = tour[r], tour[l]; l += 1; r -= 1
                    if l == r: pos[tour[l]] = l
                    dnl[t1] = False; dnl[t2] = False; dnl[t3] = False; dnl[t4] = False
                    improved = True; found = True
                    t2 = tour[(idx + 1) % n]; d12 = dist[t1, t2]; break
            if not found: dnl[t1] = True
    return tour


@njit(cache=True)
def _or_opt_nn(tour, pos, dist, neighbors, n, k, seg_size):
    dnl = np.zeros(n, dtype=np.bool_)
    improved = True
    while improved:
        improved = False
        for i in range(n - seg_size + 1):
            first = tour[i]
            if dnl[first]: continue
            last = tour[i + seg_size - 1]
            p_idx = (i - 1 + n) % n; p = tour[p_idx]; q = tour[(i + seg_size) % n]
            rg = dist[p, first] + dist[last, q] - dist[p, q]
            bg = 1e-10; bj = -1; br = False
            for ki in range(k):
                u = neighbors[first, ki]; j = pos[u]
                if j == p_idx: continue
                if i <= j < i + seg_size: continue
                v = tour[(j + 1) % n]; base = dist[u, v]
                cf = dist[u, first] + dist[last, v] - base
                if rg - cf > bg: bg = rg - cf; bj = j; br = False
                if seg_size > 1:
                    cr = dist[u, last] + dist[first, v] - base
                    if rg - cr > bg: bg = rg - cr; bj = j; br = True
            if seg_size > 1:
                for ki in range(k):
                    u = neighbors[last, ki]; j = pos[u]
                    if j == p_idx: continue
                    if i <= j < i + seg_size: continue
                    v = tour[(j + 1) % n]; base = dist[u, v]
                    cf = dist[u, first] + dist[last, v] - base
                    if rg - cf > bg: bg = rg - cf; bj = j; br = False
                    cr = dist[u, last] + dist[first, v] - base
                    if rg - cr > bg: bg = rg - cr; bj = j; br = True
            if bj >= 0:
                uc = tour[bj]; vc = tour[(bj + 1) % n]
                dnl[p] = False; dnl[first] = False; dnl[last] = False
                dnl[q] = False; dnl[uc] = False; dnl[vc] = False
                seg = tour[i:i + seg_size].copy()
                if br:
                    for ki in range(seg_size // 2):
                        seg[ki], seg[seg_size - 1 - ki] = seg[seg_size - 1 - ki], seg[ki]
                rest = np.empty(n - seg_size, dtype=np.int64); ri = 0
                for idx2 in range(n):
                    if idx2 < i or idx2 >= i + seg_size: rest[ri] = tour[idx2]; ri += 1
                ins = bj if bj < i else bj - seg_size
                nt = np.empty(n, dtype=np.int64)
                for idx2 in range(ins + 1): nt[idx2] = rest[idx2]
                for idx2 in range(seg_size): nt[ins + 1 + idx2] = seg[idx2]
                for idx2 in range(ins + 1, n - seg_size): nt[idx2 + seg_size] = rest[idx2]
                tour = nt; _rebuild_pos(tour, pos, n); improved = True; break
            else: dnl[first] = True
    return tour


@njit(cache=True)
def _local_search_nn(tour, pos, dist, neighbors, n, k):
    prev = _tour_length(tour, dist, n)
    while True:
        tour = _two_opt_nn(tour, pos, dist, neighbors, n, k)
        tour = _or_opt_nn(tour, pos, dist, neighbors, n, k, 1)
        tour = _or_opt_nn(tour, pos, dist, neighbors, n, k, 2)
        tour = _or_opt_nn(tour, pos, dist, neighbors, n, k, 3)
        tour = _or_opt_nn(tour, pos, dist, neighbors, n, k, 4)
        tour = _or_opt_nn(tour, pos, dist, neighbors, n, k, 5)
        nlen = _tour_length(tour, dist, n)
        if nlen >= prev - 1e-10: break
        prev = nlen
    return tour


def _warmup():
    n = 10
    pts = np.array([[0.,0.],[1.,0.],[2.,0.],[3.,0.],[3.,1.],
                    [3.,2.],[2.,2.],[1.,2.],[0.,2.],[0.,1.]],dtype=np.float64)
    dx = pts[:,0].reshape(-1,1)-pts[:,0].reshape(1,-1)
    dy = pts[:,1].reshape(-1,1)-pts[:,1].reshape(1,-1)
    dist = np.sqrt(dx*dx+dy*dy); k = min(5, n-1)
    neighbors = _build_neighbors(dist, n, k)
    t = _nn_tour(dist, n, 0); pos = np.zeros(n, dtype=np.int64)
    t = _local_search_nn(t, pos, dist, neighbors, n, k)
    _held_karp(dist, n)


_warmup()


def _lni_perturb(tour, dist, k):
    """Large neighborhood: remove k random cities, reinsert greedily in random order."""
    n = len(tour)
    remove_idx = sorted(random.sample(range(n), k))
    removed = [tour[i] for i in remove_idx]
    partial = [tour[i] for i in range(n) if i not in set(remove_idx)]
    random.shuffle(removed)
    for city in removed:
        best_cost = float('inf')
        best_pos = 1
        m = len(partial)
        for i in range(m):
            j = (i + 1) % m
            cost = dist[partial[i], city] + dist[city, partial[j]] - dist[partial[i], partial[j]]
            if cost < best_cost:
                best_cost = cost
                best_pos = i + 1
        partial.insert(best_pos, city)
    return np.array(partial, dtype=np.int64)


def _lni_random_perturb(tour, k):
    """Remove k random cities, reinsert at random positions — maximally diverse."""
    n = len(tour)
    remove_idx = sorted(random.sample(range(n), k))
    removed = [tour[i] for i in remove_idx]
    partial = [tour[i] for i in range(n) if i not in set(remove_idx)]
    random.shuffle(removed)
    for city in removed:
        pos_ins = random.randint(0, len(partial))
        partial.insert(pos_ins, city)
    return np.array(partial, dtype=np.int64)


def solve(coords):
    n = len(coords)
    if n == 0: return []
    if n == 1: return [0]
    if n == 2: return [0, 1]
    if n == 3: return [0, 1, 2]
    pts = np.array(coords, dtype=np.float64)
    dx = pts[:,0].reshape(-1,1)-pts[:,0].reshape(1,-1)
    dy = pts[:,1].reshape(-1,1)-pts[:,1].reshape(1,-1)
    dist = np.sqrt(dx*dx+dy*dy)
    if n <= 20:
        return _held_karp(dist, n).tolist()
    # Adaptive k: fewer neighbors for large n → faster iterations → more ILS rounds
    if n < 300: k = min(20, n-1)
    elif n < 500: k = min(15, n-1)
    elif n < 700: k = min(12, n-1)
    else: k = min(8, n-1)
    neighbors = _build_neighbors(dist, n, k)
    pos = np.zeros(n, dtype=np.int64)
    deadline = time.perf_counter() + 55.0

    # Phase 1: multi-start NN
    p1e = time.perf_counter() + min(8.0, 55.0 * 0.15)
    best_tour = _nn_tour(dist, n, 0)
    best_tour = _local_search_nn(best_tour, pos, dist, neighbors, n, k)
    best_len = _tour_length(best_tour, dist, n)
    for s in range(1, n):
        if time.perf_counter() > p1e: break
        t = _nn_tour(dist, n, s); _rebuild_pos(t, pos, n)
        t = _two_opt_nn(t, pos, dist, neighbors, n, k)
        tl = _tour_length(t, dist, n)
        if tl < best_len:
            t = _local_search_nn(t, pos, dist, neighbors, n, k)
            tl = _tour_length(t, dist, n)
            if tl < best_len: best_len = tl; best_tour = t.copy()

    # Phase 2: ILS with three alternating perturbations:
    # double-bridge, greedy LNI, random LNI (most diverse)
    stag = max(15, n // 4); current = best_tour.copy(); cur_len = best_len
    no_imp = 0; nn_s = 1; restart_count = 0; perturb_mode = 0
    k_lni_small = max(8, n // 8)
    k_lni_large = max(15, n // 5)
    k_lni_rand = max(20, n // 4)   # larger removal for random reinsert

    while time.perf_counter() < deadline - 1.0:
        if perturb_mode == 0:
            # True double-bridge 4-opt: A+D+C+B (all 4 junctions change)
            pl = sorted(random.sample(range(1, n), 3)); p1, p2, p3 = pl
            cand = np.concatenate([current[:p1], current[p3:], current[p2:p3], current[p1:p2]])
        elif perturb_mode == 1:
            # Greedy LNI
            k_use = k_lni_large if (no_imp > stag // 2) else k_lni_small
            cand = _lni_perturb(current, dist, k_use)
        else:
            # Random reinsertion LNI — maximally diverse, escapes deep basins
            cand = _lni_random_perturb(current, k_lni_rand)
        perturb_mode = (perturb_mode + 1) % 3

        cand = _local_search_nn(cand, pos, dist, neighbors, n, k)
        clen = _tour_length(cand, dist, n)
        if clen < cur_len - 1e-10:
            current = cand.copy(); cur_len = clen; no_imp = 0
            if clen < best_len - 1e-10: best_len = clen; best_tour = cand.copy()
        else:
            no_imp += 1

        if no_imp >= stag:
            if restart_count % 3 == 0:
                t = _nn_tour(dist, n, nn_s % n); nn_s += 1
            elif restart_count % 3 == 1:
                perm = list(range(n)); random.shuffle(perm)
                t = np.array(perm, dtype=np.int64)
            else:
                # Large random LNI restart for maximum diversity
                t = _lni_random_perturb(best_tour, min(n // 2, 60))
            t = _local_search_nn(t, pos, dist, neighbors, n, k)
            tl = _tour_length(t, dist, n)
            if tl < best_len: best_len = tl; best_tour = t.copy()
            current = t.copy(); cur_len = tl; no_imp = 0; restart_count += 1

    return best_tour.tolist()
