from mining_algorithms.model import Model


class HeuristicMiningModel(Model):

    def __init__(self):
        self.max_frequency = None
        self.threshold = None
        self.frequency = None

    def get_threshold(self):
        return self.threshold

    def set_threshold(self, threshold):
        self.threshold = threshold

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency

    def get_max_frequency(self):
        return self.max_frequency

    def set_max_frequency(self, max_frequency):
        self.max_frequency = max_frequency
