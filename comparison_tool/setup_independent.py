#!/usr/bin/env python3
"""
Setup Script for Independent Process Mining Comparison Tool
==========================================================

This script sets up the independent comparison tool for easy use.
Run this script to check dependencies and set up the environment.
"""

import sys
import os
import subprocess
from pathlib import Path

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a step with emoji."""
    print(f"\n{step} {description}")

def check_python_version():
    """Check if Python version is compatible."""
    print_step("🐍", "Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("   This tool requires Python 3.8 or higher")
        print("   Please upgrade your Python installation")
        return False
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
        return True

def check_and_install_packages():
    """Check and install required packages."""
    print_step("📦", "Checking required packages...")
    
    required_packages = [
        ('pm4py', '2.7.0'),
        ('pandas', '2.0.0'),
        ('numpy', '1.24.0'),
    ]
    
    missing_packages = []
    
    for package_name, min_version in required_packages:
        try:
            # Try to import the package
            if package_name == 'pm4py':
                import pm4py
                version = pm4py.__version__ if hasattr(pm4py, '__version__') else 'unknown'
            elif package_name == 'pandas':
                import pandas as pd
                version = pd.__version__
            elif package_name == 'numpy':
                import numpy as np
                version = np.__version__
            
            print(f"   ✅ {package_name} {version}")
            
        except ImportError:
            print(f"   ❌ {package_name} - Not installed")
            missing_packages.append(f"{package_name}>={min_version}")
    
    # Install missing packages
    if missing_packages:
        print(f"\n📥 Installing missing packages: {', '.join(missing_packages)}")
        try:
            for package in missing_packages:
                print(f"   Installing {package}...")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True, check=True)
                
            print("✅ All packages installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            print("   Please install manually:")
            for package in missing_packages:
                print(f"   pip install {package}")
            return False
    
    print("✅ All required packages are available!")
    return True

def check_files():
    """Check if all required files are present."""
    print_step("📁", "Checking files...")
    
    current_dir = Path(__file__).parent
    required_files = [
        'independent_comparison_tool.py',
        'independent_requirements.txt',
        'INDEPENDENT_README.md',
        'example_integration.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} - Missing")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        print("   Please ensure all files are in the same directory")
        return False
    
    print("✅ All required files are present!")
    return True

def test_import():
    """Test importing the comparison tool."""
    print_step("🧪", "Testing tool import...")
    
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from independent_comparison_tool import IndependentComparisonTool
        print("✅ Successfully imported IndependentComparisonTool!")
        
        # Test initialization
        tool = IndependentComparisonTool()
        print("✅ Tool initialization successful!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def create_test_script():
    """Create a simple test script."""
    print_step("📝", "Creating test script...")
    
    test_script_content = '''#!/usr/bin/env python3
"""
Quick test script for Independent Comparison Tool
"""

from independent_comparison_tool import IndependentComparisonTool

def main():
    print("🧪 Testing Independent Comparison Tool")
    print("=" * 50)
    
    # Initialize tool
    tool = IndependentComparisonTool()
    print("✅ Tool initialized successfully!")
    
    # Simple test data
    test_log = {
        ('A', 'B', 'C'): 10,
        ('A', 'B', 'D'): 5,
    }
    
    print("✅ Test data created!")
    print("🎯 Tool is ready for use!")
    
    print("\\n📖 Next steps:")
    print("   1. Review INDEPENDENT_README.md for usage instructions")
    print("   2. Check example_integration.py for integration examples")
    print("   3. Import your own algorithms and start comparing!")

if __name__ == "__main__":
    main()
'''
    
    try:
        current_dir = Path(__file__).parent
        test_file = current_dir / "test_setup.py"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script_content)
        
        print(f"✅ Created test script: {test_file}")
        print(f"   Run: python {test_file.name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test script: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions."""
    print_step("📖", "Usage Instructions")
    
    print("""
Your Independent Comparison Tool is ready!
Files in this directory:
   • independent_comparison_tool.py - Main comparison tool
   • example_integration.py        - Integration example
   • INDEPENDENT_README.md         - Detailed documentation
   • test_setup.py                 - Quick test script

Test the tool:
   python test_setup.py

""")

def main():
    """Main setup function."""
    print_header("Independent Process Mining Comparison Tool Setup")
    print("This script will set up the independent comparison tool for use.")
    
    # Check all requirements
    success = True
    success &= check_python_version()
    success &= check_files()
    success &= check_and_install_packages()
    success &= test_import()
    success &= create_test_script()
    
    if success:
        print_header("🎉 SETUP COMPLETE!")
        print("✅ All checks passed!")
        print("✅ Dependencies installed!")
        print("✅ Tool is ready to use!")
        print_usage_instructions()
    else:
        print_header("⚠️  SETUP INCOMPLETE")
        print("❌ Some issues were found. Please resolve them and run setup again.")
        print("\n🛠️  Common Solutions:")
        print("   • Update Python to version 3.8 or higher")
        print("   • Install packages manually: pip install pm4py pandas numpy")
        print("   • Ensure all files are in the same directory")
        print("   • Check internet connection for package installation")

if __name__ == "__main__":
    main() 