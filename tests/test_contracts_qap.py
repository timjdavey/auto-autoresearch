"""Tests for scientist/qap/train.py — solver interface contract validation.

Validates that whatever the Scientist has produced in train.py
still satisfies the interface that prepare.py expects.
"""

import unittest

from scientist.qap.prepare import (
    TRAIN_INSTANCES,
    _generate_random_instance,
    validate_assignment,
)


def _get_solve():
    """Import solve fresh to pick up whatever the Scientist wrote."""
    import importlib
    import scientist.qap.train
    importlib.reload(scientist.qap.train)
    return scientist.qap.train.solve


_solve = _get_solve()


class TestSolverContract(unittest.TestCase):
    def test_solve_exists_and_callable(self):
        self.assertTrue(callable(_solve))

    def test_returns_valid_assignment_small(self):
        flow, distance = _generate_random_instance(3, seed=999)
        assignment = _solve(flow, distance)
        self.assertIsNone(validate_assignment(3, assignment))

    def test_returns_valid_assignment_medium(self):
        flow, distance = _generate_random_instance(50, seed=888)
        assignment = _solve(flow, distance)
        self.assertIsNone(validate_assignment(50, assignment))

    def test_returns_valid_assignment_large(self):
        flow, distance = _generate_random_instance(75, seed=777)
        assignment = _solve(flow, distance)
        self.assertIsNone(validate_assignment(75, assignment))

    def test_single_facility(self):
        assignment = _solve([[0]], [[0]])
        self.assertEqual(assignment, [0])

    def test_all_training_instances(self):
        """Smoke test: solver produces valid assignments for all training instances."""
        for name, inst in TRAIN_INSTANCES.items():
            with self.subTest(instance=name):
                assignment = _solve(inst["flow"], inst["distance"])
                n = len(inst["flow"])
                err = validate_assignment(n, assignment)
                self.assertIsNone(err, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
