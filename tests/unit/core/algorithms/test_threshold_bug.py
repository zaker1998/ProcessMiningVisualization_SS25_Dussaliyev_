"""
Test that threshold changes trigger graph regeneration and actually filter traces.

BEHAVIOR:
- ALL thresholds (activity, traces, edge, noise) filter the LOG before mining
- This ensures filtering persists through all recursion levels
- Visual feedback is immediate and intuitive

All thresholds should trigger graph regeneration and produce different results.
"""

import pytest
from typing import Dict, Tuple
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent


class TestThresholdChangeDetection:
    """
    Verify that changing edge/noise thresholds triggers graph regeneration
    and produces visibly different results.
    
    This tests the practical behavior where:
    - Edge/noise thresholds filter traces from the log (like activity/traces)
    - Filtering persists through all recursion levels
    - The graph visibly changes when thresholds change
    """
    
    @pytest.fixture
    def log(self) -> Dict[Tuple[str, ...], int]:
        """Simple log with main behavior and noise."""
        return {
            ('A', 'B', 'C'): 100,
            ('A', 'X', 'C'): 10,
            ('A', 'Y', 'C'): 5,
        }
    
    def test_imd_change_only_edge_threshold(self, log):
        """
        Test practical behavior: Changing ONLY edge_threshold should filter traces and regenerate graph.
        
        Practical IMd behavior (like activity/traces):
        - Edge threshold filters traces from the log
        - Traces with weak edges are removed
        - Graph is regenerated and visibly different
        
        This simulates the user changing the edge threshold slider in the UI
        while keeping activity_threshold and traces_threshold the same.
        """
        miner = InductiveMiningDF(log)
        
        # Step 1: Generate graph with edge_threshold = 0.0
        print("\n=== Step 1: Generate with edge_threshold=0.0 ===")
        miner.generate_graph(
            activity_threshold=0.0,
            traces_threshold=0.0,
            edge_cutoff_threshold=0.0
        )
        graph1_id = id(miner.graph)
        filtered_log1 = miner.filtered_log.copy() if miner.filtered_log else None
        print(f"Graph 1 ID: {graph1_id}")
        print(f"Filtered log 1: {filtered_log1}")
        print(f"Edge threshold 1: {miner.edge_cutoff_threshold}")
        
        # Step 2: Change ONLY edge_threshold to 0.9 (keep activity and traces same)
        print("\n=== Step 2: Change ONLY edge_threshold to 0.9 ===")
        miner.generate_graph(
            activity_threshold=0.0,  # SAME as before
            traces_threshold=0.0,    # SAME as before
            edge_cutoff_threshold=0.9  # CHANGED
        )
        graph2_id = id(miner.graph)
        filtered_log2 = miner.filtered_log.copy() if miner.filtered_log else None
        print(f"Graph 2 ID: {graph2_id}")
        print(f"Filtered log 2: {filtered_log2}")
        print(f"Edge threshold 2: {miner.edge_cutoff_threshold}")
        
        # Step 3: Verify practical behavior
        print("\n=== Step 3: Verification ===")
        
        # Practical: Log SHOULD change (traces with weak edges are filtered)
        assert filtered_log1 != filtered_log2, "Filtered log should change (traces filtered)"
        print("[OK] Filtered log changed - traces with weak edges removed")
        
        # Should have fewer traces after filtering
        assert len(filtered_log2) < len(filtered_log1), "Should have fewer traces after filtering"
        print(f"[OK] Traces reduced from {len(filtered_log1)} to {len(filtered_log2)}")
        
        # The edge threshold should have changed
        assert miner.edge_cutoff_threshold == 0.9, "Edge threshold should be updated"
        print("[OK] Edge threshold was updated")
        
        # And the graph should be regenerated (different object)
        if graph1_id == graph2_id:
            print("[FAIL] BUG FOUND: Graph was NOT regenerated!")
            assert False, "Graph should be regenerated when edge_threshold changes"
        else:
            print("[OK] Graph was regenerated")
        
        print("\nSUCCESS: Threshold change filtered traces and regenerated graph!")
    
    def test_imf_change_only_noise_threshold(self, log):
        """
        Test practical behavior: Changing ONLY noise_threshold should filter traces and regenerate graph.
        
        Practical IMf behavior (like activity/traces):
        - Noise threshold filters traces from the log
        - Traces with noisy edges are removed
        - Graph is regenerated and visibly different
        
        This simulates the user changing the noise threshold slider in the UI
        while keeping activity_threshold and traces_threshold the same.
        """
        miner = InductiveMiningInfrequent(log)
        
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
        
        # Step 3: Verify practical behavior
        print("\n=== Step 3: Verification ===")
        
        # Practical: Log SHOULD change (traces with noisy edges are filtered)
        assert filtered_log1 != filtered_log2, "Filtered log should change (traces filtered)"
        print("[OK] Filtered log changed - traces with noisy edges removed")
        
        # Should have fewer traces after filtering
        assert len(filtered_log2) < len(filtered_log1), "Should have fewer traces after filtering"
        print(f"[OK] Traces reduced from {len(filtered_log1)} to {len(filtered_log2)}")
        
        # The noise threshold should have changed
        assert miner.noise_threshold == 0.9, "Noise threshold should be updated"
        print("[OK] Noise threshold was updated")
        
        # And the graph should be regenerated (different object)
        if graph1_id == graph2_id:
            print("[FAIL] BUG FOUND: Graph was NOT regenerated!")
            assert False, "Graph should be regenerated when noise_threshold changes"
        else:
            print("[OK] Graph was regenerated")
        
        print("\nSUCCESS: Threshold change filtered traces and regenerated graph!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

