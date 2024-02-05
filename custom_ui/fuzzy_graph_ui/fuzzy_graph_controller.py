from mining_algorithms.fuzzy_mining import FuzzyMining
from api.pickle_save import pickle_load

class FuzzyGraphController():
    def __init__(self, workingDirectory, default_significance = 0.0, default_edge_cutoff = 0.4, default_utility_ration = 0.5):
        super().__init__()
        self.model = None
        self.workingDirectory = workingDirectory
        self.significance = default_significance
        self.edge_cutoff = default_edge_cutoff
        self.utility_ration = default_utility_ration
        #self.correlation = default_correlation

    def startMining(self, cases):
        self.model = FuzzyMining(cases)
        self.mine_and_draw(self.significance, self.edge_cutoff, self.utility_ration)

    def mine_and_draw(self, significance, edge_cutoff, utility_ration):
        graph = self.model.create_graph_with_graphviz(float(significance), float(edge_cutoff), float(utility_ration))
        graph.render(self.workingDirectory, format=('dot'))

        return graph
    def loadModel(self, file_path):
        self.model = pickle_load(file_path)
        self.mine_and_draw(0.0, 0.4, 0.5)
        return file_path
    def getModel(self):
        return self.model