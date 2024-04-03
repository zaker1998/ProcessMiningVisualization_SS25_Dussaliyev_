import unittest
from graphs.dfg import DFG
from graphs.cuts import parallel_cut


class TestParallelCut(unittest.TestCase):
    def test_no_cut_returns_none(self):
        log = [["A", "B", "C"], ["A", "B", "C"]]
        dfg = DFG(log)
        cuts = parallel_cut(dfg)

        self.assertIsNone(cuts)

    def test_cut_return_partitions(self):
        log = [["B", "C"], ["C", "B"]]
        dfg = DFG(log)
        cuts = parallel_cut(dfg)

        self.assertEqual(len(cuts), 2)
        self.assertIn({"B"}, cuts)
        self.assertIn({"C"}, cuts)

    def test_partitions_without_start_or_end_node_merge(self):
        log = [
            ["A", "B", "C"],
            ["A", "C", "B"],
            ["B", "A", "C"],
            ["B", "C", "A"],
        ]
        dfg = DFG(log)
        cuts = parallel_cut(dfg)

        self.assertEqual(len(cuts), 2)
        # C is merged with other nodes
        self.assertNotIn({"C"}, cuts)


if __name__ == "__main__":
    unittest.main()
