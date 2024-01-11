from mining_algorithms.fuzzy_mining import FuzzyMining
from api.pickle_save import pickle_load

class FuzzyGraphController():
    def __init__(self, workingDirectory, default_significance = 1, default_correlation = 0.5):
        super().__init__()
        self.model = None
        self.workingDirectory = workingDirectory
        self.significance = default_significance
        self.correlation = default_correlation

    def startMining(self, cases):
        self.model = FuzzyMining(cases)

        # graph = self.model.get_graphviz(dependency, correlation)
        # graph.render(self.workingDirectory, format = 'dot')
        #self.model.calculate_correlation_dependency_matrix(self.correlation)
        #self.model.calculate_significance_dependency(self.significance)

    def loadModel(self, file_path):
        self.model = pickle_load(file_path)
        # TODO
        return  file_path
    def getModel(self):
        # TODO logic of Fuzzy Miner
        return self.model