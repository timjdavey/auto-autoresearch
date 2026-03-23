import time, sys, random
import numpy as np
sys.path.insert(0, '/Users/timjdavey/Projects/auto2/auto-autoresearch')
from scientist.graph_colouring.prepare import TRAIN_INSTANCES
from scientist.graph_colouring.train import _to_csr, _tabu_core, _tabu_col, _dsatur, _rlf, _greedy_reduce, solve

inst = TRAIN_INSTANCES['rand150a']
adj = inst['adj']
n = inst['n_nodes']

print(f'rand150a: n={n}')

for trial in range(5):
    t = time.time()
    col = solve(adj, n, inst['n_edges'])
    elapsed = time.time() - t
    print(f'  trial {trial}: k={max(col)+1}, time={elapsed:.2f}s')
