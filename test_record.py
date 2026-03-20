"""Tests for lab/record.py — output formatting contract tests.

These verify that record.py handles the data shapes prepare.py produces
without crashing. The Supervisor may modify record.py, so these tests
serve as a safety net for the interface contract.
"""

import io
import unittest
from contextlib import redirect_stdout

from lab.record import benchmark_results, training_results


def _training_results_dict(instances=None, avg_improvement=0.05, total_time=1.5):
    """Build a results dict matching prepare.evaluate() output shape."""
    if instances is None:
        instances = {
            "rand20a": {
                "valid": True,
                "tour_length": 37500.00,
                "baseline": 39587.04,
                "improvement": 0.0527,
                "time": 0.003,
            },
            "rand50a": {
                "valid": True,
                "tour_length": 67000.00,
                "baseline": 71140.88,
                "improvement": 0.0582,
                "time": 0.010,
            },
        }
    return {**instances, "avg_improvement": avg_improvement, "total_time": total_time}


def _benchmark_results_dict(instances=None, avg_loss=0.15, total_time=0.8):
    """Build a results dict matching prepare.benchmark() output shape."""
    if instances is None:
        instances = {
            "berlin52": {
                "valid": True,
                "tour_length": 8500.00,
                "optimal": 7542.00,
                "loss": 0.127,
                "time": 0.002,
            },
            "eil51": {
                "valid": True,
                "tour_length": 490.00,
                "optimal": 426.00,
                "loss": 0.150,
                "time": 0.002,
            },
        }
    return {**instances, "avg_loss": avg_loss, "total_time": total_time}


# ---------------------------------------------------------------------------
# training_results
# ---------------------------------------------------------------------------

class TestTrainingResults(unittest.TestCase):
    def test_valid_results_no_crash(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            training_results(_training_results_dict())
        output = buf.getvalue()
        self.assertIn("rand20a", output)
        self.assertIn("rand50a", output)

    def test_failed_instance(self):
        results = _training_results_dict(instances={
            "rand20a": {"valid": False, "error": "exceeded time budget", "time": 30.0},
        })
        buf = io.StringIO()
        with redirect_stdout(buf):
            training_results(results)
        self.assertIn("FAILED", buf.getvalue())

    def test_all_failed_no_crash(self):
        results = _training_results_dict(
            instances={
                "rand20a": {"valid": False, "error": "crash", "time": 0.0},
                "rand50a": {"valid": False, "error": "timeout", "time": 30.0},
            },
            avg_improvement=-10.0,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            training_results(results)
        # Should not raise


# ---------------------------------------------------------------------------
# benchmark_results
# ---------------------------------------------------------------------------

class TestBenchmarkResults(unittest.TestCase):
    def test_valid_results_no_crash(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            benchmark_results(_benchmark_results_dict())
        output = buf.getvalue()
        self.assertIn("berlin52", output)
        self.assertIn("eil51", output)

    def test_failed_instance(self):
        results = _benchmark_results_dict(instances={
            "berlin52": {"valid": False, "error": "solver exception", "time": 0.0},
        })
        buf = io.StringIO()
        with redirect_stdout(buf):
            benchmark_results(results)
        self.assertIn("FAILED", buf.getvalue())

    def test_mixed_valid_and_failed(self):
        results = _benchmark_results_dict(instances={
            "berlin52": {
                "valid": True,
                "tour_length": 8500.00,
                "optimal": 7542.00,
                "loss": 0.127,
                "time": 0.002,
            },
            "eil51": {"valid": False, "error": "crash", "time": 0.0},
        })
        buf = io.StringIO()
        with redirect_stdout(buf):
            benchmark_results(results)
        output = buf.getvalue()
        self.assertIn("berlin52", output)
        self.assertIn("FAILED", output)


if __name__ == "__main__":
    unittest.main()
