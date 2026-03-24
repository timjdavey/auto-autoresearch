"""Tests for prepare.py — facility location evaluation harness."""

import unittest

import scientist.facloc.prepare as prepare
from scientist.facloc.prepare import (
    BASELINE_COSTS,
    BENCHMARK_INSTANCES,
    INSTANCES,
    LP_BOUNDS,
    QUICK_INSTANCES,
    TIME_BUDGET,
    TRAIN_INSTANCES,
    _baseline_cost,
    _baseline_solve,
    _run_solver,
    benchmark,
    evaluate,
    total_cost,
    validate_assignment,
)


# ---------------------------------------------------------------------------
# total_cost
# ---------------------------------------------------------------------------

class TestTotalCost(unittest.TestCase):
    def test_single_facility(self):
        opening_costs = [100]
        assign_costs = [[10, 20, 30]]
        # All clients assigned to facility 0: opening=100, assign=10+20+30=60
        self.assertEqual(total_cost(opening_costs, assign_costs, [0, 0, 0]), 160)

    def test_two_facilities(self):
        opening_costs = [100, 200]
        assign_costs = [[10, 50], [50, 10]]
        # Client 0 -> fac 0, client 1 -> fac 1: opening=100+200, assign=10+10
        self.assertEqual(total_cost(opening_costs, assign_costs, [0, 1]), 320)
        # Both to fac 0: opening=100, assign=10+50
        self.assertEqual(total_cost(opening_costs, assign_costs, [0, 0]), 160)

    def test_unused_facility_not_charged(self):
        opening_costs = [100, 200, 300]
        assign_costs = [[10, 20], [30, 40], [50, 60]]
        # Only facility 0 used
        self.assertEqual(total_cost(opening_costs, assign_costs, [0, 0]), 130)


# ---------------------------------------------------------------------------
# validate_assignment
# ---------------------------------------------------------------------------

class TestValidateAssignment(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_assignment(3, 2, [0, 2]))

    def test_wrong_length(self):
        err = validate_assignment(2, 3, [0, 1])
        self.assertIn("2", err)
        self.assertIn("3", err)

    def test_not_a_list(self):
        err = validate_assignment(1, 1, (0,))
        self.assertIn("list", err)

    def test_out_of_range(self):
        err = validate_assignment(2, 1, [5])
        self.assertIsNotNone(err)

    def test_negative(self):
        err = validate_assignment(2, 1, [-1])
        self.assertIsNotNone(err)


# ---------------------------------------------------------------------------
# _baseline_cost
# ---------------------------------------------------------------------------

class TestBaselineCost(unittest.TestCase):
    def test_matches_total_cost(self):
        opening_costs = [100, 200, 300]
        assign_costs = [[10, 50, 30], [50, 10, 40], [30, 40, 10]]
        assignment = _baseline_solve(opening_costs, assign_costs)
        self.assertEqual(
            _baseline_cost(opening_costs, assign_costs),
            total_cost(opening_costs, assign_costs, assignment),
        )

    def test_baselines_match_cached_values(self):
        """Most important test: verify BASELINE_COSTS are consistent."""
        for name, inst in TRAIN_INSTANCES.items():
            cost = _baseline_cost(inst["opening_costs"], inst["assign_costs"])
            self.assertEqual(
                cost, BASELINE_COSTS[name],
                msg=f"Cached baseline for {name} doesn't match computed value",
            )


# ---------------------------------------------------------------------------
# _run_solver
# ---------------------------------------------------------------------------

class TestRunSolver(unittest.TestCase):
    def test_successful_solve(self):
        opening_costs = [100]
        assign_costs = [[10, 20]]
        result, elapsed = _run_solver(
            lambda o, a: [0] * len(a[0]), opening_costs, assign_costs
        )
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(elapsed, 0)

    def test_solver_raises(self):
        opening_costs = [100]
        assign_costs = [[10]]
        result, elapsed = _run_solver(
            lambda o, a: (_ for _ in ()).throw(ValueError("boom")),
            opening_costs, assign_costs,
        )
        self.assertIsInstance(result, str)
        self.assertIn("boom", result)

    def test_invalid_assignment_returned(self):
        opening_costs = [100, 200]
        assign_costs = [[10], [20]]
        result, _ = _run_solver(lambda o, a: [5], opening_costs, assign_costs)
        self.assertIsInstance(result, str)  # error message

    def test_timeout(self):
        import time as _time

        old = prepare.TIME_BUDGET
        prepare.TIME_BUDGET = 0.01
        try:
            opening_costs = [100]
            assign_costs = [[10]]
            result, _ = _run_solver(
                lambda o, a: (_time.sleep(0.1), [0])[1],
                opening_costs, assign_costs,
            )
            self.assertIsInstance(result, str)
            self.assertIn("time", result.lower())
        finally:
            prepare.TIME_BUDGET = old


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate(unittest.TestCase):
    def test_with_baseline_solver(self):
        results = evaluate(_baseline_solve)
        self.assertIn("avg_improvement", results)
        self.assertAlmostEqual(results["avg_improvement"], 0.0, places=5)
        for name in QUICK_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(o, a):
            raise RuntimeError("crash")

        results = evaluate(bad_solver)
        self.assertAlmostEqual(results["avg_improvement"], -10.0)
        for name in QUICK_INSTANCES:
            self.assertFalse(results[name]["valid"])

    def test_result_keys(self):
        results = evaluate(_baseline_solve)
        self.assertIn("avg_improvement", results)
        self.assertIn("total_time", results)
        for name in QUICK_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# benchmark
# ---------------------------------------------------------------------------

class TestBenchmark(unittest.TestCase):
    def test_with_baseline_solver(self):
        results = benchmark(_baseline_solve)
        self.assertIn("avg_loss", results)
        self.assertGreater(results["avg_loss"], 0)  # baseline is worse than LP bound
        for name in BENCHMARK_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(o, a):
            raise RuntimeError("crash")

        results = benchmark(bad_solver)
        self.assertAlmostEqual(results["avg_loss"], 10.0)

    def test_result_keys(self):
        results = benchmark(_baseline_solve)
        self.assertIn("avg_loss", results)
        self.assertIn("total_time", results)
        for name in BENCHMARK_INSTANCES:
            self.assertIn(name, results)


# ---------------------------------------------------------------------------
# Instance data integrity
# ---------------------------------------------------------------------------

class TestInstanceData(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(TRAIN_INSTANCES), 3)
        self.assertEqual(len(BENCHMARK_INSTANCES), 5)
        self.assertEqual(len(INSTANCES), 8)

    def test_quick_instances(self):
        self.assertEqual(len(QUICK_INSTANCES), 3)
        for name in QUICK_INSTANCES:
            self.assertIn(name, TRAIN_INSTANCES)

    def test_random_instances_deterministic(self):
        from scientist.facloc.prepare import _generate_random_instance
        opening_costs, assign_costs = _generate_random_instance(30, 100, seed=200003)
        self.assertEqual(opening_costs, TRAIN_INSTANCES["rand30_100a"]["opening_costs"])

    def test_benchmark_have_known(self):
        for name, inst in BENCHMARK_INSTANCES.items():
            self.assertTrue(inst["known"], f"{name} should be known")

    def test_train_no_optimal(self):
        for name, inst in TRAIN_INSTANCES.items():
            self.assertIsNone(inst["optimal"], f"{name} should have no optimal")
            self.assertFalse(inst["known"], f"{name} should not be known")

    def test_lp_bounds_exist(self):
        for name in BENCHMARK_INSTANCES:
            self.assertIn(name, LP_BOUNDS)
            self.assertGreater(LP_BOUNDS[name], 0)


if __name__ == "__main__":
    unittest.main()
