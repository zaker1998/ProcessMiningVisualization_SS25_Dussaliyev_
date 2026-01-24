"""
Test configuration and path setup for unittest.

This module configures Python paths for test discovery.
Import this module in test files that need path setup, or run tests
from the project root using: python -m unittest discover -s tests -p "test_*.py"
"""
import os
import sys

# Get the project root directory (should be the parent directory of the tests folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_dir = os.path.join(project_root, "src")

# Add the src directory to the Python path if not already there
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Also add the root directory to the path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def setup_test_paths():
    """
    Call this function at the start of test modules to ensure paths are configured.
    This is useful when running individual test files directly.
    """
    pass  # Path setup is done on module import