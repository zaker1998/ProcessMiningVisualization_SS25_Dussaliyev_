"""
Process Tree Comparison Metrics

This module implements proper process model comparison metrics based on process mining research:
1. Tree Edit Distance (TED)
2. Behavioral Profile Similarity
3. Language Inclusion/Precision/Recall
4. Structural Similarity based on graph isomorphism
"""

import numpy as np
from collections import defaultdict
from itertools import product
import random


class ProcessTreeMetrics:
    """Implements various metrics for comparing process trees."""
    
    def __init__(self):
        self.trace_cache = {}
    
    def tree_edit_distance(self, tree1, tree2, max_depth=20):
        """
        Calculate the Tree Edit Distance between two process trees.
        
        Tree Edit Distance measures the minimum number of node insertions,
        deletions, and relabelings needed to transform one tree into another.
        
        Parameters
        ----------
        tree1 : tuple or str
            First process tree
        tree2 : tuple or str  
            Second process tree
        max_depth : int
            Maximum recursion depth
            
        Returns
        -------
        int
            The edit distance between the trees
        """
        # Memoization for efficiency
        memo = {}
        
        def ted_recursive(t1, t2, depth=0):
            if depth > max_depth:
                return float('inf')
                
            # Check memo
            key = (str(t1), str(t2))
            if key in memo:
                return memo[key]
            
            # Base cases
            if isinstance(t1, str) and isinstance(t2, str):
                result = 0 if t1 == t2 else 1
            elif isinstance(t1, str) or isinstance(t2, str):
                # One is leaf, other is subtree - cost is size of subtree
                if isinstance(t1, str):
                    result = self._tree_size(t2)
                else:
                    result = self._tree_size(t1)
            else:
                # Both are tuples (operators with children)
                if t1[0] == t2[0]:
                    # Same operator - find optimal mapping of children
                    children1 = t1[1:]
                    children2 = t2[1:]
                    
                    if t1[0] in ['seq', 'loop']:
                        # Order matters for sequence and loop
                        result = self._ordered_children_distance(children1, children2, depth)
                    else:
                        # Order doesn't matter for xor and par
                        result = self._unordered_children_distance(children1, children2, depth)
                else:
                    # Different operators - cost is 1 + distance between children sets
                    result = 1 + ted_recursive(('dummy',) + t1[1:], ('dummy',) + t2[1:], depth + 1)
            
            memo[key] = result
            return result
        
        return ted_recursive(tree1, tree2)
    
    def _tree_size(self, tree):
        """Calculate the size of a tree (number of nodes)."""
        if isinstance(tree, str):
            return 1
        return 1 + sum(self._tree_size(child) for child in tree[1:])
    
    def _ordered_children_distance(self, children1, children2, depth):
        """Calculate distance between ordered children (for seq, loop)."""
        n, m = len(children1), len(children2)
        
        # Dynamic programming for edit distance
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        # Initialize base cases
        for i in range(n + 1):
            dp[i][0] = sum(self._tree_size(children1[j]) for j in range(i))
        for j in range(m + 1):
            dp[0][j] = sum(self._tree_size(children2[k]) for k in range(j))
        
        # Fill DP table
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost_replace = self.tree_edit_distance(children1[i-1], children2[j-1], depth + 1)
                cost_delete = self._tree_size(children1[i-1])
                cost_insert = self._tree_size(children2[j-1])
                
                dp[i][j] = min(
                    dp[i-1][j-1] + cost_replace,
                    dp[i-1][j] + cost_delete,
                    dp[i][j-1] + cost_insert
                )
        
        return dp[n][m]
    
    def _unordered_children_distance(self, children1, children2, depth):
        """Calculate distance between unordered children (for xor, par)."""
        # Use Hungarian algorithm approximation for bipartite matching
        n, m = len(children1), len(children2)
        
        if n == 0:
            return sum(self._tree_size(child) for child in children2)
        if m == 0:
            return sum(self._tree_size(child) for child in children1)
        
        # Create cost matrix
        cost_matrix = []
        for c1 in children1:
            row = []
            for c2 in children2:
                row.append(self.tree_edit_distance(c1, c2, depth + 1))
            cost_matrix.append(row)
        
        # Simple greedy matching (for true optimality, use Hungarian algorithm)
        total_cost = 0
        used_j = set()
        
        for i in range(n):
            best_j = -1
            best_cost = float('inf')
            
            for j in range(m):
                if j not in used_j and cost_matrix[i][j] < best_cost:
                    best_cost = cost_matrix[i][j]
                    best_j = j
            
            if best_j != -1:
                total_cost += best_cost
                used_j.add(best_j)
            else:
                total_cost += self._tree_size(children1[i])
        
        # Add cost for unmatched children from children2
        for j in range(m):
            if j not in used_j:
                total_cost += self._tree_size(children2[j])
        
        return total_cost
    
    def behavioral_profile_similarity(self, tree1, tree2, sample_size=100):
        """
        Calculate behavioral profile similarity between two process trees.
        
        This metric compares the behavioral relations (exclusive, parallel, sequential)
        between pairs of activities in both trees.
        
        Parameters
        ----------
        tree1 : tuple or str
            First process tree
        tree2 : tuple or str
            Second process tree
        sample_size : int
            Number of traces to generate for behavioral analysis
            
        Returns
        -------
        float
            Similarity score between 0 and 1
        """
        # Extract activities from both trees
        activities1 = self._extract_activities(tree1)
        activities2 = self._extract_activities(tree2)
        
        # Get union of activities
        all_activities = activities1.union(activities2)
        
        # Generate behavioral profiles
        profile1 = self._compute_behavioral_profile(tree1, all_activities, sample_size)
        profile2 = self._compute_behavioral_profile(tree2, all_activities, sample_size)
        
        # Compare profiles
        matching_relations = 0
        total_relations = 0
        
        for a1 in all_activities:
            for a2 in all_activities:
                if a1 != a2:
                    rel1 = profile1.get((a1, a2), 'none')
                    rel2 = profile2.get((a1, a2), 'none')
                    
                    if rel1 == rel2:
                        matching_relations += 1
                    total_relations += 1
        
        return matching_relations / total_relations if total_relations > 0 else 0
    
    def _extract_activities(self, tree):
        """Extract all activities (non-tau leaves) from a tree."""
        activities = set()
        
        def extract(t):
            if isinstance(t, str):
                if t != 'tau':
                    activities.add(t)
            else:
                for child in t[1:]:
                    extract(child)
        
        extract(tree)
        return activities
    
    def _compute_behavioral_profile(self, tree, activities, sample_size):
        """
        Compute behavioral relations between activities.
        
        Relations can be:
        - 'seq': a always before b
        - 'rev_seq': b always before a  
        - 'par': a and b in any order
        - 'xor': a and b never together
        """
        traces = self._generate_traces_from_tree(tree, sample_size)
        profile = {}
        
        for a1, a2 in product(activities, repeat=2):
            if a1 == a2:
                continue
                
            a1_before_a2 = 0
            a2_before_a1 = 0
            both_present = 0
            
            for trace in traces:
                if a1 in trace and a2 in trace:
                    both_present += 1
                    idx1 = trace.index(a1)
                    idx2 = trace.index(a2)
                    
                    if idx1 < idx2:
                        a1_before_a2 += 1
                    else:
                        a2_before_a1 += 1
            
            # Determine relation
            if both_present == 0:
                profile[(a1, a2)] = 'xor'
            elif a1_before_a2 > 0 and a2_before_a1 == 0:
                profile[(a1, a2)] = 'seq'
            elif a2_before_a1 > 0 and a1_before_a2 == 0:
                profile[(a1, a2)] = 'rev_seq'
            else:
                profile[(a1, a2)] = 'par'
        
        return profile
    
    def _generate_traces_from_tree(self, tree, num_traces):
        """Generate sample traces from a process tree."""
        traces = []
        
        for _ in range(num_traces):
            trace = self._execute_tree(tree)
            if trace:  # Skip empty traces
                traces.append(trace)
        
        return traces
    
    def _execute_tree(self, tree):
        """Execute a process tree to generate a trace."""
        if isinstance(tree, str):
            if tree == 'tau':
                return []
            return [tree]
        
        operator = tree[0]
        children = tree[1:]
        
        if operator == 'seq':
            # Execute children in sequence
            trace = []
            for child in children:
                trace.extend(self._execute_tree(child))
            return trace
            
        elif operator == 'xor':
            # Choose one child randomly
            chosen = random.choice(children)
            return self._execute_tree(chosen)
            
        elif operator == 'par':
            # Execute all children and interleave randomly
            child_traces = [self._execute_tree(child) for child in children]
            # Merge traces in random order
            merged = []
            indices = [0] * len(child_traces)
            
            while any(indices[i] < len(child_traces[i]) for i in range(len(child_traces))):
                # Choose a random child that still has events
                available = [i for i in range(len(child_traces)) if indices[i] < len(child_traces[i])]
                if available:
                    chosen = random.choice(available)
                    merged.append(child_traces[chosen][indices[chosen]])
                    indices[chosen] += 1
            
            return merged
            
        elif operator == 'loop':
            # Execute first child, then optionally execute second child and loop
            trace = self._execute_tree(children[0])
            
            # Randomly decide whether to loop (with decreasing probability)
            loop_prob = 0.5
            
            while len(children) > 1 and random.random() < loop_prob:
                trace.extend(self._execute_tree(children[1]))
                trace.extend(self._execute_tree(children[0]))
                loop_prob *= 0.5  # Decrease probability
            
            return trace
        
        return []
    
    def precision_recall_fitness(self, tree1, tree2, log_traces=None, sample_size=1000):
        """
        Calculate precision, recall, and fitness between two process trees.
        
        - Precision: How many traces from tree1 are accepted by tree2
        - Recall: How many traces from tree2 are accepted by tree1
        - Fitness: Combined F1 score
        
        Parameters
        ----------
        tree1 : tuple or str
            First process tree
        tree2 : tuple or str
            Second process tree
        log_traces : list of tuples, optional
            If provided, use these traces instead of generating
        sample_size : int
            Number of traces to generate if log_traces not provided
            
        Returns
        -------
        dict
            Dictionary with precision, recall, and f1 scores
        """
        if log_traces:
            traces1 = log_traces
            traces2 = log_traces
        else:
            # Generate traces from both trees
            traces1 = [tuple(t) for t in self._generate_traces_from_tree(tree1, sample_size)]
            traces2 = [tuple(t) for t in self._generate_traces_from_tree(tree2, sample_size)]
        
        # Remove duplicates
        traces1_set = set(traces1)
        traces2_set = set(traces2)
        
        # Calculate metrics
        if len(traces1_set) == 0 or len(traces2_set) == 0:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        # For precision: what fraction of tree1's language is in tree2's language
        precision = len(traces1_set.intersection(traces2_set)) / len(traces1_set)
        
        # For recall: what fraction of tree2's language is in tree1's language  
        recall = len(traces2_set.intersection(traces1_set)) / len(traces2_set)
        
        # F1 score
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    def normalized_edit_distance(self, tree1, tree2):
        """
        Calculate normalized tree edit distance (0-1 range).
        
        Parameters
        ----------
        tree1 : tuple or str
            First process tree
        tree2 : tuple or str
            Second process tree
            
        Returns
        -------
        float
            Normalized edit distance between 0 and 1
        """
        ted = self.tree_edit_distance(tree1, tree2)
        max_size = max(self._tree_size(tree1), self._tree_size(tree2))
        
        if max_size == 0:
            return 0.0
            
        # Normalize by maximum possible distance (complete replacement)
        return 1.0 - (ted / max_size)
    
    def _tree_to_graph(self, tree, node_id=0, graph=None, parent=None):
        """Convert a process tree to a directed graph."""
        if graph is None:
            graph = defaultdict(list)
        
        current_id = node_id
        
        if isinstance(tree, str):
            # Leaf node
            graph[f"{tree}_{current_id}"] = []
            if parent is not None:
                graph[parent].append(f"{tree}_{current_id}")
            return current_id + 1, f"{tree}_{current_id}", graph
        else:
            # Operator node
            op_label = f"{tree[0]}_{current_id}"
            graph[op_label] = []
            
            if parent is not None:
                graph[parent].append(op_label)
            
            next_id = current_id + 1
            
            for child in tree[1:]:
                next_id, child_label, graph = self._tree_to_graph(child, next_id, graph, op_label)
            
            return next_id, op_label, graph
    
    def graph_edit_distance_similarity(self, tree1, tree2):
        """
        Calculate similarity based on graph edit distance.
        
        This converts trees to directed graphs and computes edit distance
        on the graph representation.
        
        Parameters
        ----------
        tree1 : tuple or str
            First process tree
        tree2 : tuple or str
            Second process tree
            
        Returns
        -------
        float
            Similarity score between 0 and 1
        """
        # Convert trees to adjacency lists
        _, _, graph1 = self._tree_to_graph(tree1)
        _, _, graph2 = self._tree_to_graph(tree2)
        
        # Simple graph edit distance approximation
        nodes1 = set(graph1.keys())
        nodes2 = set(graph2.keys())
        
        # Node similarity
        node_intersection = len(nodes1.intersection(nodes2))
        node_union = len(nodes1.union(nodes2))
        node_sim = node_intersection / node_union if node_union > 0 else 0
        
        # Edge similarity
        edges1 = set()
        for node, neighbors in graph1.items():
            for neighbor in neighbors:
                edges1.add((node, neighbor))
                
        edges2 = set()
        for node, neighbors in graph2.items():
            for neighbor in neighbors:
                edges2.add((node, neighbor))
        
        edge_intersection = len(edges1.intersection(edges2))
        edge_union = len(edges1.union(edges2))
        edge_sim = edge_intersection / edge_union if edge_union > 0 else 0
        
        # Combined similarity (weighted average)
        return 0.3 * node_sim + 0.7 * edge_sim


def compare_process_trees(tree1, tree2, weights=None):
    """
    Comprehensive comparison of two process trees using multiple metrics.
    
    Parameters
    ----------
    tree1 : tuple or str
        First process tree
    tree2 : tuple or str
        Second process tree  
    weights : dict, optional
        Weights for combining metrics. Defaults to equal weights.
        
    Returns
    -------
    dict
        Dictionary containing all metrics and combined score
    """
    if weights is None:
        weights = {
            'normalized_ted': 0.25,
            'behavioral': 0.25,
            'graph_edit': 0.25,
            'language': 0.25
        }
    
    metrics = ProcessTreeMetrics()
    
    # Calculate individual metrics
    results = {
        'tree_edit_distance': metrics.tree_edit_distance(tree1, tree2),
        'normalized_ted': metrics.normalized_edit_distance(tree1, tree2),
        'behavioral_similarity': metrics.behavioral_profile_similarity(tree1, tree2),
        'graph_edit_similarity': metrics.graph_edit_distance_similarity(tree1, tree2)
    }
    
    # Language-based metrics
    lang_metrics = metrics.precision_recall_fitness(tree1, tree2)
    results.update({
        'language_precision': lang_metrics['precision'],
        'language_recall': lang_metrics['recall'],
        'language_f1': lang_metrics['f1']
    })
    
    # Calculate weighted combined score
    combined_score = (
        weights.get('normalized_ted', 0.25) * results['normalized_ted'] +
        weights.get('behavioral', 0.25) * results['behavioral_similarity'] +
        weights.get('graph_edit', 0.25) * results['graph_edit_similarity'] +
        weights.get('language', 0.25) * results['language_f1']
    )
    
    results['combined_score'] = combined_score
    
    return results 