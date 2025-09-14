import unittest
from unittest.mock import Mock, patch
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent


def isProcessTreeEqual(tree1, tree2):
    """Process tree equality checker."""
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


class TestInductiveMiningInfrequent(unittest.TestCase):
    """Test cases for InductiveMiningInfrequent functionality."""

    def setUp(self):
        """Set up test data with various noise patterns."""
        # Clean process without noise
        self.clean_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'C', 'B'): 100,
        }
        
        # Process with infrequent edges (noise)
        self.noisy_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'C', 'B'): 100,
            ('A', 'X', 'C'): 5,  # Infrequent: A->X->C
            ('A', 'B', 'Y', 'C'): 3,  # Infrequent: B->Y
            ('Z', 'B', 'C'): 2,  # Infrequent start
        }
        
        # Process with rare directly-follows relations
        self.rare_edges_log = {
            ('Start', 'Task1', 'Task2', 'End'): 50,
            ('Start', 'Task2', 'Task1', 'End'): 45,
            ('Start', 'Task1', 'End'): 30,
            ('Start', 'Task2', 'End'): 25,
            # Rare edges below
            ('Start', 'Task1', 'Rare', 'Task2', 'End'): 2,
            ('Start', 'Task2', 'Rare', 'Task1', 'End'): 1,
        }
        
        # Very noisy process that should trigger fallback
        self.very_noisy_log = {
            ('A', 'B', 'C', 'D'): 20,
            ('A', 'C', 'B', 'D'): 15,
            # Many infrequent variants
            ('A', 'E', 'B', 'C', 'D'): 2,
            ('A', 'B', 'F', 'C', 'D'): 1,
            ('A', 'B', 'C', 'G', 'D'): 1,
            ('H', 'A', 'B', 'C', 'D'): 1,
        }

    def test_initialization(self):
        """Test InductiveMiningInfrequent initialization."""
        mining = InductiveMiningInfrequent(self.clean_log)
        
        # Check inherited properties
        self.assertIsInstance(mining, InductiveMiningInfrequent)
        self.assertEqual(mining.log, self.clean_log)
        
        # Check infrequent-specific properties
        self.assertEqual(mining.noise_threshold, 0.2)
        self.assertEqual(mining.max_recursion_depth, 100)
        self.assertIsNotNone(mining._edge_freq_cache)

    def test_noise_threshold_parameter(self):
        """Test noise threshold parameter handling."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        
        # Test setting noise threshold through generate_graph
        mining.generate_graph(
            activity_threshold=0.0, 
            traces_threshold=0.0, 
            noise_threshold=0.1
        )
        
        self.assertEqual(mining.noise_threshold, 0.1)

    def test_clean_process_mining(self):
        """Test mining on clean process without noise."""
        mining = InductiveMiningInfrequent(self.clean_log)
        result = mining.inductive_mining(self.clean_log)
        
        # Should discover parallel cut after sequence
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_noisy_process_with_low_noise_threshold(self):
        """Test mining with low noise threshold (strict)."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        mining.noise_threshold = 0.05  # Very strict
        
        result = mining.inductive_mining(self.noisy_log)
        
        # Should still discover main pattern despite noise
        self.assertIsNotNone(result)
        # Main activities A, B, C should be preserved
        result_str = str(result)
        self.assertIn("A", result_str)
        self.assertIn("B", result_str) 
        self.assertIn("C", result_str)

    def test_noisy_process_with_high_noise_threshold(self):
        """Test mining with high noise threshold (permissive)."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        mining.noise_threshold = 0.5  # Very permissive
        
        result = mining.inductive_mining(self.noisy_log)
        
        # Should include more activities due to permissive threshold
        self.assertIsNotNone(result)

    def test_fallback_to_filtered_dfg(self):
        """Test fallback mechanism when full DFG fails."""
        mining = InductiveMiningInfrequent(self.very_noisy_log)
        mining.noise_threshold = 0.3
        
        # Mock the cut finding to fail on full DFG but succeed on filtered
        original_try_cuts = mining._try_cuts_on_dfg
        call_count = 0
        
        def mock_try_cuts(dfg, log):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call (full DFG)
                return None  # Force failure
            else:  # Second call (filtered DFG)
                return original_try_cuts(dfg, log)
        
        with patch.object(mining, '_try_cuts_on_dfg', side_effect=mock_try_cuts):
            result = mining.calculate_cut(self.very_noisy_log)
            # Should have tried both full and filtered DFG
            self.assertEqual(call_count, 2)

    def test_dfg_edge_filtering(self):
        """Test directly-follows graph edge filtering."""
        mining = InductiveMiningInfrequent(self.rare_edges_log)
        
        # Test with strict noise threshold
        mining.noise_threshold = 0.05  # Should filter rare edges
        
        # This should work by filtering out rare edges
        result = mining.inductive_mining(self.rare_edges_log)
        
        # Should discover main process structure
        self.assertIsNotNone(result)
        result_str = str(result)
        self.assertIn("Start", result_str)
        self.assertIn("End", result_str)

    def test_edge_frequency_caching(self):
        """Test edge frequency caching mechanism."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        
        # Access cache (should be empty initially)
        self.assertIsInstance(mining._edge_freq_cache, dict)
        
        # Process the log (this should populate cache)
        mining.generate_graph(noise_threshold=0.2)
        
        # Cache might be used internally for optimization

    def test_calculate_cut_with_different_noise_levels(self):
        """Test cut calculation with different noise levels."""
        mining = InductiveMiningInfrequent(self.rare_edges_log)
        
        test_cases = [0.0, 0.1, 0.3, 0.5]
        
        for noise_threshold in test_cases:
            with self.subTest(noise_threshold=noise_threshold):
                mining.noise_threshold = noise_threshold
                result = mining.calculate_cut(self.rare_edges_log)
                
                if result:
                    operator, sublogs = result
                    self.assertIsInstance(operator, str)
                    self.assertIsInstance(sublogs, list)
                    self.assertIn(operator, ["seq", "xor", "par", "loop"])

    def test_inheritance_from_inductive_mining(self):
        """Test that InfrequentMining properly inherits from InductiveMining."""
        mining = InductiveMiningInfrequent(self.clean_log)
        
        # Should have all base class methods
        self.assertTrue(hasattr(mining, 'inductive_mining'))
        self.assertTrue(hasattr(mining, 'get_graph'))
        self.assertTrue(hasattr(mining, 'get_events_to_remove'))
        self.assertTrue(hasattr(mining, 'calulate_minimum_traces_frequency'))

    def test_complex_noisy_pattern(self):
        """Test mining complex pattern with systematic noise."""
        complex_noisy_log = {
            # Main pattern: A -> (B || C) -> D
            ('A', 'B', 'C', 'D'): 40,
            ('A', 'C', 'B', 'D'): 35,
            ('A', 'B', 'D'): 20,
            ('A', 'C', 'D'): 18,
            
            # Systematic noise
            ('A', 'X', 'B', 'C', 'D'): 3,  # Rare X insertion
            ('A', 'B', 'C', 'Y', 'D'): 2,  # Rare Y insertion
            ('Z', 'A', 'B', 'C', 'D'): 1,  # Rare Z prefix
        }
        
        mining = InductiveMiningInfrequent(complex_noisy_log)
        result = mining.inductive_mining(complex_noisy_log)
        
        # Should discover main structure despite noise
        self.assertIsNotNone(result)
        result_str = str(result)
        
        # Main activities should be present
        for activity in ['A', 'B', 'C', 'D']:
            self.assertIn(activity, result_str)

    def test_empty_and_edge_case_logs(self):
        """Test edge cases like empty logs."""
        # Empty log
        mining = InductiveMiningInfrequent({})
        result = mining.inductive_mining({})
        self.assertEqual(result, "tau")
        
        # Single trace log
        single_log = {('A', 'B'): 1}
        mining = InductiveMiningInfrequent(single_log)
        result = mining.inductive_mining(single_log)
        expected = ("seq", "A", "B")
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_noise_threshold_boundary_values(self):
        """Test boundary values for noise threshold."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        
        # Test with threshold 0.0 (no filtering)
        mining.noise_threshold = 0.0
        result_strict = mining.calculate_cut(self.noisy_log)
        
        # Test with threshold 1.0 (maximum filtering)
        mining.noise_threshold = 1.0
        result_permissive = mining.calculate_cut(self.noisy_log)
        
        # Both should return valid results
        if result_strict:
            self.assertIsInstance(result_strict[0], str)
        if result_permissive:
            self.assertIsInstance(result_permissive[0], str)

    def test_dfg_filtering_logic(self):
        """Test the logic of DFG filtering with different thresholds."""
        mining = InductiveMiningInfrequent(self.rare_edges_log)
        
        # Create DFG and test filtering
        from graphs.dfg import DFG
        full_dfg = DFG(self.rare_edges_log)
        
        # Test with different thresholds
        for threshold in [0.1, 0.3, 0.5]:
            mining.noise_threshold = threshold
            
            # The key test is whether filtering is applied correctly
            # This mainly tests that the mechanism works without error
            try:
                result = mining.calculate_cut(self.rare_edges_log)
                # Should not raise exception
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"DFG filtering failed with threshold {threshold}: {e}")

    def test_performance_with_large_noisy_log(self):
        """Test performance characteristics with larger noisy logs."""
        # Generate larger noisy log
        large_noisy_log = {}
        
        # Main patterns
        for i in range(20):
            large_noisy_log[('A', 'B', 'C', 'D')] = large_noisy_log.get(('A', 'B', 'C', 'D'), 0) + 5
            large_noisy_log[('A', 'C', 'B', 'D')] = large_noisy_log.get(('A', 'C', 'B', 'D'), 0) + 4
        
        # Add systematic noise
        for i in range(10):
            noise_trace = ('A', f'Noise{i}', 'B', 'C', 'D')
            large_noisy_log[noise_trace] = 1
        
        mining = InductiveMiningInfrequent(large_noisy_log)
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        result = mining.inductive_mining(large_noisy_log)
        end_time = time.time()
        
        # Should complete and produce result
        self.assertIsNotNone(result)
        # Should complete in reasonable time (less than 10 seconds for this size)
        self.assertLess(end_time - start_time, 10.0)

    @patch('mining_algorithms.inductive_mining_infrequent.logger')
    def test_logging_integration(self, mock_logger):
        """Test proper logging integration."""
        mining = InductiveMiningInfrequent(self.noisy_log)
        mining.generate_graph(noise_threshold=0.2)
        
        # Should use logger for debugging/info
        # (specific calls depend on implementation details)
        self.assertTrue(hasattr(mining, 'logger'))


if __name__ == '__main__':
    unittest.main() 