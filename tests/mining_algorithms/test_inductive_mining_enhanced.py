import unittest
from unittest.mock import Mock, patch
from mining_algorithms.inductive_mining import InductiveMining
from mining_algorithms.process_tree import ProcessTreeNode, Operator


def isProcessTreeEqual(tree1, tree2):
    """Enhanced process tree equality checker from original tests."""
    if type(tree1) != type(tree2):
        return False

    if isinstance(tree1, str) or isinstance(tree1, int):
        return tree1 == tree2

    if not isinstance(tree1, tuple):
        raise Exception("Invalid tree type")

    if len(tree1) != len(tree2):
        return False

    operation = tree1[0]
    if operation != tree2[0]:
        return False

    # ordered cuts first
    if operation == "seq":
        return all(isProcessTreeEqual(tree1[i], tree2[i]) for i in range(1, len(tree1)))
    if operation == "loop":
        if not isProcessTreeEqual(tree1[1], tree2[1]):
            return False

    for i in range(1, len(tree1)):
        foundEqual = False
        for j in range(1, len(tree2)):
            if isProcessTreeEqual(tree1[i], tree2[j]):
                foundEqual = True
                break
        if not foundEqual:
            return False

    return True


class TestInductiveMiningEnhanced(unittest.TestCase):
    """Enhanced test cases for InductiveMining functionality."""

    def setUp(self):
        """Set up test data."""
        # Basic sequential process
        self.sequential_log = {
            ('A', 'B', 'C'): 10,
        }
        
        # Parallel process
        self.parallel_log = {
            ('A', 'B', 'C'): 5,
            ('A', 'C', 'B'): 5,
        }
        
        # Choice process
        self.choice_log = {
            ('A', 'B'): 10,
            ('A', 'C'): 10,
        }
        
        # Loop process
        self.loop_log = {
            ('A', 'B', 'A', 'B'): 5,
            ('A', 'B'): 3,
        }
        
        # Complex process with multiple cuts
        self.complex_log = {
            ('Start', 'Task1', 'Task2', 'End'): 20,
            ('Start', 'Task2', 'Task1', 'End'): 15,
            ('Start', 'Task3', 'End'): 10,
        }
        
        # Noisy log for filtering tests
        self.noisy_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'C', 'B'): 80,
            ('A', 'B'): 60,
            ('A', 'X', 'C'): 2,  # Noise: rare activity X
            ('Y', 'B', 'C'): 1,  # Noise: rare start Y
        }

    def test_initialization(self):
        """Test InductiveMining initialization."""
        mining = InductiveMining(self.sequential_log)
        
        # Check inherited properties
        self.assertEqual(mining.log, self.sequential_log)
        self.assertIsNotNone(mining.events)
        self.assertIsNotNone(mining.succession_matrix)
        
        # Check InductiveMining specific properties
        self.assertEqual(mining.activity_threshold, 0.0)
        self.assertEqual(mining.traces_threshold, 0.2)
        self.assertEqual(mining.max_recursion_depth, 100)
        self.assertEqual(mining.current_depth, 0)

    def test_simple_sequential_cut(self):
        """Test discovery of sequential cuts."""
        mining = InductiveMining(self.sequential_log)
        result = mining.inductive_mining(self.sequential_log)
        expected = ("seq", "A", "B", "C")
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_parallel_cut_discovery(self):
        """Test discovery of parallel cuts."""
        mining = InductiveMining(self.parallel_log)
        result = mining.inductive_mining(self.parallel_log)
        # Result should be seq(A, par(B, C)) since A must come first
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_exclusive_choice_cut(self):
        """Test discovery of exclusive choice cuts."""
        mining = InductiveMining(self.choice_log)
        result = mining.inductive_mining(self.choice_log)
        # Should be seq(A, xor(B, C))
        expected = ("seq", "A", ("xor", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_loop_cut_discovery(self):
        """Test discovery of loop cuts."""
        loop_log = {('A',): 5, ('A', 'A'): 3, ('A', 'A', 'A'): 2}
        mining = InductiveMining(loop_log)
        result = mining.inductive_mining(loop_log)
        expected = ("loop", "A", "tau")
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_empty_log_handling(self):
        """Test handling of empty logs."""
        mining = InductiveMining({})
        result = mining.inductive_mining({})
        # Empty log should return tau
        self.assertEqual(result, "tau")

    def test_single_activity_log(self):
        """Test handling of logs with single activity."""
        single_log = {('A',): 10}
        mining = InductiveMining(single_log)
        result = mining.inductive_mining(single_log)
        self.assertEqual(result, "A")

    def test_fallthrough_cases(self):
        """Test fallthrough to flower model."""
        # Create a log that should fallthrough
        chaotic_log = {
            ('A', 'B', 'C'): 1,
            ('B', 'C', 'A'): 1,
            ('C', 'A', 'B'): 1,
        }
        mining = InductiveMining(chaotic_log)
        result = mining.inductive_mining(chaotic_log)
        
        # Should fallthrough to flower model: loop(tau, A, B, C)
        expected = ("loop", "tau", "A", "B", "C")
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_activity_threshold_filtering(self):
        """Test filtering with activity thresholds."""
        mining = InductiveMining(self.noisy_log)
        
        # With high activity threshold, rare activities should be filtered
        mining.generate_graph(activity_threshold=0.5, traces_threshold=0.0)
        
        # Check that rare activities are identified for removal
        events_to_remove = mining.get_events_to_remove(0.5)
        self.assertIn('X', events_to_remove)  # Rare activity
        self.assertIn('Y', events_to_remove)  # Rare activity

    def test_trace_threshold_filtering(self):
        """Test filtering with trace thresholds."""
        mining = InductiveMining(self.noisy_log)
        
        # Calculate minimum frequency for filtering
        min_freq = mining.calulate_minimum_traces_frequency(0.5)
        expected_min = 50  # 0.5 * max frequency (100)
        self.assertEqual(min_freq, expected_min)

    def test_graph_generation(self):
        """Test complete graph generation process."""
        mining = InductiveMining(self.sequential_log)
        
        # Generate graph with thresholds
        mining.generate_graph(activity_threshold=0.0, traces_threshold=0.0)
        
        # Check that graph is generated
        graph = mining.get_graph()
        self.assertIsNotNone(graph)

    def test_recursion_depth_protection(self):
        """Test protection against excessive recursion."""
        mining = InductiveMining(self.sequential_log)
        mining.max_recursion_depth = 2  # Set very low limit
        
        # This should not cause infinite recursion
        result = mining.inductive_mining(self.sequential_log)
        self.assertIsNotNone(result)

    def test_cached_filtered_log(self):
        """Test that filtered logs are cached properly."""
        mining = InductiveMining(self.noisy_log)
        
        # Generate graph twice with same parameters
        mining.generate_graph(activity_threshold=0.1, traces_threshold=0.1)
        first_filtered_log = mining.filtered_log
        
        mining.generate_graph(activity_threshold=0.1, traces_threshold=0.1)
        second_filtered_log = mining.filtered_log
        
        # Should be the same cached result
        self.assertEqual(first_filtered_log, second_filtered_log)

    def test_different_log_patterns(self):
        """Test mining with various log patterns."""
        test_cases = [
            # Simple sequence
            ({('A', 'B', 'C'): 1}, ("seq", "A", "B", "C")),
            
            # Simple choice after start
            ({('A', 'B'): 1, ('A', 'C'): 1}, ("seq", "A", ("xor", "B", "C"))),
            
            # Activities in parallel after start
            ({('A', 'B', 'C'): 1, ('A', 'C', 'B'): 1}, ("seq", "A", ("par", "B", "C"))),
        ]
        
        for log, expected in test_cases:
            with self.subTest(log=log):
                mining = InductiveMining(log)
                result = mining.inductive_mining(log)
                self.assertTrue(isProcessTreeEqual(result, expected))

    def test_complex_nested_structure(self):
        """Test mining of complex nested process structures."""
        # This matches a test case from original tests
        complex_log = {
            (1, 2, 3, 4): 2,
            (1, 3, 2, 4): 5,
            (1, 2, 3, 5, 6, 2, 3, 4): 3,
            (1, 3, 2, 5, 6, 3, 2, 4): 1,
        }
        
        mining = InductiveMining(complex_log)
        result = mining.inductive_mining(complex_log)
        
        expected = ("seq", 1, ("loop", ("par", 2, 3), ("seq", 5, 6)), 4)
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_process_tree_node_integration(self):
        """Test integration with ProcessTreeNode."""
        mining = InductiveMining(self.sequential_log)
        
        # Test internal process tree creation
        tree_node = mining._create_tree_node("seq", ["A", "B", "C"])
        self.assertIsInstance(tree_node, ProcessTreeNode)
        self.assertEqual(tree_node.operator, Operator.SEQUENCE)
        
        # Test tuple conversion
        tuple_result = tree_node.to_tuple()
        expected = ("seq", "A", "B", "C")
        self.assertEqual(tuple_result, expected)

    def test_node_size_calculation(self):
        """Test node size calculations for visualization."""
        mining = InductiveMining(self.noisy_log)
        
        # Test size calculation for different activities
        for activity in ['A', 'B', 'C']:
            width, height = mining.calulate_node_size(activity)
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            self.assertEqual(height, width / 3)  # Height should be width/3

    def test_error_handling(self):
        """Test error handling in mining process."""
        # Test with invalid log structure
        mining = InductiveMining(self.sequential_log)
        
        # Mining should handle unexpected situations gracefully
        result = mining.inductive_mining(None)
        # Should return some valid result or handle gracefully
        self.assertIsNotNone(result)

    def test_cut_calculation_method(self):
        """Test the cut calculation method."""
        mining = InductiveMining(self.parallel_log)
        
        # Test cut calculation directly
        cut_result = mining.calculate_cut(self.parallel_log)
        self.assertIsNotNone(cut_result)
        
        # Should return (operator, sublogs)
        if cut_result:
            operator, sublogs = cut_result
            self.assertIsInstance(operator, str)
            self.assertIsInstance(sublogs, list)

    def test_tau_handling(self):
        """Test proper handling of tau (silent activity)."""
        tau_log = {(): 5, ('A',): 10}  # Empty trace represents tau
        mining = InductiveMining(tau_log)
        result = mining.inductive_mining(tau_log)
        
        # Should handle tau appropriately in the result
        self.assertIsNotNone(result)
        
        # Result should contain tau or be wrapped with xor including tau
        result_str = str(result)
        self.assertTrue("tau" in result_str or "xor" in result_str)

    @patch('mining_algorithms.inductive_mining.logger')
    def test_logging_integration(self, mock_logger):
        """Test that logging is properly integrated."""
        mining = InductiveMining(self.sequential_log)
        mining.generate_graph(activity_threshold=0.0, traces_threshold=0.0)
        
        # Verify that logger methods were called
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)

    def test_threshold_edge_cases(self):
        """Test edge cases with threshold values."""
        mining = InductiveMining(self.noisy_log)
        
        # Test with threshold = 0.0 (no filtering)
        events_removed = mining.get_events_to_remove(0.0)
        self.assertEqual(len(events_removed), 0)
        
        # Test with threshold = 1.0 (remove everything except max frequency)
        events_removed = mining.get_events_to_remove(1.0)
        max_freq = max(mining.appearance_frequency.values())
        expected_remaining = [e for e, f in mining.appearance_frequency.items() if f == max_freq]
        expected_removed = set(mining.events) - set(expected_remaining)
        self.assertEqual(events_removed, expected_removed)


if __name__ == '__main__':
    unittest.main() 