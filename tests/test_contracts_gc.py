"""Tests for scientist/graph_colouring/train.py — solver interface contract validation.

Validates that whatever the Scientist has produced in train.py
still satisfies the interface that prepare.py expects.
"""

import unittest

from scientist.graph_colouring.prepare import (
    TRAIN_INSTANCES,
    _generate_random_instance,
    validate_colouring,
)


def _get_solve():
    """Import solve fresh to pick up whatever the Scientist wrote."""
    import importlib
    import scientist.graph_colouring.train
    importlib.reload(scientist.graph_colouring.train)
    return scientist.graph_colouring.train.solve


_solve = _get_solve()


class TestSolverContract(unittest.TestCase):
    def test_solve_exists_and_callable(self):
        self.assertTrue(callable(_solve))

    def test_returns_valid_colouring_small(self):
        # Triangle graph
        adj = [[1, 2], [0, 2], [0, 1]]
        colouring = _solve(adj, 3, 3)
        self.assertIsNone(validate_colouring(adj, 3, colouring))

    def test_returns_valid_colouring_medium(self):
        adj, n_nodes, n_edges = _generate_random_instance(50, 0.3, seed=999)
        colouring = _solve(adj, n_nodes, n_edges)
        self.assertIsNone(validate_colouring(adj, n_nodes, colouring))

    def test_returns_valid_colouring_large(self):
        adj, n_nodes, n_edges = _generate_random_instance(200, 0.3, seed=888)
        colouring = _solve(adj, n_nodes, n_edges)
        self.assertIsNone(validate_colouring(adj, n_nodes, colouring))

    def test_single_node(self):
        colouring = _solve([[]], 1, 0)
        self.assertEqual(colouring, [0])

    def test_all_training_instances(self):
        """Smoke test: solver produces valid colourings for all training instances."""
        for name, inst in TRAIN_INSTANCES.items():
            with self.subTest(instance=name):
                colouring = _solve(inst["adj"], inst["n_nodes"], inst["n_edges"])
                err = validate_colouring(inst["adj"], inst["n_nodes"], colouring)
                self.assertIsNone(err, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
