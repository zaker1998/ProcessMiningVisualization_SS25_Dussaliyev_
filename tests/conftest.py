import os
import sys

# Get the project root directory (should be the parent directory of the tests folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(project_root, "src"))

# Also add the root directory to the path
sys.path.insert(0, project_root) 