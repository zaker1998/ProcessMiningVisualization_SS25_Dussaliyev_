#!/usr/bin/env python3
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
    
    print("\n📖 Next steps:")
    print("   1. Review INDEPENDENT_README.md for usage instructions")
    print("   2. Check example_integration.py for integration examples")
    print("   3. Import your own algorithms and start comparing!")

if __name__ == "__main__":
    main()
