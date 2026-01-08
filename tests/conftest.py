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