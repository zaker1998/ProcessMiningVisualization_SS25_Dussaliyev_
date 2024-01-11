from mining_algorithms.fuzzy_mining import FuzzyMining
from api.pickle_save import pickle_load

class FuzzyGraphController():
    def __init__(self, workingDirectory, default_significance = 1.0, default_correlation = 0.3):
        super().__init__()
        self.model = None
        self.workingDirectory = workingDirectory
        self.significance = default_significance
        self.correlation = default_correlation

    def startMining(self, cases):
        self.model = FuzzyMining(cases)
        self.mine_and_draw(self.significance, self.correlation)

    def mine_and_draw(self, significance, correlation):
        graph = self.model.create_graph_with_graphviz(float(significance), float(correlation))
        graph.render(self.workingDirectory, format=('dot'))

        return graph
    def loadModel(self, file_path):
        self.model = pickle_load(file_path)
        # TODO
        return  file_path
    def getModel(self):
        # TODO logic of Fuzzy Miner
        return self.model