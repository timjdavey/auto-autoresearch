"""Tests for scientist/train.py — solver interface contract validation.

Validates that whatever the Scientist has produced in scientist/train.py
still satisfies the interface that prepare.py expects. Useful as a
pre-study sanity check or CI gate.
"""

import unittest

from scientist.tsp.prepare import TRAIN_INSTANCES, _generate_random_instance, validate_tour


def _get_solve():
    """Import solve fresh to pick up whatever the Scientist wrote."""
    import importlib
    import scientist.tsp.train
    importlib.reload(scientist.tsp.train)
    return scientist.tsp.train.solve


_solve = _get_solve()


class TestSolverContract(unittest.TestCase):
    def test_solve_exists_and_callable(self):
        self.assertTrue(callable(_solve))

    def test_returns_valid_tour_small(self):
        coords = [(0, 0), (1, 0), (0, 1)]
        tour = _solve(coords)
        self.assertIsNone(validate_tour(coords, tour))

    def test_returns_valid_tour_medium(self):
        coords = _generate_random_instance(50, seed=999)
        tour = _solve(coords)
        self.assertIsNone(validate_tour(coords, tour))

    def test_returns_valid_tour_large(self):
        coords = _generate_random_instance(200, seed=888)
        tour = _solve(coords)
        self.assertIsNone(validate_tour(coords, tour))

    def test_single_city(self):
        tour = _solve([(5, 5)])
        self.assertEqual(tour, [0])

    def test_all_training_instances(self):
        """Smoke test: solver produces valid tours for all 20 training instances."""
        for name, inst in TRAIN_INSTANCES.items():
            with self.subTest(instance=name):
                tour = _solve(inst["coords"])
                err = validate_tour(inst["coords"], tour)
                self.assertIsNone(err, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
