import unittest
from graphs.visualization.base_graph import BaseGraph
import re


def get_node_strings(graphviz_string):
    return re.findall(r"\w+ \[.*\]", graphviz_string)


def get_edge_strings(graphviz_string):
    return re.findall(r"\w+ -> \w+ \[.*\]", graphviz_string)


def get_node_attributes(graphviz_string):
    return re.findall(r"node \[.*\]", graphviz_string)[0]


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

        graph.add_node(1, label="node1", node_attributes={"color": "red"})
        graph.add_node(2, label="node2", node_attributes={"color": "green"})
        graph.add_node(3, label="node3", node_attributes={"color": "blue"})
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)
        for node, color in zip(graph.get_nodes(), colors):
            self.assertIn(f"{node.id} [label={node.label} color={color}]", nodes_string)

    def test_graph_conversion_with_global_node_attributes(self):
        node_attr = {"color": "red"}
        graph = BaseGraph(global_node_attributes=node_attr)
        graphviz_string = graph.get_graphviz_string()
        node_attr_string = get_node_attributes(graphviz_string)
        self.assertEqual(node_attr_string, f"node [color={node_attr['color']}]")

    def test_graph_conversion_with_global_and_individual_node_attributes(self):
        node_attr = {"color": "red"}
        graph = BaseGraph(global_node_attributes=node_attr)
        graph.add_node(1, label="node1", node_attributes={"color": "blue"})
        graph.add_node(2, label="node2")
        graphviz_string = graph.get_graphviz_string()
        nodes_string = get_node_strings(graphviz_string)

        self.assertIn(f"node [color={node_attr['color']}]", nodes_string)
        self.assertIn("1 [label=node1 color=blue]", nodes_string)
        self.assertIn("2 [label=node2]", nodes_string)

    def test_graph_conversion_with_graph_attributes(self):
        graph_attr = {"rankdir": "LR"}
        graph = BaseGraph(graph_attributes=graph_attr)
        graphviz_string = graph.get_graphviz_string()
        self.assertIn(f"graph [rankdir={graph_attr['rankdir']}]", graphviz_string)

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
        graph.add_edge(1, 2, edge_attributes={"color": "red"})
        graph.add_edge(2, 3, edge_attributes={"color": "green"})
        graph.add_edge(3, 1, edge_attributes={"color": "blue"})
        graphviz_string = graph.get_graphviz_string()
        edges_string = get_edge_strings(graphviz_string)
        for edge, color in zip(graph.get_edges(), colors):
            self.assertIn(
                f"{edge.source} -> {edge.destination} [label=1 color={color}]",
                edges_string,
            )

    def test_graph_conversion_with_global_edge_attributes(self):
        edge_attr = {"color": "red"}
        graph = BaseGraph(global_edge_attributes=edge_attr)
        graph.add_edge(1, 2)
        graph.add_edge(2, 3, edge_attributes={"color": "green"})
        graphviz_string = graph.get_graphviz_string()
        edges_string = get_edge_strings(graphviz_string)
        self.assertEqual(
            f"edge [color={edge_attr['color']}]",
            re.findall(r"edge \[.*\]", graphviz_string)[0],
        )
        self.assertIn(f"1 -> 2 [label=1]", edges_string)
        self.assertIn(f"2 -> 3 [label=1 color=green]", edges_string)


if __name__ == "__main__":
    unittest.main()
