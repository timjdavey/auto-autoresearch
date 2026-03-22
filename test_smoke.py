"""Smoke test — end-to-end data pipeline without Claude invocation.

Runs the full chain: solver -> evaluate -> analyse.
Verifies the entire pipeline produces valid output without crashing.
"""

import unittest

from evaluate import analyse
from lab.train import solve
from prepare import benchmark, evaluate


class TestEndToEndPipeline(unittest.TestCase):
    def test_full_pipeline(self):
        # 1. Evaluate the solver
        train_results = evaluate(solve)
        self.assertIn("avg_improvement", train_results)
        self.assertIn("total_time", train_results)

        bench_results = benchmark(solve)
        self.assertIn("avg_loss", bench_results)
        self.assertIn("total_time", bench_results)

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
        self.assertIn("num_trials", stats)
        self.assertEqual(stats["num_trials"], 2)
        self.assertIsInstance(stats["total_improvement"], float)


if __name__ == "__main__":
    unittest.main()
