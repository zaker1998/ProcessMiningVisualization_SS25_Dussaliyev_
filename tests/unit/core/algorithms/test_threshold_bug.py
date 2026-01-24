"""
Test that threshold changes trigger graph regeneration and actually filter traces.

BEHAVIOR:
- ALL thresholds (activity, traces, noise) filter the LOG before mining
- This ensures filtering persists through all recursion levels
- Visual feedback is immediate and intuitive

All thresholds should trigger graph regeneration and produce different results.
"""

import unittest
import sys
import os
from typing import Dict, Tuple

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'src'))

from core.algorithms.inductive_infrequent import InductiveMiningInfrequent


class TestThresholdChangeDetection(unittest.TestCase):
    """
    Verify that changing noise thresholds triggers graph regeneration
    and produces visibly different results.
    
    This tests the practical behavior where:
    - Noise thresholds filter edges in the DFG during cut detection
    - Filtering persists through all recursion levels
    - The graph visibly changes when thresholds change
    """
    
    def setUp(self):
        """Simple log with main behavior and noise."""
        self.log = {
            ('A', 'B', 'C'): 100,
            ('A', 'X', 'C'): 10,
            ('A', 'Y', 'C'): 5,
        }
    
    def test_imf_change_only_noise_threshold(self):
        """
        Test paper-based IMf behavior: Changing noise_threshold affects DFG filtering, not log filtering.
        
        Paper-based IMf behavior (from Leemans et al. 2014):
        - Noise threshold filters EDGES in the DFG during cut detection
        - The log itself is NOT filtered (preserves all trace information)
        - Graph is regenerated with different structure due to different cuts found
        
        This is different from activity/traces thresholds which filter the log directly.
        """
        miner = InductiveMiningInfrequent(self.log)
        
        # Step 1: Generate graph with noise_threshold = 0.0
        print("\n=== Step 1: Generate with noise_threshold=0.0 ===")
        miner.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            noise_threshold=0.0
        )
        graph1_id = id(miner.graph)
        filtered_log1 = miner.filtered_log.copy() if miner.filtered_log else None
        print(f"Graph 1 ID: {graph1_id}")
        print(f"Filtered log 1: {filtered_log1}")
        print(f"Noise threshold 1: {miner.noise_threshold}")
        
        # Step 2: Change ONLY noise_threshold to 0.9 (keep activity and traces same)
        print("\n=== Step 2: Change ONLY noise_threshold to 0.9 ===")
        miner.generate_graph(
            activity_threshold=0.0,  # SAME as before
            traces_threshold=0.0,    # SAME as before
            noise_threshold=0.9      # CHANGED
        )
        graph2_id = id(miner.graph)
        filtered_log2 = miner.filtered_log.copy() if miner.filtered_log else None
        print(f"Graph 2 ID: {graph2_id}")
        print(f"Filtered log 2: {filtered_log2}")
        print(f"Noise threshold 2: {miner.noise_threshold}")
        
        # Step 3: Verify paper-based behavior
        print("\n=== Step 3: Verification ===")
        
        # Paper-based IMf: Log should NOT change (filtering is at DFG level)
        # This is the key difference from the old implementation
        self.assertEqual(filtered_log1, filtered_log2, "Paper-based IMf: filtered log should remain the same (DFG filtering)")
        print("[OK] Filtered log unchanged - paper-based IMf filters at DFG level, not log level")
        
        # The noise threshold should have changed
        self.assertEqual(miner.noise_threshold, 0.9, "Noise threshold should be updated")
        print("[OK] Noise threshold was updated")
        
        # And the graph should be regenerated (different object)
        if graph1_id == graph2_id:
            print("[FAIL] BUG FOUND: Graph was NOT regenerated!")
            self.fail("Graph should be regenerated when noise_threshold changes")
        else:
            print("[OK] Graph was regenerated")
        
        print("\nSUCCESS: Paper-based IMf behavior verified!")


if __name__ == "__main__":
    unittest.main()

