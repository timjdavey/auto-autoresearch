"""Tests for prepare.py — MAX-SAT evaluation harness."""

import unittest

import scientist.maxsat.prepare as prepare
from scientist.maxsat.prepare import (
    GREEDY_BASELINES,
    TIME_BUDGET,
    TRAIN_INSTANCES,
    _greedy_solve,
    _run_solver,
    count_unsatisfied,
    evaluate,
    validate_assignment,
)


# ---------------------------------------------------------------------------
# validate_assignment
# ---------------------------------------------------------------------------

class TestValidateAssignment(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_assignment(3, [True, False, True]))

    def test_wrong_length(self):
        err = validate_assignment(3, [True, False])
        self.assertIn("2", err)
        self.assertIn("3", err)

    def test_not_a_list(self):
        err = validate_assignment(2, (True, False))
        self.assertIn("list", err)

    def test_non_bool(self):
        err = validate_assignment(2, [True, 1])
        self.assertIsNotNone(err)
        self.assertIn("bool", err)


# ---------------------------------------------------------------------------
# count_unsatisfied
# ---------------------------------------------------------------------------

class TestCountUnsatisfied(unittest.TestCase):
    def test_all_satisfied(self):
        clauses = [[1, 2, 3], [-1, 2, 3]]
        self.assertEqual(count_unsatisfied(3, clauses, [True, True, True]), 0)

    def test_none_satisfied(self):
        # clause requires at least one True literal
        clauses = [[1, 2, 3]]
        self.assertEqual(count_unsatisfied(3, clauses, [False, False, False]), 1)

    def test_mixed(self):
        clauses = [[1, 2, 3], [-1, -2, -3]]
        # all True: first satisfied, second not
        self.assertEqual(count_unsatisfied(3, clauses, [True, True, True]), 1)


# ---------------------------------------------------------------------------
# _greedy_solve
# ---------------------------------------------------------------------------

class TestGreedySolve(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_greedy_solve(0, []), [])

    def test_single_var(self):
        assignment = _greedy_solve(1, [[1]])
        self.assertIsNone(validate_assignment(1, assignment))

    def test_produces_valid_assignment(self):
        n_vars, clauses = 10, [[1, -2, 3], [-4, 5, -6], [7, 8, -9]]
        assignment = _greedy_solve(n_vars, clauses)
        self.assertIsNone(validate_assignment(n_vars, assignment))

    def test_baselines_match_cached_values(self):
        """Most important test: verify GREEDY_BASELINES are consistent."""
        for name, inst in TRAIN_INSTANCES.items():
            assignment = _greedy_solve(inst["n_vars"], inst["clauses"])
            n_unsat = count_unsatisfied(inst["n_vars"], inst["clauses"], assignment)
            self.assertEqual(
                n_unsat, GREEDY_BASELINES[name],
                msg=f"Cached baseline for {name} doesn't match computed value",
            )


# ---------------------------------------------------------------------------
# _run_solver
# ---------------------------------------------------------------------------

class TestRunSolver(unittest.TestCase):
    def test_successful_solve(self):
        result, elapsed = _run_solver(lambda n, c: [True] * n, 3, [[1, 2, 3]])
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(elapsed, 0)

    def test_solver_raises(self):
        result, elapsed = _run_solver(
            lambda n, c: (_ for _ in ()).throw(ValueError("boom")),
            3, [[1, 2, 3]],
        )
        self.assertIsInstance(result, str)
        self.assertIn("boom", result)

    def test_invalid_assignment_returned(self):
        result, _ = _run_solver(lambda n, c: [1, 0, 1], 3, [[1, 2, 3]])
        self.assertIsInstance(result, str)  # error message (not bools)

    def test_timeout(self):
        import time as _time

        old = prepare.TIME_BUDGET
        prepare.TIME_BUDGET = 0.01
        try:
            result, _ = _run_solver(
                lambda n, c: (_time.sleep(0.1), [True] * n)[1],
                3, [[1, 2, 3]],
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
        for name in TRAIN_INSTANCES:
            self.assertTrue(results[name]["valid"])

    def test_crashing_solver(self):
        def bad_solver(n, c):
            raise RuntimeError("crash")

        results = evaluate(bad_solver)
        self.assertAlmostEqual(results["avg_improvement"], -10.0)
        for name in TRAIN_INSTANCES:
            self.assertFalse(results[name]["valid"])

    def test_result_keys(self):
        results = evaluate(_greedy_solve)
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
        from scientist.maxsat.prepare import _generate_random_instance
        n_vars, clauses = _generate_random_instance(200, 853, seed=421003)
        self.assertEqual(clauses, TRAIN_INSTANCES["rand200a"]["clauses"])

    def test_train_no_optimal(self):
        for name, inst in TRAIN_INSTANCES.items():
            self.assertIsNone(inst["optimal"], f"{name} should have no optimal")
            self.assertFalse(inst["known"], f"{name} should not be known")

    def test_all_clauses_have_3_literals(self):
        for name, inst in TRAIN_INSTANCES.items():
            for i, clause in enumerate(inst["clauses"]):
                self.assertEqual(
                    len(clause), 3,
                    msg=f"{name} clause {i} has {len(clause)} literals",
                )

    def test_variables_in_range(self):
        for name, inst in TRAIN_INSTANCES.items():
            n_vars = inst["n_vars"]
            for clause in inst["clauses"]:
                for lit in clause:
                    self.assertGreaterEqual(abs(lit), 1)
                    self.assertLessEqual(abs(lit), n_vars)


if __name__ == "__main__":
    unittest.main()
