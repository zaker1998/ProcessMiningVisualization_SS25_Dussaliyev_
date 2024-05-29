import unittest
from parameterized import parameterized
from analysis.predictions_model import PredictionModel

column_types_predictions_values = {
    "time": set(["time", "date"]),
    "event": set(["event", "activity", "action", "task", "operation"]),
    "case": set(["case", "process", "instance", "session"]),
}


class TestPredictionModel(unittest.TestCase):
    def setUp(self):
        self.prediction_model = PredictionModel(column_types_predictions_values)
