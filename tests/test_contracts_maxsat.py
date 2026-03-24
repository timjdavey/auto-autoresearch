"""Tests for scientist/maxsat/train.py — solver interface contract validation.

Validates that whatever the Scientist has produced in train.py
still satisfies the interface that prepare.py expects.
"""

import unittest

from scientist.maxsat.prepare import (
    TRAIN_INSTANCES,
    _generate_random_instance,
    validate_assignment,
)


def _get_solve():
    """Import solve fresh to pick up whatever the Scientist wrote."""
    import importlib
    import scientist.maxsat.train
    importlib.reload(scientist.maxsat.train)
    return scientist.maxsat.train.solve


_solve = _get_solve()


class TestSolverContract(unittest.TestCase):
    def test_solve_exists_and_callable(self):
        self.assertTrue(callable(_solve))

    def test_returns_valid_assignment_small(self):
        n_vars, clauses = 3, [[1, 2, 3], [-1, -2, 3]]
        assignment = _solve(n_vars, clauses)
        self.assertIsNone(validate_assignment(n_vars, assignment))

    def test_returns_valid_assignment_medium(self):
        n_vars, clauses = _generate_random_instance(50, 213, seed=999)
        assignment = _solve(n_vars, clauses)
        self.assertIsNone(validate_assignment(n_vars, assignment))

    def test_returns_valid_assignment_large(self):
        n_vars, clauses = _generate_random_instance(200, 854, seed=888)
        assignment = _solve(n_vars, clauses)
        self.assertIsNone(validate_assignment(n_vars, assignment))

    def test_empty(self):
        assignment = _solve(0, [])
        self.assertEqual(assignment, [])

    def test_all_training_instances(self):
        """Smoke test: solver produces valid assignments for all training instances."""
        for name, inst in TRAIN_INSTANCES.items():
            with self.subTest(instance=name):
                assignment = _solve(inst["n_vars"], inst["clauses"])
                err = validate_assignment(inst["n_vars"], assignment)
                self.assertIsNone(err, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
