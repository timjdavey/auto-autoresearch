"""Smoke test — end-to-end data pipeline without Claude invocation.

Runs the full chain: solver -> evaluate -> analyse.
Verifies the entire pipeline produces valid output without crashing.
"""

import unittest

from supervisor.evaluate import analyse

from scientist.qap.train import solve as qap_solve
from scientist.qap.prepare import evaluate as qap_evaluate

from scientist.facloc.train import solve as fl_solve
from scientist.facloc.prepare import benchmark as fl_benchmark, evaluate as fl_evaluate

from scientist.maxsat.train import solve as maxsat_solve
from scientist.maxsat.prepare import evaluate as maxsat_evaluate


def _run_pipeline_with_benchmark(test_case, evaluate_fn, benchmark_fn, solve_fn):
    """Shared pipeline test for problems with both evaluate and benchmark."""
    # 1. Evaluate the solver
    train_results = evaluate_fn(solve_fn)
    test_case.assertIn("avg_improvement", train_results)
    test_case.assertIn("success_rate", train_results)
    test_case.assertIn("total_time", train_results)

    bench_results = benchmark_fn(solve_fn)
    test_case.assertIn("avg_loss", bench_results)
    test_case.assertIn("success_rate", bench_results)
    test_case.assertIn("total_time", bench_results)

    # 2. Build evaluation rows and run through analyse
    rows = [
        {
            "timestamp": "2026-01-01T00:00:00",
            "avg_improvement": 0.0,
            "success_rate": 1.0,
            "training_time": train_results["total_time"],
        },
        {
            "timestamp": "2026-01-01T00:01:00",
            "avg_improvement": train_results["avg_improvement"],
            "success_rate": train_results["success_rate"],
            "training_time": train_results["total_time"],
        },
    ]
    stats = analyse(rows)
    test_case.assertIn("num_trials", stats)
    test_case.assertEqual(stats["num_trials"], 2)
    test_case.assertIsInstance(stats["total_improvement"], float)
    test_case.assertIn("avg_success_rate", stats)
    test_case.assertIn("improvement_velocity", stats)


def _run_pipeline(test_case, evaluate_fn, solve_fn):
    """Shared pipeline test for problems with evaluate only."""
    train_results = evaluate_fn(solve_fn)
    test_case.assertIn("avg_improvement", train_results)
    test_case.assertIn("success_rate", train_results)
    test_case.assertIn("total_time", train_results)

    rows = [
        {
            "timestamp": "2026-01-01T00:00:00",
            "avg_improvement": 0.0,
            "success_rate": 1.0,
            "training_time": train_results["total_time"],
        },
        {
            "timestamp": "2026-01-01T00:01:00",
            "avg_improvement": train_results["avg_improvement"],
            "success_rate": train_results["success_rate"],
            "training_time": train_results["total_time"],
        },
    ]
    stats = analyse(rows)
    test_case.assertIn("num_trials", stats)
    test_case.assertEqual(stats["num_trials"], 2)
    test_case.assertIsInstance(stats["total_improvement"], float)


class TestEndToEndPipeline(unittest.TestCase):
    def test_qap_pipeline(self):
        _run_pipeline(self, qap_evaluate, qap_solve)

    def test_facility_location_pipeline(self):
        _run_pipeline_with_benchmark(self, fl_evaluate, fl_benchmark, fl_solve)

    def test_maxsat_pipeline(self):
        train_results = maxsat_evaluate(maxsat_solve)
        self.assertIn("avg_improvement", train_results)
        self.assertIn("success_rate", train_results)
        self.assertIn("total_time", train_results)


if __name__ == "__main__":
    unittest.main()
