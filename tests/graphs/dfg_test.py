import unittest
from graphs.dfg import DFG


class TestDFG(unittest.TestCase):

    def setUp(self):
        log = [["A", "B", "C"], ["A", "C", "B"]]
        self.dfg = DFG(log)

    def test_dfg_init(self):
        self.assertEqual(self.dfg.get_nodes(), {"A", "B", "C"})
        self.assertEqual(
            self.dfg.get_edges(),
            {("A", "B"), ("B", "C"), ("A", "C"), ("C", "B")},
        )
        self.assertEqual(self.dfg.get_start_nodes(), {"A"})
        self.assertEqual(self.dfg.get_end_nodes(), {"B", "C"})

    def test_add_node(self):
        self.dfg.add_node("D")
        self.assertEqual(self.dfg.get_nodes(), {"A", "B", "C", "D"})

    def test_add_edge(self):
        self.dfg.add_edge("C", "D")
        self.assertEqual(
            self.dfg.get_edges(),
            {("A", "B"), ("B", "C"), ("A", "C"), ("C", "B"), ("C", "D")},
        )

    def test_get_nodes(self):
        self.assertEqual(self.dfg.get_nodes(), {"A", "B", "C"})

    def test_get_edges(self):
        self.assertEqual(
            self.dfg.get_edges(),
            {("A", "B"), ("B", "C"), ("A", "C"), ("C", "B")},
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

    def test_connected_components_with(self):
        self.assertEqual(self.dfg.get_connected_components(), [{"A", "B", "C"}])

    def test_connected_components_does_ignore_directions(self):
        log = [["A", "B"], ["B", "C"], ["C", "A"], ["D", "E"], ["D", "A"]]
        dfg = DFG(log)

        self.assertEqual(dfg.get_connected_components(), [{"A", "B", "C", "D", "E"}])

    def test_connected_components_with_more_than_one_connected_component(self):
        self.dfg.add_edge("D", "E")

        connected_components = self.dfg.get_connected_components()
        self.assertIn({"D", "E"}, connected_components)
        self.assertIn({"A", "B", "C"}, connected_components)


if __name__ == "__main__":
    unittest.main()
