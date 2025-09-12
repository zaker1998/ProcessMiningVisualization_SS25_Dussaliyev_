import unittest
import numpy as np
from typing import Dict, Tuple
from mining_algorithms.base_mining import BaseMining


class TestBaseMining(unittest.TestCase):
    """Test cases for BaseMining functionality."""

    def setUp(self):
        """Set up test data."""
        self.simple_log = {
            ('A', 'B', 'C'): 10,
            ('A', 'C', 'B'): 5,
            ('A', 'B'): 3,
        }
        
        self.complex_log = {
            ('Register', 'Examine', 'Check', 'Decide'): 20,
            ('Register', 'Examine', 'Decide'): 15,
            ('Register', 'Check', 'Decide'): 10,
            ('Register', 'Examine', 'Check', 'Decide', 'Notify'): 8,
            ('Start', 'Process', 'End'): 5,
        }
        
        self.empty_trace_log = {
            (): 2,
            ('A',): 3,
            ('A', 'B'): 5,
        }

    def test_event_extraction(self):
        """Test extraction of events and their frequencies."""
        base_mining = BaseMining(self.simple_log)
        
        # Check extracted events
        expected_events = {'A', 'B', 'C'}
        self.assertEqual(set(base_mining.events), expected_events)
        
        # Check event frequencies
        expected_frequencies = {'A': 18, 'B': 18, 'C': 15}
        self.assertEqual(base_mining.appearance_frequency, expected_frequencies)

    def test_event_positions(self):
        """Test event position mapping."""
        base_mining = BaseMining(self.simple_log)
        
        # Ensure all events have unique positions
        positions = set(base_mining.event_positions.values())
        self.assertEqual(len(positions), len(base_mining.events))
        
        # Ensure all events are mapped
        for event in base_mining.events:
            self.assertIn(event, base_mining.event_positions)

    def test_succession_matrix_creation(self):
        """Test directly-follows matrix creation."""
        base_mining = BaseMining(self.simple_log)
        
        # Check matrix dimensions
        n_events = len(base_mining.events)
        self.assertEqual(base_mining.succession_matrix.shape, (n_events, n_events))
        
        # Check specific transitions
        pos_A = base_mining.event_positions['A']
        pos_B = base_mining.event_positions['B']
        pos_C = base_mining.event_positions['C']
        
        # A->B: appears in trace 1 (10 times) and trace 3 (3 times) = 13
        # A->C: appears in trace 2 (5 times) = 5
        # B->C: appears in trace 1 (10 times) = 10
        # C->B: appears in trace 2 (5 times) = 5
        
        self.assertEqual(base_mining.succession_matrix[pos_A, pos_B], 13)
        self.assertEqual(base_mining.succession_matrix[pos_A, pos_C], 5)
        self.assertEqual(base_mining.succession_matrix[pos_B, pos_C], 10)
        self.assertEqual(base_mining.succession_matrix[pos_C, pos_B], 5)

    def test_start_end_nodes(self):
        """Test identification of start and end nodes."""
        base_mining = BaseMining(self.complex_log)
        
        expected_start_nodes = {'Register', 'Start'}
        expected_end_nodes = {'Decide', 'End', 'Notify'}
        
        self.assertEqual(base_mining.start_nodes, expected_start_nodes)
        self.assertEqual(base_mining.end_nodes, expected_end_nodes)

    def test_empty_traces_handling(self):
        """Test handling of logs with empty traces."""
        base_mining = BaseMining(self.empty_trace_log)
        
        # Empty traces should not affect start/end node detection
        expected_start_nodes = {'A'}
        expected_end_nodes = {'A', 'B'}
        
        self.assertEqual(base_mining.start_nodes, expected_start_nodes)
        self.assertEqual(base_mining.end_nodes, expected_end_nodes)

    def test_events_to_remove_threshold(self):
        """Test event filtering based on frequency threshold."""
        base_mining = BaseMining(self.simple_log)
        
        # With threshold 0.5, should remove events with freq < 0.5 * max_freq
        # max_freq = 18 (A and B), so threshold = 9
        # A(18), B(18) and C(15) should all remain, none should be removed
        events_to_remove = base_mining.get_events_to_remove(0.5)
        self.assertEqual(len(events_to_remove), 0)
        
        # With threshold 0.9, should remove events with freq < 0.9 * 18 = 16.2
        # Only A(18) and B(18) should remain, C(15) should be removed
        events_to_remove = base_mining.get_events_to_remove(0.9)
        self.assertEqual(events_to_remove, {'C'})

    def test_threshold_boundary_values(self):
        """Test threshold clamping for boundary values."""
        base_mining = BaseMining(self.simple_log)
        
        # Test threshold > 1.0 (should be clamped to 1.0)
        events_to_remove = base_mining.get_events_to_remove(1.5)
        expected = base_mining.get_events_to_remove(1.0)
        self.assertEqual(events_to_remove, expected)
        
        # Test threshold < 0.0 (should be clamped to 0.0)
        events_to_remove = base_mining.get_events_to_remove(-0.5)
        expected = base_mining.get_events_to_remove(0.0)
        self.assertEqual(events_to_remove, expected)

    def test_minimum_traces_frequency(self):
        """Test calculation of minimum trace frequency threshold."""
        base_mining = BaseMining(self.simple_log)
        
        # max trace frequency is 10, so threshold 0.5 should give 5
        min_freq = base_mining.calulate_minimum_traces_frequency(0.5)
        self.assertEqual(min_freq, 5)
        
        # threshold 0.3 should give round(10 * 0.3) = 3
        min_freq = base_mining.calulate_minimum_traces_frequency(0.3)
        self.assertEqual(min_freq, 3)

    def test_node_size_calculation(self):
        """Test node size calculation for visualization."""
        base_mining = BaseMining(self.simple_log)
        
        # Test for each event
        for event in base_mining.events:
            width, height = base_mining.calulate_node_size(event)
            
            # Width should be positive and greater than min_node_size
            self.assertGreater(width, 0)
            self.assertGreaterEqual(width, base_mining.min_node_size)
            
            # Height should be width/3
            self.assertAlmostEqual(height, width / 3, places=5)

    def test_scale_factor_calculation(self):
        """Test scale factor calculation for nodes."""
        base_mining = BaseMining(self.simple_log)
        
        for event in base_mining.events:
            scale_factor = base_mining.get_scale_factor(event)
            self.assertGreater(scale_factor, 0)
            
        # Test with non-existent event (should return 1.0)
        scale_factor = base_mining.get_scale_factor('NonExistent')
        self.assertEqual(scale_factor, 1.0)

    def test_empty_log_handling(self):
        """Test handling of empty logs."""
        empty_log = {}
        base_mining = BaseMining(empty_log)
        
        self.assertEqual(len(base_mining.events), 0)
        self.assertEqual(len(base_mining.appearance_frequency), 0)
        self.assertEqual(base_mining.succession_matrix.shape, (0, 0))
        self.assertEqual(len(base_mining.start_nodes), 0)
        self.assertEqual(len(base_mining.end_nodes), 0)
        
        # Test threshold calculations with empty log
        min_freq = base_mining.calulate_minimum_traces_frequency(0.5)
        self.assertEqual(min_freq, 0)
        
        events_to_remove = base_mining.get_events_to_remove(0.5)
        self.assertEqual(len(events_to_remove), 0)

    def test_single_activity_log(self):
        """Test handling of logs with single activities."""
        single_activity_log = {('A',): 5}
        base_mining = BaseMining(single_activity_log)
        
        self.assertEqual(base_mining.events, ['A'])
        self.assertEqual(base_mining.appearance_frequency, {'A': 5})
        self.assertEqual(base_mining.succession_matrix.shape, (1, 1))
        self.assertEqual(base_mining.succession_matrix[0, 0], 0)  # No self-transitions
        self.assertEqual(base_mining.start_nodes, {'A'})
        self.assertEqual(base_mining.end_nodes, {'A'})

    def test_succession_matrix_with_self_loops(self):
        """Test succession matrix with repeated activities in traces."""
        loop_log = {
            ('A', 'A', 'B'): 3,
            ('A', 'B', 'A'): 2,
        }
        base_mining = BaseMining(loop_log)
        
        pos_A = base_mining.event_positions['A']
        pos_B = base_mining.event_positions['B']
        
        # A->A: appears 3 times in first trace
        self.assertEqual(base_mining.succession_matrix[pos_A, pos_A], 3)
        
        # A->B: appears 3 times in first trace + 2 times in second trace = 5
        self.assertEqual(base_mining.succession_matrix[pos_A, pos_B], 5)
        
        # B->A: appears 2 times in second trace
        self.assertEqual(base_mining.succession_matrix[pos_B, pos_A], 2)


if __name__ == '__main__':
    unittest.main() 