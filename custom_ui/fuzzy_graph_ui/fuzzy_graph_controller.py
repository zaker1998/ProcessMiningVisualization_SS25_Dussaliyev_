from mining_algorithms.fuzzy_mining import FuzzyMining
from api.pickle_save import pickle_load

class FuzzyGraphController():
    def __init__(self, workingDirectory, default_significance = 1, default_correlation = 0.5):# instead of dependency_threshold & min_frequency after workingDirectory I have to add my required variables for fuzzy mining algorithm
        super().__init__()
        self.model = None
        self.workingDirectory = workingDirectory
        self.default_significance = default_significance
        self.default_correlation = default_correlation

    def startMining(self, cases):
        return
    def loadModel(self, file_path):
        self.model = pickle_load(file_path)
        # self.create_de
        return  file_path