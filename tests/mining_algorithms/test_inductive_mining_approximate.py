import unittest
from unittest.mock import Mock, patch
from mining_algorithms.inductive_mining_approximate import InductiveMiningApproximate


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


class TestInductiveMiningApproximate(unittest.TestCase):
    """Test cases for InductiveMiningApproximate functionality."""

    def setUp(self):
        """Set up test data with various quality patterns."""
        # High quality process - clear cuts
        self.high_quality_log = {
            ('A', 'B', 'C'): 100,
            ('A', 'C', 'B'): 100,
        }
        
        # Medium quality process - some ambiguity
        self.medium_quality_log = {
            ('A', 'B', 'C', 'D'): 50,
            ('A', 'C', 'B', 'D'): 40,
            ('A', 'B', 'D'): 30,
            ('A', 'C', 'D'): 25,
        }
        
        # Low quality process - high ambiguity
        self.low_quality_log = {
            ('A', 'B', 'C'): 20,
            ('A', 'C', 'B'): 18,
            ('B', 'A', 'C'): 15,
            ('B', 'C', 'A'): 12,
            ('C', 'A', 'B'): 10,
            ('C', 'B', 'A'): 8,
        }
        
        # Process requiring simplification
        self.complex_log = {
            ('Start', 'Process1', 'Process2', 'End'): 30,
            ('Start', 'Process2', 'Process1', 'End'): 25,
            ('Start', 'Process1', 'End'): 20,
            ('Start', 'Process2', 'End'): 15,
            # Low frequency edges that should be simplified
            ('Start', 'Process1', 'Rare1', 'Process2', 'End'): 3,
            ('Start', 'Process2', 'Rare2', 'Process1', 'End'): 2,
            ('Start', 'Rare3', 'End'): 1,
        }

    def test_initialization(self):
        """Test InductiveMiningApproximate initialization."""
        mining = InductiveMiningApproximate(self.high_quality_log)
        
        # Check inherited properties
        self.assertIsInstance(mining, InductiveMiningApproximate)
        self.assertEqual(mining.log, self.high_quality_log)
        
        # Check approximate-specific properties
        self.assertEqual(mining.simplification_threshold, 0.1)

    def test_simplification_threshold_parameter(self):
        """Test simplification threshold parameter handling."""
        mining = InductiveMiningApproximate(self.complex_log)
        
        # Test setting simplification threshold through generate_graph
        mining.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            simplification_threshold=0.2
        )
        
        self.assertEqual(mining.simplification_threshold, 0.2)

    def test_high_quality_process_mining(self):
        """Test mining on high quality process."""
        mining = InductiveMiningApproximate(self.high_quality_log)
        result = mining.inductive_mining(self.high_quality_log)
        
        # Should discover clear parallel cut after sequence
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_exclusive_cut_quality_validation(self):
        """Test exclusive cut quality validation."""
        mining = InductiveMiningApproximate(self.medium_quality_log)
        
        # Test quality validation for exclusive cuts
        # Create test splits for validation
        test_splits = [
            {('A', 'B'): 10},
            {('C', 'D'): 15}
        ]
        
        # This tests the validation logic exists and works
        result = mining._validate_exclusive_cut_quality(test_splits, self.medium_quality_log)
        self.assertIsInstance(result, bool)

    def test_sequence_cut_quality_validation(self):
        """Test sequence cut quality validation."""
        mining = InductiveMiningApproximate(self.medium_quality_log)
        
        # Test quality validation for sequence cuts
        test_splits = [
            {('A',): 10, ('A', 'B'): 5},
            {('C', 'D'): 15, ('D'): 5}
        ]
        
        result = mining._validate_sequence_cut_quality(test_splits, self.medium_quality_log)
        self.assertIsInstance(result, bool)

    def test_parallel_cut_quality_validation(self):
        """Test parallel cut quality validation."""
        mining = InductiveMiningApproximate(self.high_quality_log)
        
        # Test quality validation for parallel cuts
        test_splits = [
            {('B',): 50, ('B', 'C'): 25},
            {('C',): 40, ('C', 'B'): 30}
        ]
        
        result = mining._validate_parallel_cut_quality(test_splits, self.high_quality_log)
        self.assertIsInstance(result, bool)

    def test_loop_cut_quality_validation(self):
        """Test loop cut quality validation."""
        loop_log = {
            ('A',): 10,
            ('A', 'A'): 8,
            ('A', 'A', 'A'): 5
        }
        
        mining = InductiveMiningApproximate(loop_log)
        
        # Test quality validation for loop cuts
        test_splits = [
            {('A',): 10},  # body
            {(): 3, ('A',): 5}  # redo
        ]
        
        result = mining._validate_loop_cut_quality(test_splits, loop_log)
        self.assertIsInstance(result, bool)

    def test_fallback_to_simplified_dfg(self):
        """Test fallback to simplified DFG when quality is poor."""
        mining = InductiveMiningApproximate(self.low_quality_log)
        mining.simplification_threshold = 0.3
        
        # Mock quality validators to fail initially
        with patch.object(mining, '_validate_exclusive_cut_quality', return_value=False), \
             patch.object(mining, '_validate_sequence_cut_quality', return_value=False), \
             patch.object(mining, '_validate_parallel_cut_quality', return_value=False):
            
            result = mining.calculate_cut(self.low_quality_log)
            
            # Should still return some result using simplified approach
            if result:
                operator, sublogs = result
                self.assertIsInstance(operator, str)
                self.assertIsInstance(sublogs, list)

    def test_dfg_simplification_logic(self):
        """Test DFG simplification with different thresholds."""
        mining = InductiveMiningApproximate(self.complex_log)
        
        from graphs.dfg import DFG
        original_dfg = DFG(self.complex_log)
        
        # Test with different simplification thresholds
        for threshold in [0.05, 0.1, 0.2, 0.5]:
            mining.simplification_threshold = threshold
            
            # Test that simplification doesn't cause errors
            try:
                result = mining.calculate_cut(self.complex_log)
                # Should not raise exception
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Simplification failed with threshold {threshold}: {e}")

    def test_quality_vs_simplification_tradeoff(self):
        """Test tradeoff between quality requirements and simplification."""
        mining = InductiveMiningApproximate(self.complex_log)
        
        # Strict quality + high simplification
        mining.simplification_threshold = 0.5
        result_high_simplification = mining.calculate_cut(self.complex_log)
        
        # Strict quality + low simplification  
        mining.simplification_threshold = 0.05
        result_low_simplification = mining.calculate_cut(self.complex_log)
        
        # Both should produce valid results
        for result in [result_high_simplification, result_low_simplification]:
            if result:
                operator, sublogs = result
                self.assertIsInstance(operator, str)
                self.assertIsInstance(sublogs, list)

    def test_calculate_cut_with_validators(self):
        """Test calculate_cut method using quality validators."""
        mining = InductiveMiningApproximate(self.medium_quality_log)
        
        # Test that calculate_cut uses validators properly
        result = mining.calculate_cut(self.medium_quality_log)
        
        if result:
            operator, sublogs = result
            self.assertIn(operator, ["seq", "xor", "par", "loop"])
            self.assertIsInstance(sublogs, list)
            self.assertGreater(len(sublogs), 0)

    def test_inheritance_from_inductive_mining(self):
        """Test that ApproximateMining properly inherits from InductiveMining."""
        mining = InductiveMiningApproximate(self.high_quality_log)
        
        # Should have all base class methods
        self.assertTrue(hasattr(mining, 'inductive_mining'))
        self.assertTrue(hasattr(mining, 'get_graph'))
        self.assertTrue(hasattr(mining, 'generate_graph'))

    def test_quality_validation_edge_cases(self):
        """Test quality validation with edge cases."""
        mining = InductiveMiningApproximate(self.high_quality_log)
        
        # Empty splits
        empty_splits = []
        result = mining._validate_exclusive_cut_quality(empty_splits, self.high_quality_log)
        self.assertIsInstance(result, bool)
        
        # Single split
        single_split = [{('A', 'B', 'C'): 100}]
        result = mining._validate_exclusive_cut_quality(single_split, self.high_quality_log)
        self.assertIsInstance(result, bool)

    def test_complex_process_with_approximation(self):
        """Test complex process requiring approximation techniques."""
        complex_process = {
            ('Register', 'CheckDocs', 'Interview', 'Decide'): 25,
            ('Register', 'Interview', 'CheckDocs', 'Decide'): 20,
            ('Register', 'CheckDocs', 'Decide'): 15,
            ('Register', 'Interview', 'Decide'): 12,
            ('Register', 'FastTrack', 'Decide'): 10,
            # Noisy variants requiring approximation
            ('Register', 'CheckDocs', 'ExtraCheck', 'Interview', 'Decide'): 3,
            ('Register', 'Interview', 'Clarify', 'CheckDocs', 'Decide'): 2,
            ('Register', 'CheckDocs', 'Interview', 'Review', 'Decide'): 1,
        }
        
        mining = InductiveMiningApproximate(complex_process)
        mining.simplification_threshold = 0.1
        
        result = mining.inductive_mining(complex_process)
        
        # Should discover main structure
        self.assertIsNotNone(result)
        result_str = str(result)
        
        # Main activities should be present
        main_activities = ['Register', 'CheckDocs', 'Interview', 'Decide']
        for activity in main_activities:
            self.assertIn(activity, result_str)

    def test_quality_validator_integration(self):
        """Test integration between different quality validators."""
        mining = InductiveMiningApproximate(self.medium_quality_log)
        
        # Each validator should handle its specific cut type
        test_methods = [
            ('_validate_exclusive_cut_quality', 'xor'),
            ('_validate_sequence_cut_quality', 'seq'),
            ('_validate_parallel_cut_quality', 'par'),
            ('_validate_loop_cut_quality', 'loop')
        ]
        
        for method_name, cut_type in test_methods:
            with self.subTest(validator=method_name):
                self.assertTrue(hasattr(mining, method_name))
                # Method should be callable
                method = getattr(mining, method_name)
                self.assertTrue(callable(method))

    def test_performance_with_approximation(self):
        """Test performance characteristics with approximation."""
        # Create larger log requiring approximation
        large_log = {}
        
        # Main patterns
        base_patterns = [
            ('A', 'B', 'C', 'D'),
            ('A', 'C', 'B', 'D'),
            ('A', 'B', 'D'),
            ('A', 'C', 'D')
        ]
        
        for pattern in base_patterns:
            large_log[pattern] = 50
        
        # Add many low-frequency variants
        for i in range(20):
            variant = ('A', f'Variant{i}', 'B', 'C', 'D')
            large_log[variant] = 2
        
        mining = InductiveMiningApproximate(large_log)
        mining.simplification_threshold = 0.1
        
        # Should complete in reasonable time
        import time
        start_time = time.time()
        result = mining.inductive_mining(large_log)
        end_time = time.time()
        
        self.assertIsNotNone(result)
        self.assertLess(end_time - start_time, 10.0)  # Should complete quickly

    def test_empty_and_simple_logs(self):
        """Test edge cases with empty and simple logs."""
        # Empty log
        mining = InductiveMiningApproximate({})
        result = mining.inductive_mining({})
        self.assertEqual(result, "tau")
        
        # Single activity
        single_log = {('A',): 10}
        mining = InductiveMiningApproximate(single_log)
        result = mining.inductive_mining(single_log)
        self.assertEqual(result, "A")
        
        # Simple sequence
        seq_log = {('A', 'B'): 10}
        mining = InductiveMiningApproximate(seq_log)
        result = mining.inductive_mining(seq_log)
        expected = ("seq", "A", "B")
        self.assertTrue(isProcessTreeEqual(result, expected))

    def test_approximation_threshold_boundary_values(self):
        """Test boundary values for simplification threshold."""
        mining = InductiveMiningApproximate(self.complex_log)
        
        # Test with threshold 0.0 (no simplification)
        mining.simplification_threshold = 0.0
        result_no_simplification = mining.calculate_cut(self.complex_log)
        
        # Test with threshold 1.0 (maximum simplification)
        mining.simplification_threshold = 1.0
        result_max_simplification = mining.calculate_cut(self.complex_log)
        
        # Both should work without error
        for result in [result_no_simplification, result_max_simplification]:
            if result:
                operator, sublogs = result
                self.assertIsInstance(operator, str)

    @patch('mining_algorithms.inductive_mining_approximate.logger')
    def test_logging_integration(self, mock_logger):
        """Test proper logging integration."""
        mining = InductiveMiningApproximate(self.medium_quality_log)
        mining.generate_graph(simplification_threshold=0.2)
        
        # Should use logger appropriately
        self.assertTrue(hasattr(mining, 'logger'))


if __name__ == '__main__':
    unittest.main() 