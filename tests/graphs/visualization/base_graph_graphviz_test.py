import unittest
from graphs.visualization.base_graph import BaseGraph
import re


def get_node_strings(graphviz_string):
    return re.findall(r"\w+ \[.*\]", graphviz_string)


def get_edge_strings(graphviz_string):
    return re.findall(r"\w+ -> \w+ \[.*\]", graphviz_string)


class TestBaseGraphGraphvizConverstion(unittest.TestCase):
    def test_directed_graph_to_graphviz_conversion(self):
        graph = BaseGraph()
        graphviz_string = graph.get_graphviz_string()
        self.assertRegex(graphviz_string, r"digraph {\s*}\s*")

    def test_undirected_graph_to_graphviz_conversion(self):
        graph = BaseGraph(directed=False)
        graphviz_string = graph.get_graphviz_string()
        self.assertRegex(graphviz_string, r"graph {\s*}\s*")

    def test_directed_graph_with_nodes_to_graphviz_conversion(self):
        graph = BaseGraph()
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)
        for node in graph.get_nodes():
            self.assertIn(f"{node.id} [label={node.id}]", nodes_string)

    def test_graph_conversion_with_node_labels(self):
        graph = BaseGraph()
        graph.add_node(1, label="node1")
        graph.add_node(2, label="node2")
        graph.add_node(3, label="node3")
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)
        for node in graph.get_nodes():
            self.assertIn(f"{node.id} [label={node.label}]", nodes_string)

    def test_graph_conversion_with_words_as_ids(self):
        graph = BaseGraph()
        graph.add_node("one", label="node1")
        graph.add_node("two", label="node2")
        graph.add_node("three", label="node3")
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)
        for node in graph.get_nodes():
            self.assertIn(f"{node.id} [label={node.label}]", nodes_string)

    def test_graph_conversion_with_nodes_and_attributes(self):
        graph = BaseGraph()
        colors = ["red", "green", "blue"]

        graph.add_node(1, label="node1", color="red")
        graph.add_node(2, label="node2", color="green")
        graph.add_node(3, label="node3", color="blue")
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)
        for node, color in zip(graph.get_nodes(), colors):
            self.assertIn(f"{node.id} [label={node.label} color={color}]", nodes_string)

    def test_graph_conversion_with_graph_attributes(self):
        graph = BaseGraph(rankdir="LR")
        graphviz_string = graph.get_graphviz_string()
        self.assertIn(f"graph [rankdir=LR]", graphviz_string)

    def test_graph_conversion_with_edges(self):
        graph = BaseGraph()
        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        graph.add_edge(3, 1)
        graphviz_string = graph.get_graphviz_string()
        edges_string = get_edge_strings(graphviz_string)
        for edge in graph.get_edges():
            self.assertIn(
                f"{edge.source} -> {edge.destination} [label=1]", edges_string
            )

    def test_graph_conversion_with_edges_and_attributes(self):
        graph = BaseGraph()
        colors = ["red", "green", "blue"]
        graph.add_edge(1, 2, color="red")
        graph.add_edge(2, 3, color="green")
        graph.add_edge(3, 1, color="blue")
        graphviz_string = graph.get_graphviz_string()
        edges_string = get_edge_strings(graphviz_string)
        for edge, color in zip(graph.get_edges(), colors):
            self.assertIn(
                f"{edge.source} -> {edge.destination} [label=1 color={color}]",
                edges_string,
            )


if __name__ == "__main__":
    unittest.main()
