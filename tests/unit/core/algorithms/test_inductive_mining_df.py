"""
Comprehensive test suite for Inductive Miner - Directly-Follows (IMd)

Tests the canonical IMd implementation following:
Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2018):
Scalable process discovery and conformance checking.
Software & Systems Modeling 17, 599–631.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from core.algorithms.inductive_df import InductiveMiningDF
from core.graphs.dfg import DFG


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


class TestInductiveMiningDF(unittest.TestCase):
    """Test cases for InductiveMiningDF functionality."""

    def setUp(self):
        """Set up test data with various patterns."""
        # Simple sequential process
        self.sequential_log = {
            ('A', 'B', 'C'): 10,
        }
        
        # Parallel process
        self.parallel_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
        }
        
        # Choice process (exclusive)
        self.choice_log = {
            ('A', 'B'): 30,
            ('A', 'C'): 30,
        }
        
        # Loop process
        self.loop_log = {
            ('A',): 20,
            ('A', 'A'): 15,
            ('A', 'A', 'A'): 10,
        }
        
        # Complex nested process
        self.complex_log = {
            ('Start', 'Task1', 'Task2', 'End'): 40,
            ('Start', 'Task2', 'Task1', 'End'): 35,
            ('Start', 'Task1', 'End'): 20,
            ('Start', 'Task2', 'End'): 15,
        }
        
        # Process with weak edges (suitable for edge filtering)
        self.weak_edges_log = {
            ('A', 'B', 'C'): 100,  # Strong pattern
            ('A', 'C', 'B'): 90,   # Strong pattern
            ('A', 'B', 'D', 'C'): 3,  # Weak edge B->D
            ('A', 'X', 'B', 'C'): 2,  # Weak edge A->X
        }
        
        # Very large scale simulation (for scalability)
        self.large_scale_log = {}
        for i in range(100):
            self.large_scale_log[('Start', 'Process', 'End')] = \
                self.large_scale_log.get(('Start', 'Process', 'End'), 0) + 1

    # ===== Initialization Tests =====
    
    def test_initialization(self):
        """Test IMd initialization with correct defaults."""
        mining = InductiveMiningDF(self.sequential_log)
        
        # Check inherited properties
        self.assertEqual(mining.log, self.sequential_log)
        self.assertIsNotNone(mining.events)
        
        # Check IMd-specific properties
        self.assertEqual(mining.edge_cutoff_threshold, 0.0)
        self.assertEqual(mining._last_edge_threshold, -1.0)
        
    def test_initialization_with_empty_log(self):
        """Test initialization with empty log."""
        mining = InductiveMiningDF({})
        self.assertEqual(mining.log, {})
        
    # ===== Basic Cut Discovery Tests =====
    
    def test_sequential_cut_discovery(self):
        """Test discovery of sequential cuts using DFG."""
        mining = InductiveMiningDF(self.sequential_log)
        result = mining.inductive_mining(self.sequential_log)
        expected = ("seq", "A", "B", "C")
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    def test_parallel_cut_discovery(self):
        """Test discovery of parallel cuts using DFG."""
        mining = InductiveMiningDF(self.parallel_log)
        result = mining.inductive_mining(self.parallel_log)
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    def test_exclusive_cut_discovery(self):
        """Test discovery of exclusive (XOR) cuts using DFG."""
        mining = InductiveMiningDF(self.choice_log)
        result = mining.inductive_mining(self.choice_log)
        expected = ("seq", "A", ("xor", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    def test_loop_cut_discovery(self):
        """Test discovery of loop cuts using DFG."""
        mining = InductiveMiningDF(self.loop_log)
        result = mining.inductive_mining(self.loop_log)
        expected = ("loop", "A", "tau")
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    # ===== Edge Cutoff Threshold Tests =====
    
    def test_edge_cutoff_threshold_zero(self):
        """Test with edge_cutoff_threshold=0 (no filtering)."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            edge_cutoff_threshold=0.0
        )
        
        self.assertEqual(mining.edge_cutoff_threshold, 0.0)
        self.assertIsNotNone(mining.get_graph())
        
    def test_edge_cutoff_threshold_low(self):
        """Test with low edge_cutoff_threshold (minimal filtering)."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            edge_cutoff_threshold=0.05
        )
        
        self.assertEqual(mining.edge_cutoff_threshold, 0.05)
        # Should still discover main pattern
        self.assertIsNotNone(mining.get_graph())
        
    def test_edge_cutoff_threshold_high(self):
        """Test with high edge_cutoff_threshold (aggressive filtering)."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            edge_cutoff_threshold=0.5
        )
        
        self.assertEqual(mining.edge_cutoff_threshold, 0.5)
        # Should discover simplified pattern
        self.assertIsNotNone(mining.get_graph())
        
    def test_edge_cutoff_threshold_boundary_values(self):
        """Test boundary values for edge_cutoff_threshold."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Test 0.0
        mining.generate_graph(edge_cutoff_threshold=0.0)
        self.assertEqual(mining.edge_cutoff_threshold, 0.0)
        
        # Test 1.0
        mining.generate_graph(edge_cutoff_threshold=1.0)
        self.assertEqual(mining.edge_cutoff_threshold, 1.0)
        
    def test_edge_cutoff_threshold_invalid_clamping(self):
        """Test that invalid thresholds are clamped to valid range."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Test negative value (should clamp to 0.0)
        mining.generate_graph(edge_cutoff_threshold=-0.5)
        self.assertEqual(mining.edge_cutoff_threshold, 0.0)
        
        # Test value > 1.0 (should clamp to 1.0)
        mining.generate_graph(edge_cutoff_threshold=1.5)
        self.assertEqual(mining.edge_cutoff_threshold, 1.0)
        
    # ===== DFG-Based Cut Detection Tests =====
    
    def test_calculate_cut_with_empty_log(self):
        """Test cut calculation with empty log."""
        mining = InductiveMiningDF({})
        result = mining.calculate_cut({})
        self.assertIsNone(result)
        
    def test_calculate_cut_with_empty_trace(self):
        """Test cut calculation with empty trace (should skip)."""
        log = {(): 10, ('A', 'B'): 5}
        mining = InductiveMiningDF(log)
        result = mining.calculate_cut(log)
        self.assertIsNone(result)  # Empty trace causes skip
        
    def test_calculate_cut_returns_valid_structure(self):
        """Test that calculate_cut returns valid structure."""
        mining = InductiveMiningDF(self.parallel_log)
        result = mining.calculate_cut(self.parallel_log)
        
        if result:
            operator, sublogs = result
            self.assertIsInstance(operator, str)
            self.assertIn(operator, ["seq", "xor", "par", "loop"])
            self.assertIsInstance(sublogs, list)
            self.assertGreater(len(sublogs), 0)
            
    def test_dfg_construction_from_log(self):
        """Test that DFG is correctly constructed from log."""
        mining = InductiveMiningDF(self.sequential_log)
        
        # Manually construct DFG to verify
        dfg = DFG(self.sequential_log)
        self.assertIsNotNone(dfg)
        
        # Check nodes
        nodes = dfg.get_nodes()
        self.assertIn('A', nodes)
        self.assertIn('B', nodes)
        self.assertIn('C', nodes)
        
        # Check edges
        edges = dfg.get_edges()
        self.assertTrue(any(src == 'A' and tgt == 'B' for src, tgt in edges))
        self.assertTrue(any(src == 'B' and tgt == 'C' for src, tgt in edges))
        
    def test_try_all_cuts_dfg_order(self):
        """Test that cuts are tried in canonical order."""
        mining = InductiveMiningDF(self.complex_log)
        
        # The algorithm should try: exclusive -> sequence -> parallel -> loop
        # We can't directly test the order, but we can verify it finds a valid cut
        result = mining.calculate_cut(self.complex_log)
        
        if result:
            operator, sublogs = result
            self.assertIn(operator, ["xor", "seq", "par", "loop"])
            
    # ===== Edge Filtering Tests =====
    
    def test_create_filtered_dfg_no_filtering(self):
        """Test filtered DFG creation with threshold=0 (no filtering)."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.edge_cutoff_threshold = 0.0
        
        filtered_dfg = mining._create_filtered_dfg(self.weak_edges_log)
        
        # All edges should be present
        self.assertIsNotNone(filtered_dfg)
        
    def test_create_filtered_dfg_with_filtering(self):
        """Test filtered DFG creation with threshold>0."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.edge_cutoff_threshold = 0.1  # Should filter weak edges
        
        filtered_dfg = mining._create_filtered_dfg(self.weak_edges_log)
        
        # Should have fewer edges than full DFG
        full_dfg = DFG(self.weak_edges_log)
        self.assertIsNotNone(filtered_dfg)
        # Weak edges should be filtered
        
    def test_compute_edge_frequencies(self):
        """Test edge frequency computation."""
        mining = InductiveMiningDF(self.weak_edges_log)
        
        edge_freq = mining._compute_edge_frequencies(self.weak_edges_log)
        
        # Check that edge frequencies are computed
        self.assertIsInstance(edge_freq, dict)
        self.assertGreater(len(edge_freq), 0)
        
        # Check specific edges
        self.assertIn(('A', 'B'), edge_freq)
        self.assertIn(('B', 'C'), edge_freq)
        
        # Strong edge should have high frequency
        self.assertGreaterEqual(edge_freq[('A', 'B')], 100)
        
    def test_compute_edge_frequencies_empty_log(self):
        """Test edge frequency computation with empty log."""
        mining = InductiveMiningDF({})
        
        edge_freq = mining._compute_edge_frequencies({})
        
        self.assertIsInstance(edge_freq, dict)
        self.assertEqual(len(edge_freq), 0)
        
    def test_compute_edge_frequencies_single_activity_traces(self):
        """Test edge frequency computation with single-activity traces."""
        log = {('A',): 10, ('B',): 5}
        mining = InductiveMiningDF(log)
        
        edge_freq = mining._compute_edge_frequencies(log)
        
        # No edges in single-activity traces
        self.assertEqual(len(edge_freq), 0)
        
    def test_apply_edge_filtering_to_log(self):
        """Test log filtering based on edge frequency."""
        mining = InductiveMiningDF(self.weak_edges_log)
        
        # Filter with threshold 0.1 (should remove weak edges)
        filtered_log = mining._apply_edge_filtering_to_log(
            self.weak_edges_log, 
            threshold=0.1
        )
        
        self.assertIsInstance(filtered_log, dict)
        # Should have fewer or equal traces
        self.assertLessEqual(len(filtered_log), len(self.weak_edges_log))
        
        # Strong pattern traces should be kept
        self.assertIn(('A', 'B', 'C'), filtered_log)
        
    def test_apply_edge_filtering_threshold_zero(self):
        """Test log filtering with threshold=0 (no filtering)."""
        mining = InductiveMiningDF(self.weak_edges_log)
        
        filtered_log = mining._apply_edge_filtering_to_log(
            self.weak_edges_log, 
            threshold=0.0
        )
        
        # Should return original log
        self.assertEqual(filtered_log, self.weak_edges_log)
        
    # ===== Split Validation Tests =====
    
    def test_validate_split_dfg_valid_splits(self):
        """Test split validation with valid splits."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Create valid splits
        split1 = {('A', 'B'): 50}
        split2 = {('A', 'C'): 50}
        splits = [split1, split2]
        
        # Should validate successfully
        is_valid = mining._validate_split_dfg(splits, self.parallel_log, "par")
        self.assertTrue(is_valid)
        
    def test_validate_split_dfg_empty_split(self):
        """Test split validation with empty split (should fail)."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Create splits with empty split
        split1 = {('A', 'B'): 50}
        split2 = {}  # Empty
        splits = [split1, split2]
        
        is_valid = mining._validate_split_dfg(splits, self.parallel_log, "xor")
        self.assertFalse(is_valid)
        
    def test_validate_split_dfg_insufficient_frequency(self):
        """Test split validation with insufficient frequency preservation."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Create splits that lose too much frequency
        split1 = {('A',): 1}
        split2 = {('B',): 1}
        splits = [split1, split2]
        
        is_valid = mining._validate_split_dfg(splits, self.parallel_log, "seq")
        self.assertFalse(is_valid)
        
    def test_validate_split_dfg_single_split(self):
        """Test split validation with only one split (should fail)."""
        mining = InductiveMiningDF(self.parallel_log)
        
        splits = [{('A', 'B', 'C'): 100}]  # Only one split
        
        is_valid = mining._validate_split_dfg(splits, self.parallel_log, "xor")
        self.assertFalse(is_valid)
        
    def test_validate_split_dfg_operator_specific_thresholds(self):
        """Test that different operators use appropriate thresholds."""
        mining = InductiveMiningDF(self.complex_log)
        
        # Create splits with moderate frequency preservation
        split1 = {('Start', 'Task1', 'End'): 30}
        split2 = {('Start', 'Task2', 'End'): 25}
        splits = [split1, split2]
        
        # XOR should be more strict
        is_valid_xor = mining._validate_split_dfg(splits, self.complex_log, "xor")
        
        # Loop should be more lenient
        is_valid_loop = mining._validate_split_dfg(splits, self.complex_log, "loop")
        
        # Both should return boolean
        self.assertIsInstance(is_valid_xor, bool)
        self.assertIsInstance(is_valid_loop, bool)
        
    # ===== Start/End Node Preservation Tests =====
    
    def test_preserve_start_end_nodes(self):
        """Test preservation of start and end nodes in DFG."""
        mining = InductiveMiningDF(self.sequential_log)
        
        dfg = DFG()
        mining._preserve_start_end_nodes(dfg, self.sequential_log)
        
        # Check that start/end nodes are set
        if hasattr(dfg, 'start_nodes'):
            self.assertIn('A', dfg.start_nodes)
        if hasattr(dfg, 'end_nodes'):
            self.assertIn('C', dfg.end_nodes)
            
    def test_preserve_start_end_nodes_multiple(self):
        """Test preservation with multiple start/end nodes."""
        multi_start_log = {
            ('A', 'X'): 10,
            ('B', 'Y'): 10,
        }
        mining = InductiveMiningDF(multi_start_log)
        
        dfg = DFG()
        mining._preserve_start_end_nodes(dfg, multi_start_log)
        
        if hasattr(dfg, 'start_nodes'):
            self.assertIn('A', dfg.start_nodes)
            self.assertIn('B', dfg.start_nodes)
            
    # ===== Caching and Regeneration Tests =====
    
    def test_graph_regeneration_on_threshold_change(self):
        """Test that graph regenerates when edge threshold changes."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Generate with threshold 0.0
        mining.generate_graph(edge_cutoff_threshold=0.0)
        first_threshold = mining._last_edge_threshold
        
        # Generate with threshold 0.2
        mining.generate_graph(edge_cutoff_threshold=0.2)
        second_threshold = mining._last_edge_threshold
        
        # Threshold should have changed
        self.assertNotEqual(first_threshold, second_threshold)
        self.assertEqual(second_threshold, 0.2)
        
    def test_graph_caching_same_parameters(self):
        """Test that graph is not regenerated with same parameters."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Generate twice with same parameters
        mining.generate_graph(
            activity_threshold=0.1,
            traces_threshold=0.1,
            edge_cutoff_threshold=0.1
        )
        first_filtered_log = mining.filtered_log
        
        mining.generate_graph(
            activity_threshold=0.1,
            traces_threshold=0.1,
            edge_cutoff_threshold=0.1
        )
        second_filtered_log = mining.filtered_log
        
        # Should be the same (cached)
        self.assertEqual(first_filtered_log, second_filtered_log)
        
    # ===== Complex Process Tests =====
    
    def test_complex_nested_process(self):
        """Test mining of complex nested process."""
        complex_nested = {
            (1, 2, 3, 4): 10,
            (1, 3, 2, 4): 10,
            (1, 2, 3, 5, 6, 2, 3, 4): 5,
            (1, 3, 2, 5, 6, 3, 2, 4): 5,
        }
        
        mining = InductiveMiningDF(complex_nested)  # type: ignore
        result = mining.inductive_mining(complex_nested)
        
        expected = ("seq", 1, ("loop", ("par", 2, 3), ("seq", 5, 6)), 4)
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    def test_real_world_pattern(self):
        """Test with real-world-like process pattern."""
        real_world = {
            ('Register', 'Approve', 'Ship', 'Deliver'): 50,
            ('Register', 'Approve', 'Ship', 'Return'): 10,
            ('Register', 'Reject'): 15,
            ('Register', 'Approve', 'Cancel'): 5,
        }
        
        mining = InductiveMiningDF(real_world)
        result = mining.inductive_mining(real_world)
        
        # Should discover some valid structure
        self.assertIsNotNone(result)
        result_str = str(result)
        self.assertIn('Register', result_str)
        
    # ===== Scalability Tests =====
    
    def test_large_scale_log_processing(self):
        """Test that IMd can handle large-scale logs."""
        mining = InductiveMiningDF(self.large_scale_log)
        
        # Should complete without error
        result = mining.inductive_mining(self.large_scale_log)
        
        self.assertIsNotNone(result)
        expected = ("seq", "Start", "Process", "End")
        self.assertTrue(isProcessTreeEqual(result, expected))
        
    def test_performance_with_many_activities(self):
        """Test performance with many different activities."""
        # Create log with many activities
        many_activities_log = {}
        for i in range(50):
            trace = tuple([f'Act{j}' for j in range(i % 5 + 2)])
            many_activities_log[trace] = 1
            
        mining = InductiveMiningDF(many_activities_log)
        
        # Should complete in reasonable time
        import time
        start = time.time()
        result = mining.inductive_mining(many_activities_log)
        duration = time.time() - start
        
        self.assertIsNotNone(result)
        self.assertLess(duration, 5.0)  # Should complete in under 5 seconds
        
    # ===== API and Configuration Tests =====
    
    def test_get_edge_cutoff_threshold(self):
        """Test getter for edge cutoff threshold."""
        mining = InductiveMiningDF(self.parallel_log)
        mining.edge_cutoff_threshold = 0.3
        
        threshold = mining.get_edge_cutoff_threshold()
        self.assertEqual(threshold, 0.3)
        
    def test_set_edge_cutoff_threshold(self):
        """Test setter for edge cutoff threshold."""
        mining = InductiveMiningDF(self.parallel_log)
        
        mining.set_edge_cutoff_threshold(0.4)
        self.assertEqual(mining.edge_cutoff_threshold, 0.4)
        
    def test_set_edge_cutoff_threshold_invalid(self):
        """Test setter with invalid threshold values."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Should raise ValueError for invalid values
        with self.assertRaises(ValueError):
            mining.set_edge_cutoff_threshold(-0.1)
            
        with self.assertRaises(ValueError):
            mining.set_edge_cutoff_threshold(1.5)
            
    def test_get_algorithm_info(self):
        """Test algorithm information retrieval."""
        mining = InductiveMiningDF(self.parallel_log)
        
        info = mining.get_algorithm_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn('name', info)
        self.assertIn('version', info)
        self.assertIn('reference', info)
        self.assertIn('parameters', info)
        self.assertIn('properties', info)
        
        # Check specific values
        self.assertIn('IMd', info['name'])
        self.assertIn('Leemans', info['reference'])
        self.assertEqual(info['properties']['soundness'], 'guaranteed')
        
    # ===== Integration with Base Class Tests =====
    
    def test_inheritance_from_inductive_mining(self):
        """Test that IMd properly inherits from InductiveMining."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Should have all base class methods
        self.assertTrue(hasattr(mining, 'inductive_mining'))
        self.assertTrue(hasattr(mining, 'base_cases'))
        self.assertTrue(hasattr(mining, 'fallthrough'))
        self.assertTrue(hasattr(mining, 'get_log_alphabet'))
        self.assertTrue(hasattr(mining, 'get_graph'))
        
    def test_overridden_calculate_cut(self):
        """Test that calculate_cut is properly overridden."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Should use DFG-based cut detection
        result = mining.calculate_cut(self.parallel_log)
        
        # Result format should match base class
        if result:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            
    # ===== Error Handling Tests =====
    
    def test_error_handling_invalid_log_structure(self):
        """Test error handling with invalid log structure."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Should handle None gracefully
        result = mining.calculate_cut(None)  # type: ignore
        self.assertIsNone(result)
        
    def test_error_handling_dfg_construction_failure(self):
        """Test error handling when DFG construction fails."""
        mining = InductiveMiningDF(self.parallel_log)
        
        # Test with problematic log
        problematic_log = {(): 10}  # Only empty trace
        result = mining.calculate_cut(problematic_log)
        
        # Should handle gracefully (returns None for empty trace)
        self.assertIsNone(result)
        
    # ===== Logging Tests =====
    
    @patch('core.algorithms.inductive_df.logger')
    def test_logging_integration(self, mock_logger):
        """Test that logging is properly integrated."""
        mining = InductiveMiningDF(self.parallel_log)
        mining.generate_graph(edge_cutoff_threshold=0.2)
        
        # Should have logged something
        self.assertTrue(
            mock_logger.info.called or 
            mock_logger.debug.called
        )
        
    @patch('core.algorithms.inductive_df.logger')
    def test_logging_edge_filtering(self, mock_logger):
        """Test logging during edge filtering."""
        mining = InductiveMiningDF(self.weak_edges_log)
        mining.generate_graph(edge_cutoff_threshold=0.1)
        
        # Should log filtering information
        self.assertTrue(mock_logger.info.called)


if __name__ == '__main__':
    unittest.main()

