"""Tests for prepare.py — TSP evaluation harness."""

import math
import unittest

import scientist.tsp.prepare as prepare
from scientist.tsp.prepare import (
    BENCHMARK_INSTANCES,
    INSTANCES,
    NN_BASELINES,
    QUICK_INSTANCES,
    TIME_BUDGET,
    TRAIN_INSTANCES,
    _nn_solve,
    _run_solver,
    benchmark,
    euclidean_distance,
    evaluate,
    tour_length,
    validate_tour,
)


# ---------------------------------------------------------------------------
# euclidean_distance
# ---------------------------------------------------------------------------

class TestEuclideanDistance(unittest.TestCase):
    def test_same_point(self):
        self.assertEqual(euclidean_distance((5, 5), (5, 5)), 0.0)

    def test_known_distance(self):
        self.assertAlmostEqual(euclidean_distance((0, 0), (3, 4)), 5.0)

    def test_symmetry(self):
        a, b = (10, 20), (30, 40)
        self.assertEqual(euclidean_distance(a, b), euclidean_distance(b, a))


# ---------------------------------------------------------------------------
# tour_length
# ---------------------------------------------------------------------------

class TestTourLength(unittest.TestCase):
    def test_single_city(self):
        self.assertEqual(tour_length([(0, 0)], [0]), 0.0)

    def test_triangle(self):
        coords = [(0, 0), (3, 0), (0, 4)]
        length = tour_length(coords, [0, 1, 2])
        expected = 3.0 + 5.0 + 4.0  # 0->1 + 1->2 + 2->0
        self.assertAlmostEqual(length, expected)

    def test_order_affects_length(self):
        coords = [(0, 0), (1, 0), (0, 1), (1, 1)]
        l1 = tour_length(coords, [0, 1, 3, 2])  # square path
        l2 = tour_length(coords, [0, 1, 2, 3])  # zigzag path
        self.assertNotAlmostEqual(l1, l2)


# ---------------------------------------------------------------------------
# validate_tour
# ---------------------------------------------------------------------------

class TestValidateTour(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_tour([(0, 0), (1, 1), (2, 2)], [2, 0, 1]))

    def test_wrong_length(self):
        err = validate_tour([(0, 0), (1, 1)], [0])
        self.assertIn("1", err)
        self.assertIn("2", err)

    def test_not_a_list(self):
        err = validate_tour([(0, 0)], (0,))
        self.assertIn("list", err)

    def test_duplicate_cities(self):
        err = validate_tour([(0, 0), (1, 1)], [0, 0])
        self.assertIsNotNone(err)

    def test_missing_city(self):
        err = validate_tour([(0, 0), (1, 1), (2, 2)], [0, 1, 5])
        self.assertIsNotNone(err)


# ---------------------------------------------------------------------------
# _nn_solve
# ---------------------------------------------------------------------------

class TestNNSolve(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_nn_solve([]), [])

    def test_single_city(self):
        self.assertEqual(_nn_solve([(5, 5)]), [0])

    def test_produces_valid_tour(self):
        coords = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        tour = _nn_solve(coords)
        self.assertIsNone(validate_tour(coords, tour))

    def test_baselines_match_cached_values(self):
        """Most important test: verify NN_BASELINES are consistent."""
        for name, inst in TRAIN_INSTANCES.items():
            tour = _nn_solve(inst["coords"])
            length = tour_length(inst["coords"], tour)
            self.assertAlmostEqual(
                length, NN_BASELINES[name], places=5,
                msg=f"Cached baseline for {name} doesn't match computed value",
            )


# ---------------------------------------------------------------------------
# _run_solver
# ---------------------------------------------------------------------------

class TestRunSolver(unittest.TestCase):
    def test_successful_solve(self):
        coords = [(0, 0), (1, 0), (0, 1)]
        result, elapsed = _run_solver(lambda c: list(range(len(c))), coords)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(elapsed, 0)

    def test_solver_raises(self):
        coords = [(0, 0), (1, 0)]
        result, elapsed = _run_solver(lambda c: (_ for _ in ()).throw(ValueError("boom")), coords)
        self.assertIsInstance(result, str)
        self.assertIn("boom", result)

    def test_invalid_tour_returned(self):
        coords = [(0, 0), (1, 0)]
        result, _ = _run_solver(lambda c: [0, 0], coords)
        self.assertIsInstance(result, str)  # error message

    def test_timeout(self):
        import time as _time

        old = prepare.TIME_BUDGET
        prepare.TIME_BUDGET = 0.01
        try:
            result, _ = _run_solver(lambda c: (_time.sleep(0.1), list(range(len(c))))[-1], coords=[(0, 0)])
            self.assertIsInstance(result, str)
            self.assertIn("time", result.lower())
        finally:
            prepare.TIME_BUDGET = old


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate(unittest.TestCase):
    def test_with_nn_solver(self):
        results = evaluate(_nn_solve)
        self.assertIn("avg_improvement", results)
        self.assertAlmostEqual(results["avg_improvement"], 0.0, places=5)
        for name in QUICK_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(c):
            raise RuntimeError("crash")

        results = evaluate(bad_solver)
        self.assertAlmostEqual(results["avg_improvement"], -10.0)
        for name in QUICK_INSTANCES:
            self.assertFalse(results[name]["valid"])

    def test_result_keys(self):
        results = evaluate(_nn_solve)
        self.assertIn("avg_improvement", results)
        self.assertIn("total_time", results)
        for name in QUICK_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# benchmark
# ---------------------------------------------------------------------------

class TestBenchmark(unittest.TestCase):
    def test_with_nn_solver(self):
        results = benchmark(_nn_solve)
        self.assertIn("avg_loss", results)
        self.assertGreater(results["avg_loss"], 0)  # NN is worse than optimal
        for name in BENCHMARK_INSTANCES:
            self.assertTrue(results[name]["valid"])
            self.assertGreater(results[name]["loss"], 0)

    def test_crashing_solver(self):
        def bad_solver(c):
            raise RuntimeError("crash")

        results = benchmark(bad_solver)
        self.assertAlmostEqual(results["avg_loss"], 10.0)

    def test_result_keys(self):
        results = benchmark(_nn_solve)
        self.assertIn("avg_loss", results)
        self.assertIn("total_time", results)
        for name in BENCHMARK_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# Instance data integrity
# ---------------------------------------------------------------------------

class TestInstanceData(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(TRAIN_INSTANCES), 20)
        self.assertEqual(len(BENCHMARK_INSTANCES), 5)
        self.assertEqual(len(INSTANCES), 25)

    def test_quick_instances(self):
        self.assertEqual(len(QUICK_INSTANCES), 3)
        for name in QUICK_INSTANCES:
            self.assertIn(name, TRAIN_INSTANCES)

    def test_random_instances_deterministic(self):
        from scientist.tsp.prepare import _generate_random_instance
        self.assertEqual(_generate_random_instance(20, seed=142857), list(TRAIN_INSTANCES["rand20a"]["coords"]))

    def test_benchmark_have_optimal(self):
        for name, inst in BENCHMARK_INSTANCES.items():
            self.assertIsNotNone(inst["optimal"], f"{name} missing optimal")
            self.assertTrue(inst["known"], f"{name} should be known")

    def test_train_no_optimal(self):
        for name, inst in TRAIN_INSTANCES.items():
            self.assertIsNone(inst["optimal"], f"{name} should have no optimal")
            self.assertFalse(inst["known"], f"{name} should not be known")


if __name__ == "__main__":
    unittest.main()
