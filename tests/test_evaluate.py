"""Tests for evaluate.py — study progress analysis."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import scientist
import supervisor.evaluate as evaluate
from supervisor.evaluate import analyse, analyse_and_save, load_results, print_report, STUDY_FIELDS


def _row(avg_improvement, training_time=1.0):
    """Helper to build a row dict with sensible defaults."""
    return {
        "timestamp": "2026-01-01T00:00:00",
        "avg_improvement": avg_improvement,
        "training_time": training_time,
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
    def test_load_valid_tsv(self):
        tsv_content = (
            "timestamp\tavg_improvement\ttraining_time\n"
            "2026-01-01T00:00:00\t0.05\t1.0\n"
            "2026-01-01T00:01:00\t0.10\t2.0\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(tsv_content)
            f.flush()
            tmp_path = f.name
        try:
            rows = load_results(tmp_path)
            self.assertEqual(len(rows), 2)
            self.assertAlmostEqual(rows[0]["avg_improvement"], 0.05)
            self.assertAlmostEqual(rows[1]["avg_improvement"], 0.10)
        finally:
            os.unlink(tmp_path)

    def test_missing_file_returns_empty(self):
        rows = load_results("/tmp/nonexistent_eval_file.tsv")
        self.assertEqual(rows, [])

    def test_value_types(self):
        tsv_content = (
            "timestamp\tavg_improvement\ttraining_time\n"
            "2026-03-20T17:26:16\t0.129949\t0.928\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(tsv_content)
            f.flush()
            tmp_path = f.name
        try:
            rows = load_results(tmp_path)
            row = rows[0]
            self.assertIsInstance(row["timestamp"], str)
            self.assertIsInstance(row["avg_improvement"], float)
            self.assertIsInstance(row["training_time"], float)
        finally:
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# analyse_and_save
# ---------------------------------------------------------------------------

class TestAnalyseAndSave(unittest.TestCase):
    def _make_problem_dir(self, base_dir, problem_name, rows):
        """Create a problem directory with program.md and results.tsv."""
        problem_dir = Path(base_dir) / problem_name
        problem_dir.mkdir(parents=True)
        # Create program.md so discover_problems() finds it
        (problem_dir / "program.md").write_text("# test problem\n")
        # Write results.tsv
        results_path = problem_dir / "results.tsv"
        with open(results_path, "w") as f:
            f.write("timestamp\tavg_improvement\ttraining_time\n")
            for r in rows:
                f.write(f"{r['timestamp']}\t{r['avg_improvement']}\t{r['training_time']}\n")
        return problem_dir

    def test_saves_per_problem_and_aggregate_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scientist_dir = Path(tmpdir) / "scientist"
            scientist_dir.mkdir()
            self._make_problem_dir(scientist_dir, "prob_a", [_row(0.0), _row(0.05), _row(0.10)])
            self._make_problem_dir(scientist_dir, "prob_b", [_row(0.0), _row(0.03), _row(0.06)])

            output_path = os.path.join(tmpdir, "study_results.csv")
            with patch.object(scientist, "SCIENTIST_DIR", scientist_dir), \
                 patch.object(evaluate, "SCIENTIST_DIR", scientist_dir):
                all_stats = analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)

            self.assertIsNotNone(all_stats)
            self.assertIn("prob_a", all_stats)
            self.assertIn("prob_b", all_stats)
            self.assertIn("_aggregate", all_stats)

            # Verify CSV has 3 rows (prob_a, prob_b, _aggregate)
            import csv
            with open(output_path) as f:
                reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 3)
            problems_in_csv = [r["problem"] for r in reader]
            self.assertIn("prob_a", problems_in_csv)
            self.assertIn("prob_b", problems_in_csv)
            self.assertIn("_aggregate", problems_in_csv)
            self.assertEqual(set(reader[0].keys()), set(STUDY_FIELDS))

    def test_returns_none_with_too_few_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scientist_dir = Path(tmpdir) / "scientist"
            scientist_dir.mkdir()
            self._make_problem_dir(scientist_dir, "prob_a", [_row(0.0)])

            output_path = os.path.join(tmpdir, "study_results.csv")
            with patch.object(scientist, "SCIENTIST_DIR", scientist_dir), \
                 patch.object(evaluate, "SCIENTIST_DIR", scientist_dir):
                all_stats = analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)

            self.assertIsNone(all_stats)
            self.assertFalse(os.path.exists(output_path))

    def test_appends_multiple_studies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scientist_dir = Path(tmpdir) / "scientist"
            scientist_dir.mkdir()
            self._make_problem_dir(scientist_dir, "prob_a", [_row(0.0), _row(0.05)])

            output_path = os.path.join(tmpdir, "study_results.csv")
            with patch.object(scientist, "SCIENTIST_DIR", scientist_dir), \
                 patch.object(evaluate, "SCIENTIST_DIR", scientist_dir):
                analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)
                analyse_and_save(timestamp="2026-01-02T00:00:00", output_path=output_path)

            import csv
            with open(output_path) as f:
                reader = list(csv.DictReader(f))
            # 2 studies x 2 rows each (prob_a + _aggregate)
            self.assertEqual(len(reader), 4)
            timestamps = set(r["timestamp"] for r in reader)
            self.assertEqual(timestamps, {"2026-01-01T00:00:00", "2026-01-02T00:00:00"})

    def test_aggregate_is_mean_of_problems(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scientist_dir = Path(tmpdir) / "scientist"
            scientist_dir.mkdir()
            self._make_problem_dir(scientist_dir, "prob_a", [_row(0.0), _row(0.10)])
            self._make_problem_dir(scientist_dir, "prob_b", [_row(0.0), _row(0.06)])

            output_path = os.path.join(tmpdir, "study_results.csv")
            with patch.object(scientist, "SCIENTIST_DIR", scientist_dir), \
                 patch.object(evaluate, "SCIENTIST_DIR", scientist_dir):
                all_stats = analyse_and_save(timestamp="2026-01-01T00:00:00", output_path=output_path)

            agg = all_stats["_aggregate"]
            # Mean of total_improvement: (0.10 + 0.06) / 2 = 0.08
            self.assertAlmostEqual(agg["total_improvement"], 0.08)


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

    def test_with_problem_name(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(self._stats(), problem="tsp")
        self.assertIn("[tsp]", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
