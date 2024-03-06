import unittest
from graphs.visualization.base_graph import BaseGraph, Node, Edge


class TestNode(unittest.TestCase):

    def test_node_creation_without_label(self):
        node = Node("1")
        self.assertEqual(node.get_label(), "1")
        self.assertEqual(node.get_label(), "1")

    def test_node_creation_with_number_as_id(self):
        node = Node(1)
        self.assertEqual(node.get_id(), "1")

    def test_node_creation_with_additional_data(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data(), data)

    def test_node_creation_with_label(self):
        node = Node(1, "node1")
        self.assertEqual(node.get_label(), "node1")

    def test_node_get_data_from_correct_key(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data_from_key("color"), "red")
        self.assertEqual(node.get_data_from_key("shape"), "circle")

    def test_node_get_data_from_incorrect_key(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data_from_key("size"), None)


if __name__ == "__main__":
    unittest.main()
