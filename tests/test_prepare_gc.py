"""Tests for prepare.py — graph colouring evaluation harness."""

import unittest

import scientist.graph_colouring.prepare as prepare
from scientist.graph_colouring.prepare import (
    BENCHMARK_INSTANCES,
    GREEDY_BASELINES,
    INSTANCES,
    QUICK_INSTANCES,
    TIME_BUDGET,
    TRAIN_INSTANCES,
    _count_colours,
    _greedy_solve,
    _run_solver,
    benchmark,
    evaluate,
    validate_colouring,
)


# ---------------------------------------------------------------------------
# validate_colouring
# ---------------------------------------------------------------------------

class TestValidateColouring(unittest.TestCase):
    def test_valid(self):
        adj = [[1, 2], [0, 2], [0, 1]]  # triangle
        self.assertIsNone(validate_colouring(adj, 3, [0, 1, 2]))

    def test_wrong_length(self):
        adj = [[1], [0]]
        err = validate_colouring(adj, 2, [0])
        self.assertIn("1", err)
        self.assertIn("2", err)

    def test_not_a_list(self):
        adj = [[]]
        err = validate_colouring(adj, 1, (0,))
        self.assertIn("list", err)

    def test_negative_colour(self):
        adj = [[1], [0]]
        err = validate_colouring(adj, 2, [0, -1])
        self.assertIsNotNone(err)

    def test_adjacent_same_colour(self):
        adj = [[1], [0]]
        err = validate_colouring(adj, 2, [0, 0])
        self.assertIsNotNone(err)
        self.assertIn("adjacent", err)

    def test_non_integer_colour(self):
        adj = [[]]
        err = validate_colouring(adj, 1, [1.5])
        self.assertIsNotNone(err)


# ---------------------------------------------------------------------------
# _greedy_solve
# ---------------------------------------------------------------------------

class TestGreedySolve(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_greedy_solve([], 0, 0), [])

    def test_single_node(self):
        colouring = _greedy_solve([[]], 1, 0)
        self.assertEqual(colouring, [0])

    def test_produces_valid_colouring(self):
        # Complete graph K4
        adj = [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]
        colouring = _greedy_solve(adj, 4, 6)
        self.assertIsNone(validate_colouring(adj, 4, colouring))
        self.assertEqual(_count_colours(colouring), 4)

    def test_baselines_match_cached_values(self):
        """Most important test: verify GREEDY_BASELINES are consistent."""
        for name, inst in TRAIN_INSTANCES.items():
            colouring = _greedy_solve(inst["adj"], inst["n_nodes"], inst["n_edges"])
            n_colours = _count_colours(colouring)
            self.assertEqual(
                n_colours, GREEDY_BASELINES[name],
                msg=f"Cached baseline for {name} doesn't match computed value",
            )


# ---------------------------------------------------------------------------
# _run_solver
# ---------------------------------------------------------------------------

class TestRunSolver(unittest.TestCase):
    def test_successful_solve(self):
        adj = [[1, 2], [0, 2], [0, 1]]
        result, elapsed = _run_solver(lambda a, n, e: list(range(n)), adj, 3, 3)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(elapsed, 0)

    def test_solver_raises(self):
        adj = [[1], [0]]
        result, elapsed = _run_solver(
            lambda a, n, e: (_ for _ in ()).throw(ValueError("boom")),
            adj, 2, 1,
        )
        self.assertIsInstance(result, str)
        self.assertIn("boom", result)

    def test_invalid_colouring_returned(self):
        adj = [[1], [0]]
        result, _ = _run_solver(lambda a, n, e: [0, 0], adj, 2, 1)
        self.assertIsInstance(result, str)  # error message

    def test_timeout(self):
        import time as _time

        old = prepare.TIME_BUDGET
        prepare.TIME_BUDGET = 0.01
        try:
            result, _ = _run_solver(
                lambda a, n, e: (_time.sleep(0.1), [0])[1],
                [[]], 1, 0,
            )
            self.assertIsInstance(result, str)
            self.assertIn("time", result.lower())
        finally:
            prepare.TIME_BUDGET = old


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate(unittest.TestCase):
    def test_with_greedy_solver(self):
        results = evaluate(_greedy_solve)
        self.assertIn("avg_improvement", results)
        self.assertAlmostEqual(results["avg_improvement"], 0.0, places=5)
        for name in QUICK_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(a, n, e):
            raise RuntimeError("crash")

        results = evaluate(bad_solver)
        self.assertAlmostEqual(results["avg_improvement"], -10.0)
        for name in QUICK_INSTANCES:
            self.assertFalse(results[name]["valid"])

    def test_result_keys(self):
        results = evaluate(_greedy_solve)
        self.assertIn("avg_improvement", results)
        self.assertIn("total_time", results)
        for name in QUICK_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# benchmark
# ---------------------------------------------------------------------------

class TestBenchmark(unittest.TestCase):
    def test_with_greedy_solver(self):
        results = benchmark(_greedy_solve)
        self.assertIn("avg_loss", results)
        self.assertGreaterEqual(results["avg_loss"], 0)  # greedy >= optimal
        for name in BENCHMARK_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(a, n, e):
            raise RuntimeError("crash")

        results = benchmark(bad_solver)
        self.assertAlmostEqual(results["avg_loss"], 10.0)

    def test_result_keys(self):
        results = benchmark(_greedy_solve)
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
        from scientist.graph_colouring.prepare import _generate_random_instance
        adj, n_nodes, n_edges = _generate_random_instance(30, 0.3, seed=142857)
        self.assertEqual(adj, TRAIN_INSTANCES["rand30a"]["adj"])

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
