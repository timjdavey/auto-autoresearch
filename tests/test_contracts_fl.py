"""Tests for scientist/facloc/train.py — solver interface contract validation.

Validates that whatever the Scientist has produced in train.py
still satisfies the interface that prepare.py expects.
"""

import unittest

from scientist.facloc.prepare import (
    TRAIN_INSTANCES,
    _generate_random_instance,
    validate_assignment,
)


def _get_solve():
    """Import solve fresh to pick up whatever the Scientist wrote."""
    import importlib
    import scientist.facloc.train
    importlib.reload(scientist.facloc.train)
    return scientist.facloc.train.solve


_solve = _get_solve()


class TestSolverContract(unittest.TestCase):
    def test_solve_exists_and_callable(self):
        self.assertTrue(callable(_solve))

    def test_returns_valid_assignment_small(self):
        opening_costs, assign_costs = _generate_random_instance(5, 10, seed=999)
        assignment = _solve(opening_costs, assign_costs)
        self.assertIsNone(validate_assignment(5, 10, assignment))

    def test_returns_valid_assignment_medium(self):
        opening_costs, assign_costs = _generate_random_instance(30, 100, seed=888)
        assignment = _solve(opening_costs, assign_costs)
        self.assertIsNone(validate_assignment(30, 100, assignment))

    def test_returns_valid_assignment_large(self):
        opening_costs, assign_costs = _generate_random_instance(50, 150, seed=777)
        assignment = _solve(opening_costs, assign_costs)
        self.assertIsNone(validate_assignment(50, 150, assignment))

    def test_single_facility(self):
        assignment = _solve([100], [[50, 60, 70]])
        self.assertEqual(assignment, [0, 0, 0])

    def test_all_training_instances(self):
        """Smoke test: solver produces valid assignments for all training instances."""
        for name, inst in TRAIN_INSTANCES.items():
            with self.subTest(instance=name):
                assignment = _solve(inst["opening_costs"], inst["assign_costs"])
                n_fac = len(inst["opening_costs"])
                n_cli = len(inst["assign_costs"][0])
                err = validate_assignment(n_fac, n_cli, assignment)
                self.assertIsNone(err, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
