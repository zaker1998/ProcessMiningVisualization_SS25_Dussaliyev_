import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import unittest
from src.core.log_processing.splits_imf import _optimal_sequence_split


class TestOptimalSequenceLogSplit(unittest.TestCase):

    def test_example_from_paper(self):
        partitions = [{"A"}, {"B"}]
        trace = (
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "B",
            "B",
            "A",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
        )

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual(
            [
                ("A", "A", "A", "A", "A", "A", "A", "A", "A"),
                ("B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B"),
            ],
            split_logs,
        )

    def test_example_1(self):
        partitions = [{"A"}, {"B"}]
        trace = (
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "A",
            "B",
            "A",
            "A",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
            "B",
        )

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual(
            [
                ("A", "A", "A", "A", "A", "A", "A", "A", "A", "A", "A"),
                ("B", "B", "B", "B", "B", "B", "B", "B", "B", "B"),
            ],
            split_logs,
        )

    def test_example_2(self):
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("A", "C", "B", "B", "C")

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual(
            [("A",), ("B", "B"), ("C",)],
            split_logs,
        )


if __name__ == "__main__":
    unittest.main()
