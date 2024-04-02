import unittest
from graphs.dfg import DFG
from graphs.cuts import sequence_cut


class TestSequenceCut(unittest.TestCase):

    def test_sequence_cut_with_partitions_of_size_1(self):
        log = [["A", "B", "C", "D", "E", "F"]]
        dfg = DFG(log)
        cuts = sequence_cut(dfg)

        self.assertEqual(len(cuts), len(log[0]))
        for i in range(len(log[0])):
            self.assertEqual(set(log[0][i]), cuts[i])

    def test_cut_with_skipped_partitions(self):
        log = [[1, 2, 3], [1, 3]]
        dfg = DFG(log)
        cuts = sequence_cut(dfg)

        self.assertEqual(len(cuts), 3)
        self.assertEqual(cuts[0], {1})
        self.assertEqual(cuts[1], {2})
        self.assertEqual(cuts[2], {3})


if __name__ == "__main__":
    unittest.main()
