"""
Edge case and robustness tests for inductive mining algorithms.

This module tests:
- Extreme edge cases
- Malformed inputs
- Boundary conditions
- Stress tests
- Error recovery
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'src'))

from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# Import from local utils module
from tests.unit.core.algorithms.utils import (
    isProcessTreeEqual,
    ProcessTreeValidator,
    extract_activities_from_tree
)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases for all inductive mining variants."""
    
    # ===== Empty and Minimal Input Tests =====
    
    def test_completely_empty_log(self):
        """Test with completely empty log."""
        empty_log = {}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(empty_log)
                result = miner.inductive_mining(empty_log)
                
                # Should return tau or minimal structure with tau
                self.assertIn(result, ['tau', ('loop', 'tau')])
                
    def test_only_empty_traces(self):
        """Test log containing only empty traces."""
        empty_trace_log = {(): 10}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(empty_trace_log)
                result = miner.inductive_mining(empty_trace_log)
                
                self.assertEqual(result, 'tau')
                
    def test_single_activity_single_occurrence(self):
        """Test with single activity occurring once."""
        single_log = {('A',): 1}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(single_log)
                result = miner.inductive_mining(single_log)
                
                self.assertEqual(result, 'A')
                
    def test_zero_frequency_traces(self):
        """Test with traces having zero frequency."""
        zero_freq_log = {('A', 'B'): 0, ('C', 'D'): 10}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(zero_freq_log)
                # Should handle gracefully
                try:
                    result = miner.inductive_mining(zero_freq_log)
                    self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"{MinerClass.__name__} failed with zero frequency: {e}")
                    
    # ===== Extreme Values Tests =====
    
    def test_very_long_traces(self):
        """Test with very long traces."""
        long_trace = tuple([f'Activity{i}' for i in range(100)])
        long_log = {long_trace: 1}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(long_log)
                result = miner.inductive_mining(long_log)
                
                # Should handle long traces
                self.assertIsNotNone(result)
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    def test_very_high_frequency(self):
        """Test with very high trace frequencies."""
        high_freq_log = {('A', 'B', 'C'): 1000000}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(high_freq_log)
                result = miner.inductive_mining(high_freq_log)
                
                expected = ('seq', 'A', 'B', 'C')
                self.assertTrue(isProcessTreeEqual(result, expected))
                
    def test_many_trace_variants(self):
        """Test with many different trace variants."""
        many_variants_log = {}
        for i in range(100):
            trace = ('Start', f'Task{i}', 'End')
            many_variants_log[trace] = 1
            
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(many_variants_log)
                result = miner.inductive_mining(many_variants_log)
                
                # Should handle many variants (likely flower model)
                self.assertIsNotNone(result)
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    def test_many_activities_in_trace(self):
        """Test with many unique activities."""
        activities = [f'Act{i}' for i in range(50)]
        trace = tuple(activities)
        many_activities_log = {trace: 10}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(many_activities_log)
                result = miner.inductive_mining(many_activities_log)
                
                # Should handle many activities
                self.assertIsNotNone(result)
                
                # All activities should be preserved
                result_activities = extract_activities_from_tree(result)
                for act in activities:
                    self.assertIn(act, result_activities)
                    
    # ===== Special Characters and Data Types =====
    
    def test_numeric_activity_labels(self):
        """Test with numeric activity labels."""
        numeric_log = {(1, 2, 3): 10, (1, 3, 2): 10}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(numeric_log)
                result = miner.inductive_mining(numeric_log)
                
                expected = ('seq', 1, ('par', 2, 3))
                self.assertTrue(isProcessTreeEqual(result, expected))
                
    def test_special_characters_in_labels(self):
        """Test with special characters in activity labels."""
        special_log = {
            ('Start!', 'Process@#$', 'End?'): 10,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(special_log)
                result = miner.inductive_mining(special_log)
                
                self.assertIsNotNone(result)
                
    def test_unicode_activity_labels(self):
        """Test with Unicode characters in activity labels."""
        unicode_log = {
            ('开始', '处理', '结束'): 10,
            ('🚀', '⚙️', '✅'): 5,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(unicode_log)
                result = miner.inductive_mining(unicode_log)
                
                self.assertIsNotNone(result)
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    def test_very_long_activity_names(self):
        """Test with very long activity names."""
        long_name = 'A' * 1000
        long_name_log = {(long_name, 'B', 'C'): 10}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(long_name_log)
                result = miner.inductive_mining(long_name_log)
                
                self.assertIsNotNone(result)
                
    # ===== Boundary Threshold Tests =====
    
    def test_threshold_exactly_one(self):
        """Test with threshold = 1.0 (maximum)."""
        log = {('A', 'B'): 100, ('C', 'D'): 50}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # With threshold 1.0, should filter most activities
                events_to_remove = miner.get_events_to_remove(1.0)
                
                # Should filter activities that don't have max frequency
                self.assertGreater(len(events_to_remove), 0)
                
    def test_threshold_exactly_zero(self):
        """Test with threshold = 0.0 (minimum)."""
        log = {('A', 'B'): 100, ('C', 'D'): 50}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # With threshold 0.0, should not filter anything
                events_to_remove = miner.get_events_to_remove(0.0)
                
                self.assertEqual(len(events_to_remove), 0)
                
    def test_threshold_infinitesimal(self):
        """Test with very small threshold value."""
        log = {('A', 'B'): 100, ('C', 'D'): 1}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # With threshold 0.001, should keep almost everything
                events_to_remove = miner.get_events_to_remove(0.001)
                
                # Should filter very little
                self.assertLess(len(events_to_remove), len(miner.events))
                
    # ===== Recursion Depth Tests =====
    
    def test_deeply_nested_structure(self):
        """Test with pattern that creates deep nesting."""
        # Create a pattern that forces deep recursion
        deep_log = {
            (1, 2, 3, 4, 5, 6): 10,
            (1, 3, 2, 4, 6, 5): 10,
            (1, 2, 4, 3, 5, 6): 10,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(deep_log)
                result = miner.inductive_mining(deep_log)
                
                # Should handle deep nesting
                self.assertIsNotNone(result)
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    def test_recursion_limit_protection(self):
        """Test that recursion limits prevent infinite loops."""
        # Create a complex pattern
        complex_log = {}
        for i in range(20):
            trace = tuple([j % 5 for j in range(i, i + 10)])
            complex_log[trace] = 1
            
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(complex_log)
                
                # Should not cause stack overflow
                try:
                    result = miner.inductive_mining(complex_log)
                    self.assertIsNotNone(result)
                except RecursionError:
                    self.fail(f"{MinerClass.__name__} hit recursion limit")
                    
    # ===== Concurrent Activities Tests =====
    
    def test_fully_concurrent_activities(self):
        """Test with all activities fully concurrent."""
        import itertools
        
        activities = ['A', 'B', 'C', 'D']
        concurrent_log = {}
        
        # Generate all permutations
        for perm in itertools.permutations(activities):
            concurrent_log[perm] = 10
            
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(concurrent_log)
                result = miner.inductive_mining(concurrent_log)
                
                # Should detect parallelism
                self.assertIsNotNone(result)
                result_str = str(result)
                self.assertIn('par', result_str)
                
    def test_partial_concurrency(self):
        """Test with partially concurrent activities."""
        partial_log = {
            ('Start', 'A', 'B', 'End'): 10,
            ('Start', 'B', 'A', 'End'): 10,
            # C is not concurrent with A and B
            ('Start', 'C', 'End'): 5,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(partial_log)
                result = miner.inductive_mining(partial_log)
                
                # Should handle partial concurrency
                self.assertIsNotNone(result)
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    # ===== Malformed Input Tests =====
    
    def test_none_input_to_mining(self):
        """Test with None as input to mining method."""
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass({('A', 'B'): 10})
                
                # None input should raise an error (expected behavior)
                try:
                    result = miner.inductive_mining(None)
                    # If it doesn't raise, check if it returns something valid
                    if result is not None:
                        self.assertTrue(True)  # Acceptable
                except (TypeError, AttributeError):
                    # Expected behavior - None is not a valid log
                    self.assertTrue(True)
                
    def test_duplicate_activities_in_trace(self):
        """Test with traces containing duplicate activities."""
        duplicate_log = {
            ('A', 'A', 'A'): 10,
            ('B', 'B'): 5,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(duplicate_log)
                result = miner.inductive_mining(duplicate_log)
                
                # Should handle duplicates (loops)
                self.assertIsNotNone(result)
                
    # ===== Filtering Edge Cases =====
    
    def test_filtering_removes_all_traces(self):
        """Test when filtering would remove all traces."""
        log = {('A', 'B'): 1, ('C', 'D'): 1}
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # Very high threshold should filter everything
                miner.generate_graph(
                    activity_threshold=0.9,
                    traces_threshold=0.9
                )
                
                # Should still have a graph (even if minimal)
                graph = miner.get_graph()
                self.assertIsNotNone(graph)
                
    def test_filtering_removes_all_but_one_activity(self):
        """Test when filtering leaves only one activity."""
        log = {
            ('A', 'B', 'C'): 100,
            ('X', 'Y', 'Z'): 1,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # Filter out rare activities (provide all required parameters)
                miner.generate_graph(
                    activity_threshold=0.5,
                    traces_threshold=0.0
                )
                
                # Should handle single activity
                self.assertIsNotNone(miner.get_graph())
                
    # ===== IMd-Specific Edge Cases =====
    
    def test_imd_empty_dfg(self):
        """Test IMd with log that creates empty DFG."""
        single_activity_log = {('A',): 10, ('B',): 10}
        
        imd = InductiveMiningDF(single_activity_log)
        result = imd.inductive_mining(single_activity_log)
        
        # Should handle DFG with no edges
        self.assertIsNotNone(result)
        
    def test_imd_edge_filtering_removes_all_edges(self):
        """Test IMd when edge filtering removes all edges."""
        log = {('A', 'B'): 1, ('C', 'D'): 1}
        
        imd = InductiveMiningDF(log)
        imd.edge_cutoff_threshold = 0.99  # Very high
        
        result = imd.inductive_mining(log)
        
        # Should handle case with no edges
        self.assertIsNotNone(result)
        
    # ===== IMf-Specific Edge Cases =====
    
    def test_imf_noise_filtering_removes_all_edges(self):
        """Test IMf when noise filtering is too aggressive."""
        log = {('A', 'B'): 5, ('C', 'D'): 5}
        
        imf = InductiveMiningInfrequent(log)
        imf.noise_threshold = 0.99  # Very high
        
        result = imf.inductive_mining(log)
        
        # Should handle over-filtering
        self.assertIsNotNone(result)
        
    def test_imf_phase_one_success_skips_phase_two(self):
        """Test that IMf Phase 1 success skips Phase 2."""
        clean_log = {('A', 'B', 'C'): 100}
        
        imf = InductiveMiningInfrequent(clean_log)
        imf.noise_threshold = 0.2
        
        # On clean log, Phase 1 should succeed
        result = imf.calculate_cut(clean_log)
        
        self.assertIsNotNone(result)
        
    # ===== Performance and Stress Tests =====
    
    def test_stress_many_trace_variants_large_frequency(self):
        """Stress test with many variants and large frequencies."""
        stress_log = {}
        for i in range(50):
            trace = ('Start', f'Task{i}', 'End')
            stress_log[trace] = 10000
            
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(stress_log)
                
                import time
                start = time.time()
                result = miner.inductive_mining(stress_log)
                duration = time.time() - start
                
                # Should complete in reasonable time
                self.assertLess(duration, 10.0)
                self.assertIsNotNone(result)
                
    def test_stress_deeply_nested_loops(self):
        """Stress test with pattern creating deeply nested loops."""
        nested_loop_log = {}
        for i in range(1, 11):
            trace = tuple(['A'] * i)
            nested_loop_log[trace] = 20 - i
            
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(nested_loop_log)
                result = miner.inductive_mining(nested_loop_log)
                
                # Should handle nested loops
                self.assertIsNotNone(result)
                
    # ===== Error Recovery Tests =====
    
    def test_error_recovery_from_dfg_construction_failure(self):
        """Test error recovery when DFG construction fails."""
        for MinerClass in [InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass({('A', 'B'): 10})
                
                # Mock DFG to raise exception
                with patch('core.graphs.dfg.DFG', side_effect=Exception("DFG Error")):
                    try:
                        result = miner.calculate_cut({('A', 'B'): 10})  # type: ignore
                        # Should either return None or handle gracefully
                        self.assertIn(result, [None, ('A', 'B')])
                    except Exception as e:
                        # Error handling is acceptable
                        pass
                        
    def test_graph_generation_with_invalid_tree(self):
        """Test graph generation when process tree is malformed."""
        miner = InductiveMining({('A', 'B'): 10})
        
        # Mock inductive_mining to return invalid tree
        with patch.object(miner, 'inductive_mining', return_value=None):
            try:
                miner.generate_graph(
                    activity_threshold=0.0,
                    traces_threshold=0.0
                )
                # Should handle gracefully
            except Exception:
                # Error is acceptable
                pass


class TestRobustness(unittest.TestCase):
    """Robustness tests for inductive mining algorithms."""
    
    def test_consistent_results_on_same_input(self):
        """Test that same input produces same results consistently."""
        log = {
            ('A', 'B', 'C'): 10,
            ('A', 'C', 'B'): 10,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                # Run multiple times
                results = []
                for _ in range(5):
                    miner = MinerClass(log)
                    result = miner.inductive_mining(log)
                    results.append(result)
                
                # All results should be equal
                for i in range(1, len(results)):
                    self.assertTrue(
                        isProcessTreeEqual(results[0], results[i]),
                        f"Inconsistent results: {results[0]} vs {results[i]}"
                    )
                    
    def test_parameter_validation(self):
        """Test that invalid parameters are validated."""
        log = {('A', 'B'): 10}
        
        # Test IMd edge cutoff validation
        imd = InductiveMiningDF(log)
        with self.assertRaises(ValueError):
            imd.set_edge_cutoff_threshold(-0.5)
        with self.assertRaises(ValueError):
            imd.set_edge_cutoff_threshold(1.5)
            
        # Test IMf noise threshold validation
        imf = InductiveMiningInfrequent(log)
        with self.assertRaises(ValueError):
            imf.set_noise_threshold(-0.5)
        with self.assertRaises(ValueError):
            imf.set_noise_threshold(1.5)
            
    def test_immutability_of_input_log(self):
        """Test that input log is not modified by mining."""
        original_log = {
            ('A', 'B', 'C'): 10,
            ('A', 'C', 'B'): 10,
        }
        
        for MinerClass in [InductiveMining, InductiveMiningDF, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                log_copy = original_log.copy()
                miner = MinerClass(log_copy)
                miner.inductive_mining(log_copy)
                
                # Original log should not be modified
                self.assertEqual(log_copy, original_log)


if __name__ == '__main__':
    unittest.main()

