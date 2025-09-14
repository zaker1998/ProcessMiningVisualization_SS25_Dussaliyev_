#!/usr/bin/env python3
"""
Test runner for all inductive mining algorithm tests.

This script runs all unit tests for the inductive mining implementations
and provides a comprehensive summary report.
"""

import unittest
import sys
import os
import time
from io import StringIO


def discover_and_run_tests():
    """Discover and run all tests in the mining_algorithms test directory."""
    
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 80)
    print("INDUCTIVE MINING ALGORITHM TEST SUITE")
    print("=" * 80)
    print(f"Test directory: {test_dir}")
    print()
    
    # Discover all test modules
    loader = unittest.TestLoader()
    start_dir = test_dir
    pattern = 'test_*.py'
    
    print("Discovering tests...")
    suite = loader.discover(start_dir, pattern=pattern)
    
    # Count total tests
    total_tests = count_tests(suite)
    print(f"Found {total_tests} tests across multiple modules")
    print()
    
    # Run tests with detailed output
    print("Running tests...")
    print("-" * 80)
    
    # Capture test results
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, 
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print captured output
    print(stream.getvalue())
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    duration = end_time - start_time
    print(f"Total tests run: {result.testsRun}")
    print(f"Total time: {duration:.2f} seconds")
    print(f"Average time per test: {duration/result.testsRun:.3f} seconds")
    print()
    
    # Results breakdown
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"⏭️  Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print()
    
    # Detailed failure/error reporting
    if result.failures:
        print("FAILURES:")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"❌ {test}")
            print(f"   {traceback.split(chr(10))[-2]}")  # Last meaningful line
        print()
    
    if result.errors:
        print("ERRORS:")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"💥 {test}")
            print(f"   {traceback.split(chr(10))[-2]}")  # Last meaningful line
        print()
    
    # Success rate
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    # Overall result
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} TEST(S) FAILED")
        return 1


def count_tests(suite):
    """Recursively count the number of tests in a test suite."""
    count = 0
    for test in suite:
        if hasattr(test, '__iter__'):
            # It's a test suite
            count += count_tests(test)
        else:
            # It's a test case
            count += 1
    return count


def run_specific_test_module(module_name):
    """Run tests for a specific module."""
    print(f"Running tests for module: {module_name}")
    print("-" * 50)
    
    try:
        # Import the specific test module
        test_module = __import__(module_name)
        
        # Create test suite from module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Could not import test module '{module_name}': {e}")
        return False


def main():
    """Main entry point for the test runner."""
    
    if len(sys.argv) > 1:
        # Run specific test module
        module_name = sys.argv[1]
        if not module_name.startswith('test_'):
            module_name = f'test_{module_name}'
        success = run_specific_test_module(module_name)
        return 0 if success else 1
    else:
        # Run all tests
        return discover_and_run_tests()


def print_test_modules_info():
    """Print information about available test modules."""
    print("Available test modules:")
    print("=" * 40)
    
    test_modules = [
        ("test_base_mining.py", "Tests for BaseMining class - core functionality"),
        ("test_process_tree.py", "Tests for ProcessTreeNode - tree structures"),
        ("test_inductive_mining_enhanced.py", "Enhanced tests for main InductiveMining"),
        ("test_inductive_mining_infrequent.py", "Tests for InductiveMiningInfrequent"),
        ("test_inductive_mining_approximate.py", "Tests for InductiveMiningApproximate"),
        ("inductive_mining_test.py", "Original basic tests for InductiveMining"),
    ]
    
    for module, description in test_modules:
        print(f"📁 {module}")
        print(f"   {description}")
        print()


if __name__ == "__main__":
    # If --help or -h is provided, show help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print(__doc__)
        print()
        print("Usage:")
        print("  python test_runner.py                    # Run all tests")
        print("  python test_runner.py [module_name]      # Run specific test module")
        print("  python test_runner.py --info             # Show available test modules")
        print()
        print("Examples:")
        print("  python test_runner.py base_mining        # Run base mining tests")
        print("  python test_runner.py process_tree       # Run process tree tests")
        print("  python test_runner.py inductive_mining   # Run main inductive mining tests")
        sys.exit(0)
    
    # If --info is provided, show test modules info
    if len(sys.argv) > 1 and sys.argv[1] == '--info':
        print_test_modules_info()
        sys.exit(0)
    
    # Run the main test runner
    exit_code = main()
    sys.exit(exit_code) 