class BaseMining:
    def __init__(self, log):
        self.log = log
        self.graph = None

    def get_graph(self):
        return self.graph
