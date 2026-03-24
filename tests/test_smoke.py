"""Smoke test — end-to-end data pipeline without Claude invocation.

Runs the full chain: solver -> evaluate -> analyse.
Verifies the entire pipeline produces valid output without crashing.
"""

import unittest

from supervisor.evaluate import analyse

from scientist.tsp.train import solve as tsp_solve
from scientist.tsp.prepare import benchmark as tsp_benchmark, evaluate as tsp_evaluate

from scientist.graph_colouring.train import solve as gc_solve
from scientist.graph_colouring.prepare import benchmark as gc_benchmark, evaluate as gc_evaluate

from scientist.qap.train import solve as qap_solve
from scientist.qap.prepare import benchmark as qap_benchmark, evaluate as qap_evaluate


def _run_pipeline(test_case, evaluate_fn, benchmark_fn, solve_fn):
    """Shared pipeline test for any problem."""
    # 1. Evaluate the solver
    train_results = evaluate_fn(solve_fn)
    test_case.assertIn("avg_improvement", train_results)
    test_case.assertIn("total_time", train_results)

    bench_results = benchmark_fn(solve_fn)
    test_case.assertIn("avg_loss", bench_results)
    test_case.assertIn("total_time", bench_results)

    # 2. Build evaluation rows and run through analyse
    rows = [
        {
            "timestamp": "2026-01-01T00:00:00",
            "avg_improvement": 0.0,  # baseline
            "avg_loss": bench_results["avg_loss"],
            "training_time": train_results["total_time"],
            "benchmark_time": bench_results["total_time"],
        },
        {
            "timestamp": "2026-01-01T00:01:00",
            "avg_improvement": train_results["avg_improvement"],
            "avg_loss": bench_results["avg_loss"],
            "training_time": train_results["total_time"],
            "benchmark_time": bench_results["total_time"],
        },
    ]
    stats = analyse(rows)
    test_case.assertIn("num_trials", stats)
    test_case.assertEqual(stats["num_trials"], 2)
    test_case.assertIsInstance(stats["total_improvement"], float)


class TestEndToEndPipeline(unittest.TestCase):
    def test_tsp_pipeline(self):
        _run_pipeline(self, tsp_evaluate, tsp_benchmark, tsp_solve)

    def test_graph_colouring_pipeline(self):
        _run_pipeline(self, gc_evaluate, gc_benchmark, gc_solve)

    def test_qap_pipeline(self):
        _run_pipeline(self, qap_evaluate, qap_benchmark, qap_solve)


if __name__ == "__main__":
    unittest.main()
