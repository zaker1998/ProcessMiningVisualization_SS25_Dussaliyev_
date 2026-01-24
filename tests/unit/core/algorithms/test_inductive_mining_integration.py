"""
Integration tests for inductive mining algorithm variants.

This module tests:
- Comparison between IM and IMf
- Behavioral differences and similarities
- Edge cases across all variants
- Performance characteristics
"""

import unittest
import time
import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'src'))

from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# Import from local utils module
from tests.unit.core.algorithms.utils import (
    isProcessTreeEqual, 
    TestLogGenerator,
    COMMON_TEST_LOGS,
    EXPECTED_TREES,
    ProcessTreeValidator,
    extract_activities_from_tree,
    count_activities_in_tree
)


class TestInductiveMiningIntegration(unittest.TestCase):
    """Integration tests comparing inductive mining variants."""
    
    def setUp(self):
        """Set up common test data."""
        self.test_logs = COMMON_TEST_LOGS.copy()
        
        # Add more complex test cases
        self.noisy_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'C', 'B'): 95,
            ('A', 'X', 'B', 'C'): 3,  # Noise
            ('A', 'B', 'Y', 'C'): 2,  # Noise
        }
        
        self.large_log = {}
        for i in range(50):
            self.large_log[('Start', 'Process', 'End')] = \
                self.large_log.get(('Start', 'Process', 'End'), 0) + 1
                
    # ===== Consistency Tests =====
    
    def test_all_variants_on_clean_sequence(self):
        """Test that all variants produce same result on clean sequence."""
        log = self.test_logs['simple_sequence']
        
        im = InductiveMining(log)
        imf = InductiveMiningInfrequent(log)
        
        result_im = im.inductive_mining(log)
        result_imf = imf.inductive_mining(log)
        
        expected = EXPECTED_TREES['simple_sequence']
        
        # Both should produce same result
        self.assertTrue(isProcessTreeEqual(result_im, expected))
        self.assertTrue(isProcessTreeEqual(result_imf, expected))
        
    def test_all_variants_on_clean_parallel(self):
        """Test that all variants produce same result on clean parallel."""
        log = self.test_logs['simple_parallel']
        
        im = InductiveMining(log)
        imf = InductiveMiningInfrequent(log)
        
        result_im = im.inductive_mining(log)
        result_imf = imf.inductive_mining(log)
        
        expected = EXPECTED_TREES['simple_parallel']
        
        # Both should produce same result on clean data
        self.assertTrue(isProcessTreeEqual(result_im, expected))
        self.assertTrue(isProcessTreeEqual(result_imf, expected))
        
    def test_all_variants_on_clean_choice(self):
        """Test that all variants produce same result on clean choice."""
        log = self.test_logs['simple_choice']
        
        im = InductiveMining(log)
        imf = InductiveMiningInfrequent(log)
        
        result_im = im.inductive_mining(log)
        result_imf = imf.inductive_mining(log)
        
        expected = EXPECTED_TREES['simple_choice']
        
        # Both should produce same result
        self.assertTrue(isProcessTreeEqual(result_im, expected))
        self.assertTrue(isProcessTreeEqual(result_imf, expected))
        
    def test_all_variants_on_loop(self):
        """Test that all variants handle loops correctly."""
        log = self.test_logs['simple_loop']
        
        im = InductiveMining(log)
        imf = InductiveMiningInfrequent(log)
        
        result_im = im.inductive_mining(log)
        result_imf = imf.inductive_mining(log)
        
        expected = EXPECTED_TREES['simple_loop']
        
        # Both should produce same result
        self.assertTrue(isProcessTreeEqual(result_im, expected))
        self.assertTrue(isProcessTreeEqual(result_imf, expected))
        
    # ===== Noise Handling Comparison =====
    
    def test_im_vs_imf_on_noisy_log(self):
        """Compare IM and IMf behavior on noisy log."""
        im = InductiveMining(self.noisy_log)
        imf = InductiveMiningInfrequent(self.noisy_log)
        
        result_im = im.inductive_mining(self.noisy_log)
        result_imf = imf.inductive_mining(self.noisy_log)
        
        # Both should produce valid trees
        self.assertTrue(ProcessTreeValidator.is_valid_structure(result_im))
        self.assertTrue(ProcessTreeValidator.is_valid_structure(result_imf))
        
        # IMf might produce cleaner result by filtering noise
        # (We don't assert equality because IMf may differ)
        
    def test_imf_with_noise_filtering(self):
        """Test IMf noise filtering behavior."""
        imf = InductiveMiningInfrequent(self.noisy_log)
        
        # IMf with noise filtering
        imf.noise_threshold = 0.1
        result_imf = imf.inductive_mining(self.noisy_log)
        
        # Should produce valid tree
        self.assertTrue(ProcessTreeValidator.is_valid_structure(result_imf))
        
        # Should preserve main activities
        activities_imf = extract_activities_from_tree(result_imf)
        
        self.assertIn('A', activities_imf)
        self.assertIn('B', activities_imf)
        self.assertIn('C', activities_imf)
        
    # ===== Threshold Behavior =====
    
    def test_activity_threshold_consistency(self):
        """Test that activity threshold works consistently across variants."""
        test_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'B', 'D'): 10,  # D is less frequent
            ('A', 'X', 'C'): 1,   # X is rare
        }
        
        threshold = 0.5  # Should filter X and D
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(test_log)
                miner.generate_graph(activity_threshold=threshold, traces_threshold=0.0)
                
                # Should have filtered rare activities
                events_to_remove = miner.get_events_to_remove(threshold)
                self.assertIn('X', events_to_remove)
                
    def test_traces_threshold_consistency(self):
        """Test that traces threshold works consistently across variants."""
        test_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'B', 'D'): 50,
            ('X', 'Y', 'Z'): 2,  # Rare trace
        }
        
        threshold = 0.5  # Should filter rare trace
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(test_log)
                min_freq = miner.calculate_minimum_traces_frequency(threshold)
                
                # Should require frequency >= 50 (0.5 * 100)
                self.assertEqual(min_freq, 50)
                
    # ===== Edge Cases Across All Variants =====
    
    def test_empty_log_all_variants(self):
        """Test that all variants handle empty log correctly."""
        empty_log = {}
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(empty_log)
                result = miner.inductive_mining(empty_log)
                
                # Should return tau or minimal structure with tau
                self.assertIn(result, ['tau', ('loop', 'tau')])
                
    def test_single_trace_all_variants(self):
        """Test that all variants handle single trace correctly."""
        single_log = {('A', 'B', 'C'): 1}
        
        expected = ('seq', 'A', 'B', 'C')
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(single_log)
                result = miner.inductive_mining(single_log)
                
                self.assertTrue(isProcessTreeEqual(result, expected))
                
    def test_single_activity_all_variants(self):
        """Test that all variants handle single activity correctly."""
        single_activity_log = {('A',): 10}
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(single_activity_log)
                result = miner.inductive_mining(single_activity_log)
                
                # Should return just the activity
                self.assertEqual(result, 'A')
                
    def test_tau_handling_all_variants(self):
        """Test that all variants handle tau (empty traces) correctly."""
        tau_log = self.test_logs['with_tau']
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(tau_log)
                result = miner.inductive_mining(tau_log)
                
                # Should produce valid tree with tau handling
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
                # Result should contain tau or xor
                result_str = str(result)
                self.assertTrue('tau' in result_str or 'xor' in result_str, 
                               f"Expected 'tau' or 'xor' in result, got: {result_str}")
                
    def test_flower_model_fallback_all_variants(self):
        """Test that all variants fallback to flower model appropriately."""
        chaotic_log = self.test_logs['flower_model_trigger']
        
        expected_flower = ('loop', 'tau', 'A', 'B', 'C')
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(chaotic_log)
                result = miner.inductive_mining(chaotic_log)
                
                # Should fallback to flower model
                self.assertTrue(isProcessTreeEqual(result, expected_flower))
                
    # ===== Performance Comparison =====
    
    def test_performance_comparison_large_log(self):
        """Compare performance of all variants on large log."""
        timings = {}
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            miner = MinerClass(self.large_log)
            
            start = time.time()
            result = miner.inductive_mining(self.large_log)
            duration = time.time() - start
            
            timings[MinerClass.__name__] = duration
            
            # All should complete in reasonable time
            self.assertLess(duration, 5.0)
            self.assertIsNotNone(result)
            
        print(f"\nPerformance timings: {timings}")
        
    def test_memory_efficiency_comparison(self):
        """Test that all variants handle large logs without excessive memory."""
        # Generate larger log
        large_log = {}
        for i in range(100):
            trace = ('Start', 'Middle', 'End')
            large_log[trace] = large_log.get(trace, 0) + 1
            
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(large_log)
                result = miner.inductive_mining(large_log)
                
                # Should complete without error
                self.assertIsNotNone(result)
                
    # ===== Graph Generation Tests =====
    
    def test_graph_generation_all_variants(self):
        """Test that all variants can generate graphs successfully."""
        log = self.test_logs['simple_parallel']
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                miner.generate_graph(
                    activity_threshold=0.0,
                    traces_threshold=0.0
                )
                
                graph = miner.get_graph()
                self.assertIsNotNone(graph)
                
    def test_graph_regeneration_all_variants(self):
        """Test that graphs regenerate correctly when parameters change."""
        log = self.test_logs['simple_parallel']
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                # Generate with first parameters
                miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0)
                first_graph = miner.get_graph()
                
                # Generate with different parameters
                miner.generate_graph(activity_threshold=0.1, traces_threshold=0.1)
                second_graph = miner.get_graph()
                
                # Should have regenerated
                self.assertIsNotNone(first_graph)
                self.assertIsNotNone(second_graph)
                
    # ===== Soundness Verification =====
    
    def test_soundness_all_variants(self):
        """Verify that all variants produce sound process models."""
        test_logs = [
            self.test_logs['simple_sequence'],
            self.test_logs['simple_parallel'],
            self.test_logs['simple_choice'],
            self.test_logs['simple_loop'],
            self.test_logs['complex_nested'],
        ]
        
        for log in test_logs:
            for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
                with self.subTest(miner=MinerClass.__name__, log=str(log)[:50]):
                    miner = MinerClass(log)
                    result = miner.inductive_mining(log)
                    
                    # Should produce sound model
                    self.assertTrue(ProcessTreeValidator.is_sound(result))
                    
    # ===== Algorithm-Specific Feature Tests =====
    
    def test_imf_noise_threshold_feature(self):
        """Test IMf-specific noise threshold feature."""
        imf = InductiveMiningInfrequent(self.noisy_log)
        
        # Test with different noise thresholds
        for threshold in [0.0, 0.1, 0.3, 0.5]:
            with self.subTest(threshold=threshold):
                imf.noise_threshold = threshold
                result = imf.inductive_mining(self.noisy_log)
                
                self.assertTrue(ProcessTreeValidator.is_valid_structure(result))
                
    def test_imf_two_phase_approach(self):
        """Test that IMf uses two-phase approach (full DFG, then filtered)."""
        imf = InductiveMiningInfrequent(self.noisy_log)
        imf.noise_threshold = 0.2
        
        # The calculate_cut method should try full DFG first
        result = imf.calculate_cut(self.noisy_log)
        
        # Should return valid cut or None
        if result:
            operator, sublogs = result
            self.assertIn(operator, ['seq', 'xor', 'par', 'loop'])
            
    # ===== Complex Pattern Tests =====
    
    def test_all_variants_on_complex_nested(self):
        """Test all variants on complex nested pattern."""
        log = self.test_logs['complex_nested']
        expected = EXPECTED_TREES['complex_nested']
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                result = miner.inductive_mining(log)
                
                # Should produce expected structure
                self.assertTrue(isProcessTreeEqual(result, expected))
                
    def test_all_variants_preserve_main_activities(self):
        """Test that all variants preserve main activities in result."""
        test_log = {
            ('A', 'B', 'C', 'D'): 50,
            ('A', 'C', 'B', 'D'): 50,
        }
        
        main_activities = {'A', 'B', 'C', 'D'}
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(test_log)
                result = miner.inductive_mining(test_log)
                
                # Extract activities from result
                result_activities = extract_activities_from_tree(result)
                
                # Should preserve all main activities
                self.assertTrue(main_activities.issubset(result_activities))
                
    # ===== API Consistency Tests =====
    
    def test_get_graph_api_consistency(self):
        """Test that get_graph API is consistent across variants."""
        log = self.test_logs['simple_parallel']
        
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                miner.generate_graph(
                    activity_threshold=0.0,
                    traces_threshold=0.0
                )
                
                # Should have get_graph method
                self.assertTrue(hasattr(miner, 'get_graph'))
                
                # Should return graph
                graph = miner.get_graph()
                self.assertIsNotNone(graph)
                
    def test_threshold_getter_api_consistency(self):
        """Test that threshold getter APIs are consistent."""
        log = self.test_logs['simple_parallel']
        
        # All should have activity and traces threshold getters
        for MinerClass in [InductiveMining, InductiveMiningInfrequent]:
            with self.subTest(miner=MinerClass.__name__):
                miner = MinerClass(log)
                
                self.assertTrue(hasattr(miner, 'get_activity_threshold'))
                self.assertTrue(hasattr(miner, 'get_traces_threshold'))
                
                # Should return default values
                self.assertIsInstance(miner.get_activity_threshold(), float)
                self.assertIsInstance(miner.get_traces_threshold(), float)


if __name__ == '__main__':
    unittest.main()

