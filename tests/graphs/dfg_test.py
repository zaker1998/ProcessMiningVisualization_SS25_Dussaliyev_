import unittest
from graphs.dfg import DFG


class TestDFG(unittest.TestCase):

    def setUp(self):
        log = [["A", "B", "C"], ["A", "C", "B"]]
        self.dfg = DFG(log)

    def test_dfg_init(self):
        log = [["A", "B", "C"], ["A", "C", "B"]]
        dfg = DFG(log)
        self.assertEqual(self.dfg.nodes, {"A", "B", "C"})
        self.assertEqual(
            self.dfg.edges,
            {("A", "B"): 1, ("B", "C"): 1, ("A", "C"): 1, ("C", "B"): 1},
        )
        self.assertEqual(self.dfg.start_nodes, {"A"})
        self.assertEqual(self.dfg.end_nodes, {"B", "C"})

    def test_add_node(self):
        self.dfg.add_node("D")
        self.assertEqual(self.dfg.nodes, {"A", "B", "C", "D"})

    def test_add_edge(self):
        self.dfg.add_edge("C", "D")
        self.assertEqual(
            self.dfg.edges,
            {("A", "B"): 1, ("B", "C"): 1, ("A", "C"): 1, ("C", "B"): 1, ("C", "D"): 1},
        )

    def test_adding_existing_edge_increases_weight(self):
        self.dfg.add_edge("A", "B")
        self.assertEqual(
            self.dfg.edges,
            {("A", "B"): 2, ("B", "C"): 1, ("A", "C"): 1, ("C", "B"): 1},
        )

    def test_add_edge_with_weight(self):
        self.dfg.add_edge("C", "D", 3)
        self.assertEqual(
            self.dfg.edges,
            {("A", "B"): 1, ("B", "C"): 1, ("A", "C"): 1, ("C", "B"): 1, ("C", "D"): 3},
        )

    def test_add_edge_with_negative_weight(self):
        with self.assertRaises(ValueError):
            self.dfg.add_edge("C", "D", -3)

    def test_get_nodes(self):
        self.assertEqual(self.dfg.get_nodes(), {"A", "B", "C"})

    def test_get_edges(self):
        self.assertEqual(
            self.dfg.get_edges(),
            {("A", "B"): 1, ("B", "C"): 1, ("A", "C"): 1, ("C", "B"): 1},
        )

    def test_get_start_nodes(self):
        self.assertEqual(self.dfg.get_start_nodes(), {"A"})

    def test_get_end_nodes(self):
        self.assertEqual(self.dfg.get_end_nodes(), {"B", "C"})

    def test_is_in_start_nodes(self):
        self.assertTrue(self.dfg.is_in_start_nodes("A"))
        self.assertFalse(self.dfg.is_in_start_nodes("B"))
        self.assertFalse(self.dfg.is_in_start_nodes("C"))

    def test_is_in_end_nodes(self):
        self.assertFalse(self.dfg.is_in_end_nodes("A"))
        self.assertTrue(self.dfg.is_in_end_nodes("B"))
        self.assertTrue(self.dfg.is_in_end_nodes("C"))

    def test_contains_node(self):
        self.assertTrue(self.dfg.contains_node("A"))
        self.assertFalse(self.dfg.contains_node("D"))

    def test_contains_edge(self):
        self.assertTrue(self.dfg.contains_edge("A", "B"))
        self.assertFalse(self.dfg.contains_edge("B", "A"))

    def test_get_neighbours(self):
        self.assertEqual(self.dfg.get_neighbours("A"), ["B", "C"])
        self.assertEqual(self.dfg.get_neighbours("B"), ["C"])
        self.assertEqual(self.dfg.get_neighbours("C"), ["B"])


if __name__ == "__main__":
    unittest.main()
