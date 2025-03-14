"""Unit tests for the Python report tool (run with: make test-py)."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.helpers import parse_books  # noqa: E402
from tools.report import average_copies, total_copies  # noqa: E402

DATA = os.path.join(ROOT, "data", "books.txt")
EXPECTED = os.path.join(ROOT, "tests", "expected_report.txt")


class ReportTests(unittest.TestCase):
    """Checks the totals printed by tools/report.py."""

    def setUp(self):
        self.books = parse_books(DATA)

    def test_parse_books_skips_comment_lines(self):
        self.assertEqual(len(self.books), 8)

    def test_total_copies(self):
        self.assertEqual(total_copies(self.books), 34)

    def test_total_copies_of_nothing_is_zero(self):
        self.assertEqual(total_copies([]), 0)

    def test_average_copies(self):
        self.assertAlmostEqual(average_copies(self.books), 4.25)

    def test_report_output_matches_expected_file(self):
        result = subprocess.run(
            [sys.executable, "-m", "tools.report", DATA],
            cwd=ROOT, stdout=subprocess.PIPE, universal_newlines=True, check=True,
        )
        with open(EXPECTED, encoding="utf-8") as handle:
            self.assertEqual(result.stdout, handle.read())


if __name__ == "__main__":
    unittest.main()
