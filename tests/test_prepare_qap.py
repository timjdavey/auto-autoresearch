"""Tests for prepare.py — QAP evaluation harness."""

import unittest

import scientist.qap.prepare as prepare
from scientist.qap.prepare import (
    IDENTITY_BASELINES,
    TIME_BUDGET,
    TRAIN_INSTANCES,
    _identity_cost,
    _run_solver,
    assignment_cost,
    evaluate,
    validate_assignment,
)


# ---------------------------------------------------------------------------
# assignment_cost
# ---------------------------------------------------------------------------

class TestAssignmentCost(unittest.TestCase):
    def test_identity_2x2(self):
        flow = [[0, 5], [5, 0]]
        distance = [[0, 3], [3, 0]]
        # identity: cost = 5*3 + 5*3 = 30
        self.assertEqual(assignment_cost(flow, distance, [0, 1]), 30)

    def test_swap_2x2(self):
        flow = [[0, 5], [5, 0]]
        distance = [[0, 3], [3, 0]]
        # swap: cost = 5*3 + 5*3 = 30 (symmetric case)
        self.assertEqual(assignment_cost(flow, distance, [1, 0]), 30)

    def test_asymmetric_3x3(self):
        flow = [[0, 1, 0], [1, 0, 0], [0, 0, 0]]
        distance = [[0, 10, 20], [10, 0, 30], [20, 30, 0]]
        # identity: flow[0][1]*dist[0][1] + flow[1][0]*dist[1][0] = 1*10 + 1*10 = 20
        self.assertEqual(assignment_cost(flow, distance, [0, 1, 2]), 20)
        # swap 0,1: flow[0][1]*dist[1][0] + flow[1][0]*dist[0][1] = 1*10 + 1*10 = 20
        self.assertEqual(assignment_cost(flow, distance, [1, 0, 2]), 20)


# ---------------------------------------------------------------------------
# validate_assignment
# ---------------------------------------------------------------------------

class TestValidateAssignment(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_assignment(3, [2, 0, 1]))

    def test_wrong_length(self):
        err = validate_assignment(2, [0])
        self.assertIn("1", err)
        self.assertIn("2", err)

    def test_not_a_list(self):
        err = validate_assignment(1, (0,))
        self.assertIn("list", err)

    def test_duplicate_locations(self):
        err = validate_assignment(2, [0, 0])
        self.assertIsNotNone(err)

    def test_out_of_range(self):
        err = validate_assignment(2, [0, 5])
        self.assertIsNotNone(err)


# ---------------------------------------------------------------------------
# _identity_cost
# ---------------------------------------------------------------------------

class TestIdentityCost(unittest.TestCase):
    def test_matches_assignment_cost(self):
        flow = [[0, 5, 2], [5, 0, 3], [2, 3, 0]]
        distance = [[0, 10, 20], [10, 0, 30], [20, 30, 0]]
        self.assertEqual(
            _identity_cost(flow, distance),
            assignment_cost(flow, distance, [0, 1, 2]),
        )

    def test_baselines_match_cached_values(self):
        """Most important test: verify IDENTITY_BASELINES are consistent."""
        for name, inst in TRAIN_INSTANCES.items():
            cost = _identity_cost(inst["flow"], inst["distance"])
            self.assertEqual(
                cost, IDENTITY_BASELINES[name],
                msg=f"Cached baseline for {name} doesn't match computed value",
            )


# ---------------------------------------------------------------------------
# _run_solver
# ---------------------------------------------------------------------------

class TestRunSolver(unittest.TestCase):
    def test_successful_solve(self):
        flow = [[0, 1], [1, 0]]
        distance = [[0, 1], [1, 0]]
        result, elapsed = _run_solver(lambda f, d: list(range(len(f))), flow, distance)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(elapsed, 0)

    def test_solver_raises(self):
        flow = [[0, 1], [1, 0]]
        distance = [[0, 1], [1, 0]]
        result, elapsed = _run_solver(
            lambda f, d: (_ for _ in ()).throw(ValueError("boom")),
            flow, distance,
        )
        self.assertIsInstance(result, str)
        self.assertIn("boom", result)

    def test_invalid_assignment_returned(self):
        flow = [[0, 1], [1, 0]]
        distance = [[0, 1], [1, 0]]
        result, _ = _run_solver(lambda f, d: [0, 0], flow, distance)
        self.assertIsInstance(result, str)  # error message

    def test_timeout(self):
        import time as _time

        old = prepare.TIME_BUDGET
        prepare.TIME_BUDGET = 0.01
        try:
            flow = [[0]]
            distance = [[0]]
            result, _ = _run_solver(
                lambda f, d: (_time.sleep(0.1), [0])[1],
                flow, distance,
            )
            self.assertIsInstance(result, str)
            self.assertIn("time", result.lower())
        finally:
            prepare.TIME_BUDGET = old


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate(unittest.TestCase):
    def test_with_identity_solver(self):
        results = evaluate(lambda f, d: list(range(len(f))))
        self.assertIn("avg_improvement", results)
        self.assertAlmostEqual(results["avg_improvement"], 0.0, places=5)
        for name in TRAIN_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(f, d):
            raise RuntimeError("crash")

        results = evaluate(bad_solver)
        self.assertAlmostEqual(results["avg_improvement"], -10.0)
        for name in TRAIN_INSTANCES:
            self.assertFalse(results[name]["valid"])

    def test_result_keys(self):
        results = evaluate(lambda f, d: list(range(len(f))))
        self.assertIn("avg_improvement", results)
        self.assertIn("total_time", results)
        for name in TRAIN_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# Instance data integrity
# ---------------------------------------------------------------------------

class TestInstanceData(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(TRAIN_INSTANCES), 3)

    def test_random_instances_deterministic(self):
        from scientist.qap.prepare import _generate_random_instance
        flow, distance = _generate_random_instance(50, seed=314159)
        self.assertEqual(flow, TRAIN_INSTANCES["rand50a"]["flow"])

    def test_train_no_optimal(self):
        for name, inst in TRAIN_INSTANCES.items():
            self.assertIsNone(inst["optimal"], f"{name} should have no optimal")
            self.assertFalse(inst["known"], f"{name} should not be known")

    def test_flow_distance_symmetric(self):
        """All instances should have symmetric flow and distance matrices."""
        for name, inst in TRAIN_INSTANCES.items():
            flow = inst["flow"]
            distance = inst["distance"]
            n = len(flow)
            for i in range(n):
                for j in range(i + 1, n):
                    self.assertEqual(flow[i][j], flow[j][i], f"{name}: flow not symmetric at ({i},{j})")
                    self.assertEqual(distance[i][j], distance[j][i], f"{name}: distance not symmetric at ({i},{j})")


if __name__ == "__main__":
    unittest.main()
