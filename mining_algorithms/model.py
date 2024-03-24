from graphs.visualization.base_graph import BaseGraph


class Model:
    cases = None
    graph: BaseGraph = None

    def get_cases(self):
        return self.cases

    def set_cases(self, cases) -> None:
        self.cases = cases

    def get_graph(self) -> BaseGraph:
        return self.graph

    def set_graph(self, graph: BaseGraph) -> None:
        self.graph = graph
