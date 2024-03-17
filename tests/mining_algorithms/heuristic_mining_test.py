"""
This unittest tests the integrity of the heuristic_graph_controller which holds the HeuristicMining Model.
"""

import unittest
from custom_ui.heuristic_graph_ui.heuristic_graph_controller import (
    HeuristicGraphController,
)
from graphs.visualization.base_graph import BaseGraph
from mining_algorithms.heuristic_mining import HeuristicMining
from api.csv_preprocessor import read
from collections import deque


class TestHeuristic(unittest.TestCase):

    def test_create_dependency_graph_using_preprocessed_txt(self):
        print("-------------- Running test.txt ----------------")
        self.__run_test_txt("test0")
        print("passed test 0")
        self.__run_test_txt("test1")
        print("passed test 1")
        self.__run_test_txt("test2")
        print("passed test 2")
        self.__run_test_txt("test3")
        print("passed test 3")
        print("---------------- test.txt passed! ----------------")

    def test_create_dependency_graph_using_test_csv(self):
        print("-------------- Running test_csv ----------------")
        self.__run_test_csv(0.5, 1)
        print("passed test 1")
        self.__run_test_csv(0.1, 1)
        print("passed test 2")
        self.__run_test_csv(0.9, 1)
        print("passed test 3")
        self.__run_test_csv(0.5, 10)
        print("passed test 4")
        print("---------------- test_csv passed! ----------------")

    def test_create_dependency_graph_using_CallcenterExample(self):
        print("-------------- Running large CallcenterExample ----------------")
        self.__run_CallcenterExample_csv(0.5, 1)
        print("---------------- CallcenterExample passed! ----------------")

    def test_loading_pickle_HeuristicMining_model(self):
        print("----------- Running pickle loading test ----------")
        print("(This test fails if you messed with the HeuristicMining class)")
        print("(Replace the pickle file with a new one if you did)")
        self.__run_pickle_loading_test("tests/testpickle/test_csv.pickle")
        print("---------------- pickle loading test passed! ----------------")

    # read test cases that are txt files for testing
    def __read_cases(self, filename):
        log = []
        # cwd = os.getcwd()
        # path = os.path.join(cwd, filename)
        with open(filename, "r") as f:
            for line in f.readlines():
                assert isinstance(line, str)
                log.append(list(line.split()))
        return log

    def __run_test_txt(self, filename):
        Controller = HeuristicGraphController("temp/graph_viz")
        Controller.startMining(self.__read_cases("tests/testlogs/" + filename + ".txt"))
        G = Controller.create_dependency_graph(0.5, 1)
        self.__check_graph_integrity(G)

    def __run_test_csv(self, threshold, min_freq):
        Controller = HeuristicGraphController("temp/graph_viz")
        Controller.startMining(read("tests/testcsv/test_csv.csv"))
        G = Controller.create_dependency_graph(
            threshold, min_freq
        )  # G is a HeuricticGraph/BaseGraph
        self.__check_graph_integrity(G)

    def __run_CallcenterExample_csv(self, threshold, min_freq):
        Controller = HeuristicGraphController("temp/graphviz")
        Controller.startMining(
            read(
                "tests/testcsv/CallcenterExample.csv",
                caseLabel="Service ID",
                eventLabel="Operation",
                timeLabel="Start Date",
            )
        )
        G = Controller.create_dependency_graph(
            threshold, min_freq
        )  # G is a HeuricticGraph/BaseGraph
        self.__check_graph_integrity(G)

    def __run_pickle_loading_test(self, pickleFile):
        Controller = HeuristicGraphController("temp/graph_viz")
        Controller.loadModel(pickleFile)

        self.assertIsInstance(Controller.getModel(), HeuristicMining)

        G = Controller.create_dependency_graph(0.2, 4)
        self.assertIsNotNone(G)

        max_frequency = Controller.get_max_frequency()
        self.assertIsNotNone(max_frequency)

        min_frequency = Controller.get_min_frequency()
        self.assertIsNotNone(min_frequency)

        threshold = Controller.get_threshold()
        self.assertIsNotNone(threshold)

    def __check_graph_integrity(self, graph: BaseGraph):
        self.assertTrue(graph.contains_node("Start"), "Start node not found.")
        self.assertTrue(graph.contains_node("End"), "End node not found.")

        # Check there is a 'start' node that connects to at least 1 other node
        self.assertTrue(
            len(list(filter(lambda edge: edge.source == "Start", graph.get_edges())))
            >= 1,
            "Start node does not connect to any other nodes.",
        )

        # Check if all nodes are reachable from the 'start' node
        reachable_nodes = set()
        queue = deque(["Start"])
        while queue:
            node = queue.popleft()
            reachable_nodes.add(node)
            for edge in graph.get_edges():
                if edge.source == node:
                    if edge.destination not in reachable_nodes:
                        queue.append(edge.destination)

        self.assertEqual(
            reachable_nodes,
            set(map(lambda node: node.id, graph.get_nodes())),
            "Not all nodes are reachable from the 'start' node.",
        )
