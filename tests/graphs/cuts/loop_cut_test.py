import unittest
from graphs.dfg import DFG
from graphs.cuts import loop_cut


class TestLoopCut(unittest.TestCase):

    def test_loop_cut_with_partitions_of_size_1(self):
        log = [["A", "B", "A", "B", "A", "B", "A"]]
        dfg = DFG(log)
        cuts = loop_cut(dfg)

        self.assertEqual(len(cuts), 2)

        self.assertEqual(cuts[0], {"A"})
        self.assertEqual(cuts[1], {"B"})

    def test_loop_cut_returns_None_without_cut(self):
        log = [["A", "B", "C", "D", "E", "F"]]
        dfg = DFG(log)
        cuts = loop_cut(dfg)

        self.assertIsNone(cuts)


if __name__ == "__main__":
    unittest.main()
