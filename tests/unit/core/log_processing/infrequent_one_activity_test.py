import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import unittest
from src.core.log_processing.splits_imf import is_single_activity_frequent, _optimal_sequence_split
from parameterized import parameterized


class TestIsSingleActivityFrequent(unittest.TestCase):
    """
    Tests for is_single_activity_frequent function.
    
    Paper Reference (Section 3.2):
    "a is only discovered by IMi if the average number of occurrences per trace 
    of a in the log is close enough to 1, dependent on the relative threshold k."
    
    Bounds: lower_bound = 1 - k, upper_bound = 1 / (1 - k)
    Activity is frequent if: lower_bound <= avg <= upper_bound
    """
    
    @parameterized.expand([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    def test_one_frequent_activity(self, noise_threshold):
        """Single activity appearing once per trace should be frequent (avg = 1.0)."""
        log = {("a",): 5}

        is_frequent = is_single_activity_frequent(log, noise_threshold)

        self.assertTrue(is_frequent)

    @parameterized.expand([
        (0.0, False),  # lower_bound=1.0, avg=0.024 < 1.0
        (0.1, False),  # lower_bound=0.9, avg=0.024 < 0.9
        (0.5, False),  # lower_bound=0.5, avg=0.024 < 0.5
        (0.9, False),  # lower_bound=0.1, avg=0.024 < 0.1
        (0.98, True),  # lower_bound=0.02, avg=0.024 >= 0.02
        (1.0, True),   # lower_bound=0.0, avg=0.024 >= 0.0
    ])
    def test_empty_traces_dominate(self, noise_threshold, expected):
        """
        Log: 5 traces with 'a', 200 empty traces
        avg = 5/(5+200) = 0.024
        Should be infrequent if avg < lower_bound (1 - k)
        """
        log = {
            ("a",): 5,
            tuple(): 200,
        }

        is_frequent = is_single_activity_frequent(log, noise_threshold)

        self.assertEqual(expected, is_frequent)

    @parameterized.expand([
        (0.0, False),  # upper_bound=1.0, avg=1.98 > 1.0
        (0.1, False),  # upper_bound=1.11, avg=1.98 > 1.11
        (0.2, False),  # upper_bound=1.25, avg=1.98 > 1.25
        (0.3, False),  # upper_bound=1.43, avg=1.98 > 1.43
        (0.4, False),  # upper_bound=1.67, avg=1.98 > 1.67
        (0.5, True),   # upper_bound=2.0, avg=1.98 <= 2.0
        (0.6, True),   # upper_bound=2.5, avg=1.98 <= 2.5
        (0.9, True),   # upper_bound=10.0, avg=1.98 <= 10.0
    ])
    def test_activity_appearing_twice_per_trace(self, noise_threshold, expected):
        """
        Log: 5 traces with 'a' once, 200 traces with 'a' twice
        avg = (5*1 + 200*2) / (5+200) = 405/205 = 1.976
        Should be infrequent if avg > upper_bound (1/(1-k))
        """
        log = {
            ("a",): 5,
            ("a", "a"): 200,
        }

        is_frequent = is_single_activity_frequent(log, noise_threshold)

        self.assertEqual(expected, is_frequent)


class TestOptimalSequenceSplit(unittest.TestCase):
    """
    Tests for _optimal_sequence_split function.
    
    Paper Reference (Section 3.3 - →):
    "Behaviour that violates the → operator is the presence of events out of order 
    according to the subtrees. For instance, in the trace t2=⟨a, a, a, a, b, b, b, b, a, b⟩, 
    the last a occurs after a b, which violates the →. Filtering infrequent behaviour 
    is an optimisation problem: the trace is to be split in the least-events-removing way.
    In t2, the split ⟨a, a, a, a⟩ ∈ L1, ⟨b, b, b, b, b⟩ ∈ L2 discards the least events."
    """

    def test_paper_example_t2(self):
        """
        Paper example: t2=⟨a,a,a,a,b,b,b,b,a,b⟩
        Expected: ⟨a,a,a,a⟩ ∈ L1, ⟨b,b,b,b,b⟩ ∈ L2
        The 'a' after the first 'b' is removed as infrequent.
        """
        partitions = [{"a"}, {"b"}]
        trace = ("a", "a", "a", "a", "b", "b", "b", "b", "a", "b")

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual(
            [("a", "a", "a", "a"), ("b", "b", "b", "b", "b")],
            split_logs,
        )

    def test_example_from_paper_extended(self):
        """Extended version with more As and Bs."""
        partitions = [{"A"}, {"B"}]
        trace = (
            "A", "A", "A", "A", "A", "A", "A", "A", "A",
            "B", "B", "A",  # A after B violates sequence
            "B", "B", "B", "B", "B", "B", "B", "B", "B", "B",
        )

        split_logs = _optimal_sequence_split(trace, partitions)

        # The A after B should be removed
        self.assertEqual(
            [
                ("A", "A", "A", "A", "A", "A", "A", "A", "A"),
                ("B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B"),
            ],
            split_logs,
        )

    def test_multiple_violations(self):
        """Multiple As appearing after Bs should all be removed."""
        partitions = [{"A"}, {"B"}]
        trace = (
            "A", "A", "A", "A", "A", "A", "A", "A", "A",
            "B", "A", "A",  # Two As after B violate sequence
            "B", "B", "B", "B", "B", "B", "B", "B", "B", "B",
        )

        split_logs = _optimal_sequence_split(trace, partitions)

        # Both As after B should be removed
        self.assertEqual(
            [
                ("A", "A", "A", "A", "A", "A", "A", "A", "A"),
                ("B", "B", "B", "B", "B", "B", "B", "B", "B", "B", "B"),
            ],
            split_logs,
        )

    def test_three_partitions_with_violations(self):
        """
        Three partitions with out-of-order events.
        Trace: A, C, B, B, C
        - A → partition 0 ✓
        - C → partition 2 (forward jump, skipping B)
        - B, B → partition 1, but current is 2, so B < 2 → removed!
        - C → partition 2 ✓
        """
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("A", "C", "B", "B", "C")

        split_logs = _optimal_sequence_split(trace, partitions)

        # B's are removed because they appear after we moved to partition C
        self.assertEqual(
            [("A",), (), ("C", "C")],
            split_logs,
        )

    def test_no_violations_simple_sequence(self):
        """Trace with no violations should keep all events."""
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("A", "A", "B", "B", "C", "C")

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual(
            [("A", "A"), ("B", "B"), ("C", "C")],
            split_logs,
        )

    def test_empty_trace(self):
        """Empty trace should return empty tuples for each partition."""
        partitions = [{"A"}, {"B"}]
        trace = ()

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([(), ()], split_logs)

    def test_single_event_trace(self):
        """Single event trace should be assigned to correct partition."""
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("B",)

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([(), ("B",), ()], split_logs)

    def test_all_events_from_one_partition(self):
        """All events from one partition should stay together."""
        partitions = [{"A"}, {"B"}]
        trace = ("A", "A", "A", "A", "A")

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([("A", "A", "A", "A", "A"), ()], split_logs)

    def test_skip_partition(self):
        """Skipping a partition entirely should work."""
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("A", "A", "C", "C")  # Skip B entirely

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([("A", "A"), (), ("C", "C")], split_logs)

    def test_interleaved_violations(self):
        """
        Trace: A,B,A,B,A,B
        All events after first B that go back to A violate sequence.
        """
        partitions = [{"A"}, {"B"}]
        trace = ("A", "B", "A", "B", "A", "B")

        split_logs = _optimal_sequence_split(trace, partitions)

        # First A stays, then all Bs stay, middle As removed
        self.assertEqual([("A",), ("B", "B", "B")], split_logs)

    def test_multiple_events_per_partition(self):
        """Partitions can contain multiple event types."""
        partitions = [{"A", "X"}, {"B", "Y"}]
        trace = ("A", "X", "B", "Y", "A")  # Last A violates sequence

        split_logs = _optimal_sequence_split(trace, partitions)

        # Last A should be removed
        self.assertEqual([("A", "X"), ("B", "Y")], split_logs)

    def test_four_partitions(self):
        """Test with four partitions."""
        partitions = [{"A"}, {"B"}, {"C"}, {"D"}]
        trace = ("A", "B", "C", "D", "B")  # Last B violates sequence

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([("A",), ("B",), ("C",), ("D",)], split_logs)

    def test_complex_violations(self):
        """
        Complex case: A,A,B,B,A,A,C,C,B,B
        The A,A after B,B and the B,B after C,C should be removed.
        """
        partitions = [{"A"}, {"B"}, {"C"}]
        trace = ("A", "A", "B", "B", "A", "A", "C", "C", "B", "B")

        split_logs = _optimal_sequence_split(trace, partitions)

        # A,A after B,B removed, B,B after C,C removed
        self.assertEqual([("A", "A"), ("B", "B"), ("C", "C")], split_logs)

    def test_violation_at_start(self):
        """
        Trace starting with later partition event, earlier partition event follows.
        B,A,A,A - A comes after B started, so As should be removed.
        """
        partitions = [{"A"}, {"B"}]
        trace = ("B", "A", "A", "A")

        split_logs = _optimal_sequence_split(trace, partitions)

        # A events after B should be removed
        self.assertEqual([(), ("B",)], split_logs)

    def test_greedy_behavior(self):
        """
        The greedy algorithm removes events that go backward.
        A,B,B,A,A,A should keep A, then all Bs, then remove remaining As.
        """
        partitions = [{"A"}, {"B"}]
        trace = ("A", "B", "B", "A", "A", "A")

        split_logs = _optimal_sequence_split(trace, partitions)

        self.assertEqual([("A",), ("B", "B")], split_logs)


if __name__ == "__main__":
    unittest.main() 

