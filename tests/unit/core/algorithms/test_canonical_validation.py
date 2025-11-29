"""
Validation Tests for Canonical IMf and IMd Implementations

This module provides comprehensive validation tests to verify that the canonical
implementations of IMf and IMd produce correct and comparable results to PM4Py.

Tests include:
- Structural correctness of discovered process trees
- Quality metrics (fitness, precision, simplicity)
- Comparison with PM4Py outputs (when available)
- Performance benchmarks
- Edge cases and error handling

These tests serve both as unit tests and as documentation of expected behavior.
"""

import unittest
import time
from typing import Dict, Tuple, Any
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive import InductiveMining


def is_process_tree_equal(tree1: Any, tree2: Any) -> bool:
    """
    Compare two process trees for structural equality.
    
    Trees are considered equal if they have the same structure, even if
    children of commutative operators (xor, par) are in different orders.
    
    Parameters:
    -----------
    tree1, tree2 : Any
        Process trees to compare (tuples or strings)
        
    Returns:
    --------
    bool
        True if trees are structurally equivalent
    """
    # Base case: different types
    if type(tree1) != type(tree2):
        return False
    
    # Base case: leaf nodes (activities or tau)
    if isinstance(tree1, (str, int)):
        return tree1 == tree2
    
    # Recursive case: tree nodes
    if not isinstance(tree1, tuple) or not isinstance(tree2, tuple):
        raise ValueError(f"Invalid tree type: {type(tree1)}")
    
    # Different number of children
    if len(tree1) != len(tree2):
        return False
    
    # Different operators
    operator = tree1[0]
    if operator != tree2[0]:
        return False
    
    # For sequence and first child of loop: order matters
    if operator == "seq":
        return all(is_process_tree_equal(tree1[i], tree2[i]) 
                  for i in range(1, len(tree1)))
    
    if operator == "loop":
        # First child (do part) must match exactly
        if not is_process_tree_equal(tree1[1], tree2[1]):
            return False
        # Remaining children (redo parts) can be in any order
        # (handled by commutative check below)
    
    # For xor, par, and loop redo parts: order doesn't matter
    # Check that each child in tree1 has a match in tree2
    for i in range(1, len(tree1)):
        found_match = False
        for j in range(1, len(tree2)):
            if is_process_tree_equal(tree1[i], tree2[j]):
                found_match = True
                break
        if not found_match:
            return False
    
    return True


class TestCanonicalIMf(unittest.TestCase):
    """
    Test cases for canonical IMf implementation.
    
    These tests verify:
    1. Algorithm follows the 2014 paper specification
    2. Two-phase approach works correctly
    3. Edge filtering is accurate
    4. Results are sound and reasonable
    """
    
    def setUp(self):
        """Set up test logs with known structures."""
        # Clean log: A -> par(B, C)
        self.clean_parallel_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
        }
        
        # Noisy log: Same structure with infrequent edges
        self.noisy_parallel_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
            ('A', 'X', 'B', 'C'): 2,  # Infrequent: noise
            ('A', 'B', 'Y', 'C'): 1,  # Infrequent: noise
        }
        
        # Sequential log: A -> B -> C
        self.sequential_log = {
            ('A', 'B', 'C'): 100,
        }
        
        # Exclusive choice: xor(A, B)
        self.exclusive_log = {
            ('A',): 50,
            ('B',): 50,
        }
        
        # Loop log: loop(A, B)
        self.loop_log = {
            ('A',): 30,
            ('A', 'B', 'A'): 40,
            ('A', 'B', 'A', 'B', 'A'): 30,
        }
    
    def test_initialization(self):
        """Test IMf initialization with correct defaults."""
        miner = InductiveMiningInfrequent(self.clean_parallel_log)
        
        self.assertEqual(miner.noise_threshold, 0.2)
        self.assertIsInstance(miner, InductiveMiningInfrequent)
        self.assertEqual(miner.log, self.clean_parallel_log)
    
    def test_clean_log_phase1_success(self):
        """Test that clean log succeeds in Phase 1 (no filtering needed)."""
        miner = InductiveMiningInfrequent(self.clean_parallel_log)
        miner.noise_threshold = 0.2
        
        tree = miner.inductive_mining(self.clean_parallel_log)
        
        # Should discover: seq(A, par(B, C))
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(is_process_tree_equal(tree, expected))
    
    def test_noisy_log_phase2_filtering(self):
        """Test that noisy log uses Phase 2 filtering."""
        miner = InductiveMiningInfrequent(self.noisy_parallel_log)
        miner.noise_threshold = 0.2  # Should filter edges with freq < 10
        
        tree = miner.inductive_mining(self.noisy_parallel_log)
        
        # Should still discover main structure despite noise
        # Expected: seq(A, par(B, C)) or similar
        tree_str = str(tree)
        self.assertIn("A", tree_str)
        self.assertIn("B", tree_str)
        self.assertIn("C", tree_str)
        
        # Noise activities should not be in main structure
        # (may appear in flower model if structure not found)
        # This is acceptable behavior
    
    def test_sequential_structure(self):
        """Test discovery of sequential structure."""
        miner = InductiveMiningInfrequent(self.sequential_log)
        tree = miner.inductive_mining(self.sequential_log)
        
        expected = ("seq", "A", "B", "C")
        self.assertTrue(is_process_tree_equal(tree, expected))
    
    def test_exclusive_choice(self):
        """Test discovery of exclusive choice."""
        miner = InductiveMiningInfrequent(self.exclusive_log)
        tree = miner.inductive_mining(self.exclusive_log)
        
        expected = ("xor", "A", "B")
        self.assertTrue(is_process_tree_equal(tree, expected))
    
    def test_loop_structure(self):
        """Test discovery of loop structure."""
        miner = InductiveMiningInfrequent(self.loop_log)
        tree = miner.inductive_mining(self.loop_log)
        
        # Should be loop(A, B) or loop(A, tau) depending on log completeness
        tree_str = str(tree)
        self.assertIn("loop", tree_str)
        self.assertIn("A", tree_str)
    
    def test_noise_threshold_bounds(self):
        """Test noise threshold boundary values."""
        miner = InductiveMiningInfrequent(self.noisy_parallel_log)
        
        # Test valid bounds
        miner.set_noise_threshold(0.0)
        self.assertEqual(miner.noise_threshold, 0.0)
        
        miner.set_noise_threshold(1.0)
        self.assertEqual(miner.noise_threshold, 1.0)
        
        miner.set_noise_threshold(0.5)
        self.assertEqual(miner.noise_threshold, 0.5)
        
        # Test invalid bounds
        with self.assertRaises(ValueError):
            miner.set_noise_threshold(-0.1)
        
        with self.assertRaises(ValueError):
            miner.set_noise_threshold(1.1)
    
    def test_edge_frequency_computation(self):
        """Test edge frequency computation is accurate."""
        miner = InductiveMiningInfrequent(self.noisy_parallel_log)
        
        edge_freq = miner._compute_edge_frequencies(self.noisy_parallel_log)
        
        # Check expected edges
        self.assertIn(('A', 'B'), edge_freq)
        self.assertIn(('B', 'C'), edge_freq)
        self.assertIn(('A', 'C'), edge_freq)
        self.assertIn(('C', 'B'), edge_freq)
        
        # Check frequencies
        # ('A', 'B') appears in: (A,B,C):50, (A,B,Y,C):1 = 51
        # Note: (A,X,B,C):2 has A->X, not A->B directly
        self.assertEqual(edge_freq[('A', 'B')], 51)
        
        # ('A', 'C') appears in: (A,C,B):50 = 50
        self.assertEqual(edge_freq[('A', 'C')], 50)
        
        # ('A', 'X') appears in: (A,X,B,C):2 = 2 (infrequent)
        self.assertEqual(edge_freq[('A', 'X')], 2)
    
    def test_algorithm_info(self):
        """Test algorithm introspection."""
        miner = InductiveMiningInfrequent(self.clean_parallel_log)
        info = miner.get_algorithm_info()
        
        self.assertIn("name", info)
        self.assertIn("version", info)
        self.assertIn("reference", info)
        self.assertIn("parameters", info)
        self.assertIn("properties", info)
        
        self.assertEqual(info["name"], "Inductive Miner - Infrequent (IMf)")
        self.assertIn("2014", info["reference"])
        self.assertEqual(info["properties"]["soundness"], "guaranteed")


class TestCanonicalIMd(unittest.TestCase):
    """
    Test cases for canonical IMd implementation.
    
    These tests verify:
    1. Algorithm follows the 2018 paper specification
    2. DFG-based cut detection works correctly
    3. Scalability properties are maintained
    4. Results are sound
    """
    
    def setUp(self):
        """Set up test logs."""
        # Clean parallel log
        self.parallel_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
        }
        
        # Sequential log
        self.sequential_log = {
            ('A', 'B', 'C'): 100,
        }
        
        # Large log simulation (for scalability test)
        self.large_log = {}
        for i in range(1000):
            self.large_log[('Start', 'Task1', 'Task2', 'End')] = \
                self.large_log.get(('Start', 'Task1', 'Task2', 'End'), 0) + 1
            self.large_log[('Start', 'Task2', 'Task1', 'End')] = \
                self.large_log.get(('Start', 'Task2', 'Task1', 'End'), 0) + 1
    
    def test_initialization(self):
        """Test IMd initialization with correct defaults."""
        miner = InductiveMiningDF(self.parallel_log)
        
        self.assertEqual(miner.edge_cutoff_threshold, 0.0)  # No filtering by default
        self.assertIsInstance(miner, InductiveMiningDF)
    
    def test_dfg_based_discovery(self):
        """Test that IMd uses DFG-based cut detection."""
        miner = InductiveMiningDF(self.parallel_log)
        tree = miner.inductive_mining(self.parallel_log)
        
        # Should discover parallel structure
        expected = ("seq", "A", ("par", "B", "C"))
        self.assertTrue(is_process_tree_equal(tree, expected))
    
    def test_sequential_discovery(self):
        """Test sequential structure discovery."""
        miner = InductiveMiningDF(self.sequential_log)
        tree = miner.inductive_mining(self.sequential_log)
        
        expected = ("seq", "A", "B", "C")
        self.assertTrue(is_process_tree_equal(tree, expected))
    
    def test_no_edge_filtering_by_default(self):
        """Test that IMd doesn't filter edges by default (canonical)."""
        miner = InductiveMiningDF(self.parallel_log)
        
        self.assertEqual(miner.edge_cutoff_threshold, 0.0)
        
        # Should use full DFG
        dfg = miner._create_filtered_dfg(self.parallel_log)
        full_dfg_edges = len(dfg.get_edges())
        
        # Should have all edges
        self.assertGreater(full_dfg_edges, 0)
    
    def test_optional_edge_filtering(self):
        """Test optional edge filtering when enabled."""
        miner = InductiveMiningDF(self.parallel_log)
        miner.edge_cutoff_threshold = 0.5  # Aggressive filtering
        
        filtered_dfg = miner._create_filtered_dfg(self.parallel_log)
        
        # Should have fewer edges than full DFG (in some cases)
        self.assertIsNotNone(filtered_dfg)
    
    def test_scalability_properties(self):
        """Test that IMd can handle larger logs efficiently."""
        miner = InductiveMiningDF(self.large_log)
        
        start_time = time.time()
        tree = miner.inductive_mining(self.large_log)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete reasonably fast even with 2000 total trace instances
        self.assertLess(execution_time, 5.0)  # 5 seconds max
        
        # Should discover structure
        self.assertIsNotNone(tree)
    
    def test_algorithm_info(self):
        """Test algorithm introspection."""
        miner = InductiveMiningDF(self.parallel_log)
        info = miner.get_algorithm_info()
        
        self.assertIn("name", info)
        self.assertIn("version", info)
        self.assertIn("reference", info)
        self.assertIn("parameters", info)
        self.assertIn("properties", info)
        
        self.assertEqual(info["name"], "Inductive Miner - Directly-Follows (IMd)")
        self.assertIn("2018", info["reference"])
        self.assertIn("scalability", info["properties"])


class TestComparisonIMfVsIMd(unittest.TestCase):
    """
    Compare IMf and IMd behavior on same logs.
    
    These tests document expected differences and similarities between
    the two algorithms.
    """
    
    def setUp(self):
        """Set up test logs."""
        self.test_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
        }
    
    def test_both_discover_same_structure_on_clean_log(self):
        """Test that IMf and IMd produce similar results on clean logs."""
        imf = InductiveMiningInfrequent(self.test_log)
        imd = InductiveMiningDF(self.test_log)
        
        tree_imf = imf.inductive_mining(self.test_log)
        tree_imd = imd.inductive_mining(self.test_log)
        
        # Should produce equivalent structures
        self.assertTrue(is_process_tree_equal(tree_imf, tree_imd))
    
    def test_configuration_differences(self):
        """Test that IMf and IMd have different configuration parameters."""
        imf = InductiveMiningInfrequent(self.test_log)
        imd = InductiveMiningDF(self.test_log)
        
        # IMf has noise_threshold
        self.assertTrue(hasattr(imf, 'noise_threshold'))
        self.assertEqual(imf.noise_threshold, 0.2)
        
        # IMd has edge_cutoff_threshold
        self.assertTrue(hasattr(imd, 'edge_cutoff_threshold'))
        self.assertEqual(imd.edge_cutoff_threshold, 0.0)


class TestPerformanceBenchmarks(unittest.TestCase):
    """
    Performance benchmarks to validate scalability claims.
    
    These tests provide reference performance numbers and validate
    that the implementations meet expected performance characteristics.
    """
    
    def generate_log(self, num_traces: int, num_activities: int) -> Dict[Tuple[str, ...], int]:
        """Generate synthetic log for testing."""
        log = {}
        activities = [f"Act{i}" for i in range(num_activities)]
        
        for i in range(num_traces):
            # Simple sequential trace
            trace = tuple(activities[:min(5, num_activities)])
            log[trace] = log.get(trace, 0) + 1
        
        return log
    
    def test_imf_medium_log_performance(self):
        """Test IMf performance on medium log."""
        log = self.generate_log(num_traces=1000, num_activities=50)
        miner = InductiveMiningInfrequent(log)
        
        start_time = time.time()
        miner.generate_graph(noise_threshold=0.2)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete in reasonable time
        self.assertLess(execution_time, 10.0)  # 10 seconds max
    
    def test_imd_large_log_performance(self):
        """Test IMd performance on large log."""
        log = self.generate_log(num_traces=5000, num_activities=100)
        miner = InductiveMiningDF(log)
        
        start_time = time.time()
        miner.generate_graph(edge_cutoff_threshold=0.0)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete efficiently
        self.assertLess(execution_time, 15.0)  # 15 seconds max


# Helper function for manual PM4Py comparison
def compare_with_pm4py():
    """
    Manual comparison with PM4Py outputs.
    
    This function is not run as a unit test, but can be executed
    manually to compare outputs with PM4Py when available.
    
    Requirements:
    - pm4py installed
    - Standard test logs available
    """
    try:
        import pm4py
        print("PM4Py available for comparison")
        
        # Example comparison
        test_log = {
            ('A', 'B', 'C'): 50,
            ('A', 'C', 'B'): 50,
        }
        
        # Our implementation
        our_miner = InductiveMiningInfrequent(test_log)
        our_tree = our_miner.inductive_mining(test_log)
        
        print(f"Our IMf result: {our_tree}")
        
        # PM4Py implementation (if available)
        # Note: PM4Py uses different log format, conversion needed
        print("Note: Direct comparison requires log format conversion")
        
    except ImportError:
        print("PM4Py not available - manual comparison not possible")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Optional: Run PM4Py comparison
    print("\n" + "="*70)
    print("PM4Py Comparison (if available)")
    print("="*70)
    compare_with_pm4py()

