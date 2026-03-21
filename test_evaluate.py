"""Tests for evaluate.py — study progress analysis."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import evaluate
from evaluate import analyse, analyse_and_save, load_results, print_report, STUDY_FIELDS


def _row(avg_improvement, avg_loss=0.1, training_time=1.0, benchmark_time=0.5):
    """Helper to build a row dict with sensible defaults."""
    return {
        "timestamp": "2026-01-01T00:00:00",
        "avg_improvement": avg_improvement,
        "avg_loss": avg_loss,
        "training_time": training_time,
        "benchmark_time": benchmark_time,
    }


# ---------------------------------------------------------------------------
# analyse
# ---------------------------------------------------------------------------

class TestAnalyse(unittest.TestCase):
    def test_two_trials_basic(self):
        rows = [_row(0.0), _row(0.05)]
        stats = analyse(rows)
        self.assertEqual(stats["num_trials"], 2)
        self.assertAlmostEqual(stats["first_avg_improvement"], 0.0)
        self.assertAlmostEqual(stats["last_avg_improvement"], 0.05)
        self.assertAlmostEqual(stats["total_improvement"], 0.05)
        self.assertAlmostEqual(stats["improvement_per_trial"], 0.025)

    def test_monotonically_improving(self):
        rows = [_row(i * 0.01) for i in range(10)]
        stats = analyse(rows)
        self.assertAlmostEqual(stats["total_improvement"], 0.09)
        self.assertAlmostEqual(stats["improvement_per_trial"], 0.009)
        self.assertFalse(stats["tailing_off"])

    def test_tailing_off_detected(self):
        # Strong early improvement, flat tail
        rows = [_row(i * 0.02) for i in range(8)]
        rows += [_row(0.14), _row(0.14)]  # flat last 2
        stats = analyse(rows)
        self.assertTrue(stats["tailing_off"])

    def test_tailing_off_not_detected_when_steady(self):
        rows = [_row(i * 0.01) for i in range(10)]
        stats = analyse(rows)
        self.assertFalse(stats["tailing_off"])

    def test_tailing_off_none_when_fewer_than_5(self):
        rows = [_row(0.0), _row(0.01), _row(0.02), _row(0.03)]
        stats = analyse(rows)
        self.assertIsNone(stats["tailing_off"])

    def test_tail_window_size(self):
        rows = [_row(i * 0.01) for i in range(10)]
        stats = analyse(rows)
        self.assertEqual(stats["tail_trials"], 2)

    def test_tail_window_minimum_one(self):
        rows = [_row(0.0), _row(0.05)]
        stats = analyse(rows)
        self.assertGreaterEqual(stats["tail_trials"], 1)

    def test_declining_performance(self):
        rows = [_row(0.10), _row(0.08), _row(0.05), _row(0.02), _row(0.0)]
        stats = analyse(rows)
        self.assertLess(stats["total_improvement"], 0)
        self.assertLess(stats["improvement_per_trial"], 0)

    def test_all_identical_values(self):
        rows = [_row(0.05)] * 6
        stats = analyse(rows)
        self.assertAlmostEqual(stats["total_improvement"], 0.0)
        self.assertAlmostEqual(stats["tail_velocity"], 0.0)
        self.assertAlmostEqual(stats["overall_velocity"], 0.0)


# ---------------------------------------------------------------------------
# load_results
# ---------------------------------------------------------------------------

class TestLoadResults(unittest.TestCase):
    def test_load_valid_csv(self):
        csv_content = (
            "timestamp,avg_improvement,avg_loss,training_time,benchmark_time\n"
            "2026-01-01T00:00:00,0.05,0.1,1.0,0.5\n"
            "2026-01-01T00:01:00,0.10,0.08,2.0,0.6\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            tmp_path = f.name
        try:
            with patch.object(evaluate, "RESULTS_LOG_PATH", tmp_path):
                rows = load_results()
            self.assertEqual(len(rows), 2)
            self.assertAlmostEqual(rows[0]["avg_improvement"], 0.05)
            self.assertAlmostEqual(rows[1]["avg_improvement"], 0.10)
        finally:
            os.unlink(tmp_path)

    def test_missing_file_returns_empty(self):
        with patch.object(evaluate, "RESULTS_LOG_PATH", "/tmp/nonexistent_eval_file.csv"):
            rows = load_results()
        self.assertEqual(rows, [])

    def test_value_types(self):
        csv_content = (
            "timestamp,avg_improvement,avg_loss,training_time,benchmark_time\n"
            "2026-03-20T17:26:16,0.129949,0.032781,0.928,0.159\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            tmp_path = f.name
        try:
            with patch.object(evaluate, "RESULTS_LOG_PATH", tmp_path):
                rows = load_results()
            row = rows[0]
            self.assertIsInstance(row["timestamp"], str)
            self.assertIsInstance(row["avg_improvement"], float)
            self.assertIsInstance(row["avg_loss"], float)
            self.assertIsInstance(row["training_time"], float)
            self.assertIsInstance(row["benchmark_time"], float)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# analyse_and_save
# ---------------------------------------------------------------------------

class TestAnalyseAndSave(unittest.TestCase):
    def _write_results_csv(self, rows):
        """Write a temporary results CSV and return its path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        f.write("timestamp,avg_improvement,avg_loss,training_time,benchmark_time\n")
        for r in rows:
            f.write(f"{r['timestamp']},{r['avg_improvement']},{r['avg_loss']},"
                    f"{r['training_time']},{r['benchmark_time']}\n")
        f.flush()
        f.close()
        return f.name

    def test_saves_study_row(self):
        results_path = self._write_results_csv([
            _row(0.0), _row(0.05), _row(0.10),
        ])
        output_path = tempfile.mktemp(suffix=".csv")
        try:
            with patch.object(evaluate, "RESULTS_LOG_PATH", results_path):
                stats = analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)
            self.assertIsNotNone(stats)
            self.assertEqual(stats["num_trials"], 3)
            # Verify output file
            import csv
            with open(output_path) as f:
                reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0]["timestamp"], "2026-01-01T00:00:00")
            self.assertEqual(set(reader[0].keys()), set(STUDY_FIELDS))
        finally:
            os.unlink(results_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_returns_none_with_too_few_rows(self):
        results_path = self._write_results_csv([_row(0.0)])
        output_path = tempfile.mktemp(suffix=".csv")
        try:
            with patch.object(evaluate, "RESULTS_LOG_PATH", results_path):
                stats = analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)
            self.assertIsNone(stats)
            self.assertFalse(os.path.exists(output_path))
        finally:
            os.unlink(results_path)

    def test_appends_multiple_studies(self):
        results_path = self._write_results_csv([_row(0.0), _row(0.05)])
        output_path = tempfile.mktemp(suffix=".csv")
        try:
            with patch.object(evaluate, "RESULTS_LOG_PATH", results_path):
                analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)
                analyse_and_save(timestamp="2026-01-02T00:00:00", output_path=output_path)
            import csv
            with open(output_path) as f:
                reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 2)
            self.assertEqual(reader[0]["timestamp"], "2026-01-01T00:00:00")
            self.assertEqual(reader[1]["timestamp"], "2026-01-02T00:00:00")
        finally:
            os.unlink(results_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


# ---------------------------------------------------------------------------
# print_report
# ---------------------------------------------------------------------------

class TestPrintReport(unittest.TestCase):
    def _stats(self, **overrides):
        defaults = {
            "num_trials": 10,
            "first_avg_improvement": 0.0,
            "last_avg_improvement": 0.09,
            "total_improvement": 0.09,
            "improvement_per_trial": 0.009,
            "tail_trials": 2,
            "tail_velocity": 0.005,
            "overall_velocity": 0.009,
            "tailing_off": False,
        }
        defaults.update(overrides)
        return defaults

    def test_no_crash_and_contains_values(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(self._stats())
        output = buf.getvalue()
        self.assertIn("10", output)  # num_trials
        self.assertIn("0.09", output)  # total_improvement

    def test_tailing_off_none(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(self._stats(tailing_off=None))
        self.assertIn("too few trials", buf.getvalue())

    def test_tailing_off_true(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(self._stats(tailing_off=True))
        self.assertIn("YES", buf.getvalue())

    def test_tailing_off_false(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(self._stats(tailing_off=False))
        output = buf.getvalue()
        self.assertIn("no", output.lower())


if __name__ == "__main__":
    unittest.main()
