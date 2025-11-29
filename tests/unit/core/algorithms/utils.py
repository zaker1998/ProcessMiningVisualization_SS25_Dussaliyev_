"""
Shared utilities for inductive mining algorithm tests.

This module provides common test data, helper functions, and utilities
used across all inductive mining algorithm test suites.
"""

from typing import Dict, Tuple, Any, List


def isProcessTreeEqual(tree1, tree2):
    """
    Check if two process trees are structurally equal.
    
    This function handles unordered operators (xor, par) where children
    can appear in any order, and ordered operators (seq, loop) where
    order matters.
    
    Parameters
    ----------
    tree1 : tuple | str | int
        First process tree
    tree2 : tuple | str | int
        Second process tree
        
    Returns
    -------
    bool
        True if trees are equal, False otherwise
    """
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

    # Ordered cuts - sequence must match exactly
    if operation == "seq":
        return all(isProcessTreeEqual(tree1[i], tree2[i]) for i in range(1, len(tree1)))
    
    # Loop - first child (body) must match exactly
    if operation == "loop":
        if not isProcessTreeEqual(tree1[1], tree2[1]):
            return False

    # Unordered cuts - children can appear in any order
    for i in range(1, len(tree1)):
        foundEqual = False
        for j in range(1, len(tree2)):
            if isProcessTreeEqual(tree1[i], tree2[j]):
                foundEqual = True
                break
        if not foundEqual:
            return False

    return True


def count_activities_in_tree(tree) -> int:
    """
    Count the number of activity nodes (leaves) in a process tree.

    Parameters
    ----------
    tree : tuple | str | int
        Process tree

    Returns
    -------
    int
        Number of activity nodes
    """
    if isinstance(tree, str):
        return 0 if tree == "tau" else 1
    if isinstance(tree, int):
        return 1
    if isinstance(tree, tuple):
        return sum(count_activities_in_tree(child) for child in tree[1:])
    return 0


def extract_activities_from_tree(tree) -> set:
    """
    Extract all unique activities from a process tree.

    Parameters
    ----------
    tree : tuple | str | int
        Process tree

    Returns
    -------
    set
        Set of all activities (excluding tau)
    """
    if isinstance(tree, str):
        return set() if tree == "tau" else {tree}
    if isinstance(tree, int):
        return {tree}
    if isinstance(tree, tuple):
        activities = set()
        for child in tree[1:]:
            activities.update(extract_activities_from_tree(child))
        return activities
    return set()


class TestLogGenerator:
    """Helper class to generate test event logs with various patterns."""
    
    @staticmethod
    def sequential(activities: List[str], frequency: int = 10) -> Dict[Tuple[str, ...], int]:
        """
        Generate a purely sequential log.
        
        Parameters
        ----------
        activities : List[str]
            List of activities in sequence
        frequency : int
            Frequency of the trace
            
        Returns
        -------
        Dict[Tuple[str, ...], int]
            Event log
        """
        return {tuple(activities): frequency}
    
    @staticmethod
    def parallel(start: str, parallel_activities: List[str], end: str, 
                 frequency: int = 10) -> Dict[Tuple[str, ...], int]:
        """
        Generate a log with parallel activities.
        
        Parameters
        ----------
        start : str
            Starting activity
        parallel_activities : List[str]
            Activities that can occur in parallel
        end : str
            Ending activity
        frequency : int
            Base frequency for each variant
            
        Returns
        -------
        Dict[Tuple[str, ...], int]
            Event log with all permutations
        """
        import itertools
        log = {}
        for perm in itertools.permutations(parallel_activities):
            trace = (start,) + perm + (end,)
            log[trace] = frequency
        return log
    
    @staticmethod
    def choice(start: str, choices: List[str], end: str, 
               frequency: int = 10) -> Dict[Tuple[str, ...], int]:
        """
        Generate a log with exclusive choices.
        
        Parameters
        ----------
        start : str
            Starting activity
        choices : List[str]
            Mutually exclusive activities
        end : str
            Ending activity
        frequency : int
            Frequency for each choice
            
        Returns
        -------
        Dict[Tuple[str, ...], int]
            Event log
        """
        log = {}
        for choice in choices:
            trace = (start, choice, end)
            log[trace] = frequency
        return log
    
    @staticmethod
    def loop(activity: str, max_iterations: int = 3, 
             base_frequency: int = 10) -> Dict[Tuple[str, ...], int]:
        """
        Generate a log with loop behavior.
        
        Parameters
        ----------
        activity : str
            Activity that repeats
        max_iterations : int
            Maximum number of iterations
        base_frequency : int
            Base frequency (decreases with iterations)
            
        Returns
        -------
        Dict[Tuple[str, ...], int]
            Event log
        """
        log = {}
        for i in range(1, max_iterations + 1):
            trace = tuple([activity] * i)
            log[trace] = base_frequency // i
        return log
    
    @staticmethod
    def with_noise(clean_log: Dict[Tuple[str, ...], int], 
                   noise_ratio: float = 0.1) -> Dict[Tuple[str, ...], int]:
        """
        Add noise to a clean event log.
        
        Parameters
        ----------
        clean_log : Dict[Tuple[str, ...], int]
            Clean event log
        noise_ratio : float
            Ratio of noise to add (0.0 - 1.0)
            
        Returns
        -------
        Dict[Tuple[str, ...], int]
            Event log with added noise
        """
        import random
        
        noisy_log = clean_log.copy()
        
        # Extract all activities
        all_activities = set()
        for trace in clean_log.keys():
            all_activities.update(trace)
        
        activities_list = list(all_activities)
        if len(activities_list) < 2:
            return noisy_log  # Can't add meaningful noise
        
        # Calculate noise frequency
        total_frequency = sum(clean_log.values())
        noise_frequency = int(total_frequency * noise_ratio)
        
        # Add noisy traces
        noise_activities = ['Noise1', 'Noise2', 'Noise3']
        for _ in range(min(5, noise_frequency)):
            # Create a noisy trace by inserting noise activity
            base_trace = random.choice(list(clean_log.keys()))
            if len(base_trace) > 0:
                insert_pos = random.randint(0, len(base_trace))
                noise_act = random.choice(noise_activities)
                noisy_trace = base_trace[:insert_pos] + (noise_act,) + base_trace[insert_pos:]
                noisy_log[noisy_trace] = max(1, noise_frequency // 5)
        
        return noisy_log


class ProcessTreeValidator:
    """Validator for process tree properties."""
    
    @staticmethod
    def is_valid_structure(tree) -> bool:
        """
        Check if process tree has valid structure.
        
        Parameters
        ----------
        tree : tuple | str | int
            Process tree
            
        Returns
        -------
        bool
            True if structure is valid
        """
        if isinstance(tree, (str, int)):
            return True
        
        if not isinstance(tree, tuple):
            return False
        
        if len(tree) == 0:
            return False
        
        operator = tree[0]
        if operator not in ['seq', 'xor', 'par', 'loop', 'tau']:
            return False
        
        # Operators should have at least one child
        if operator != 'tau' and len(tree) < 2:
            return False
        
        # Recursively check children
        return all(ProcessTreeValidator.is_valid_structure(child) 
                   for child in tree[1:])
    
    @staticmethod
    def is_sound(tree) -> bool:
        """
        Perform basic soundness checks on process tree.
        
        Note: This is a simplified check, not a full soundness verification.
        
        Parameters
        ----------
        tree : tuple | str | int
            Process tree
            
        Returns
        -------
        bool
            True if basic soundness checks pass
        """
        # Check structure validity first
        if not ProcessTreeValidator.is_valid_structure(tree):
            return False
        
        # Loop must have at least 2 children (body, redo)
        if isinstance(tree, tuple) and tree[0] == 'loop':
            if len(tree) < 2:
                return False
        
        # All operators should have children
        if isinstance(tree, tuple) and tree[0] in ['seq', 'xor', 'par', 'loop']:
            if len(tree) < 2:
                return False
        
        return True


# Common test data sets
COMMON_TEST_LOGS = {
    'simple_sequence': {
        ('A', 'B', 'C'): 10,
    },
    
    'simple_parallel': {
        ('A', 'B', 'C'): 10,
        ('A', 'C', 'B'): 10,
    },
    
    'simple_choice': {
        ('A', 'B'): 10,
        ('A', 'C'): 10,
    },
    
    'simple_loop': {
        ('A',): 10,
        ('A', 'A'): 5,
        ('A', 'A', 'A'): 2,
    },
    
    'complex_nested': {
        (1, 2, 3, 4): 10,
        (1, 3, 2, 4): 10,
        (1, 2, 3, 5, 6, 2, 3, 4): 5,
        (1, 3, 2, 5, 6, 3, 2, 4): 5,
    },
    
    'with_tau': {
        (): 5,
        ('A',): 10,
        ('A', 'B'): 8,
    },
    
    'flower_model_trigger': {
        ('A', 'B', 'C'): 1,
        ('B', 'C', 'A'): 1,
        ('C', 'A', 'B'): 1,
    },
}


EXPECTED_TREES = {
    'simple_sequence': ('seq', 'A', 'B', 'C'),
    'simple_parallel': ('seq', 'A', ('par', 'B', 'C')),
    'simple_choice': ('seq', 'A', ('xor', 'B', 'C')),
    'simple_loop': ('loop', 'A', 'tau'),
    'complex_nested': ('seq', 1, ('loop', ('par', 2, 3), ('seq', 5, 6)), 4),
}



