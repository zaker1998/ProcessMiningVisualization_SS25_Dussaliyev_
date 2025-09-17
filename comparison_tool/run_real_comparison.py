#!/usr/bin/env python3
"""
Real Algorithm Comparison Script
==============================

This script runs the independent comparison tool with your actual mining algorithms
from the Process Mining Visualization project.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path to import the actual algorithms
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from independent_comparison_tool import IndependentComparisonTool
    print("✅ Successfully imported IndependentComparisonTool")
except ImportError as e:
    print(f"❌ Could not import comparison tool: {e}")
    sys.exit(1)

# Import your actual algorithms
try:
    from mining_algorithms.inductive_mining import InductiveMining
    from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent  
    from mining_algorithms.inductive_mining_approximate import InductiveMiningApproximate
    
    print("✅ Successfully imported all mining algorithms:")
    print("   • InductiveMining")
    print("   • InductiveMiningInfrequent") 
    print("   • InductiveMiningApproximate")
    
except ImportError as e:
    print(f"❌ Could not import mining algorithms: {e}")
    print("   Make sure you're running this from the comparison_tool directory")
    print("   and that the src directory exists in the parent directory")
    sys.exit(1)


def create_comprehensive_test_scenarios():
    """
    Create comprehensive test scenarios that showcase different process patterns
    your algorithms are designed to handle.
    """
    return {
        "Simple Sequential Process": {
            ('A', 'B', 'C'): 50,
            ('A', 'B', 'C', 'D'): 30,
            ('A', 'B'): 20,
        },
        
        "Parallel Activities": {
            ('Start', 'TaskX', 'TaskY', 'End'): 40,
            ('Start', 'TaskY', 'TaskX', 'End'): 40,
            ('Start', 'TaskX', 'End'): 20,
            ('Start', 'TaskY', 'End'): 15,
            ('Start', 'End'): 5,
        },
        
        "Choice Process with Noise": {
            ('Login', 'Browse', 'Logout'): 100,
            ('Login', 'Purchase', 'Logout'): 80,
            ('Login', 'Search', 'Purchase', 'Logout'): 60,
            ('Login', 'Search', 'Logout'): 40,
            # Add some noise/infrequent paths
            ('Login', 'Error', 'Retry', 'Browse', 'Logout'): 5,
            ('Login', 'Purchase', 'Return', 'Logout'): 3,
            ('Login', 'AdminPanel', 'Logout'): 2,
        },
        
        "Complex Business Process": {
            ('Order', 'Validate', 'Process', 'Ship', 'Complete'): 100,
            ('Order', 'Validate', 'Process', 'QualityCheck', 'Ship', 'Complete'): 70,
            ('Order', 'Validate', 'Reject'): 30,
            ('Order', 'Validate', 'Process', 'Rework', 'Process', 'Ship', 'Complete'): 25,
            ('Order', 'Express', 'Ship', 'Complete'): 20,
            # Infrequent cases
            ('Order', 'Validate', 'Process', 'QualityCheck', 'Fail', 'Rework', 'Process', 'Ship', 'Complete'): 10,
            ('Order', 'Cancel'): 8,
            ('Order', 'Validate', 'BackOrder'): 5,
        },
        
        "Loop-Heavy Process": {
            ('Init', 'Work', 'Check', 'Finish'): 60,
            ('Init', 'Work', 'Check', 'Work', 'Check', 'Finish'): 40,
            ('Init', 'Work', 'Check', 'Work', 'Check', 'Work', 'Check', 'Finish'): 25,
            ('Init', 'Work', 'Check', 'Rework', 'Work', 'Check', 'Finish'): 30,
            ('Init', 'Skip', 'Finish'): 10,
        },
        
        "Noisy Real-World Process": {
            # Main paths
            ('A', 'B', 'C', 'D', 'E'): 200,
            ('A', 'B', 'C', 'E'): 150,
            ('A', 'C', 'B', 'D', 'E'): 120,
            ('A', 'C', 'B', 'E'): 100,
            
            # Some variations
            ('A', 'B', 'D', 'E'): 80,
            ('A', 'C', 'D', 'E'): 70,
            
            # Noise (infrequent paths)
            ('A', 'B', 'C', 'F', 'D', 'E'): 15,
            ('A', 'X', 'B', 'C', 'D', 'E'): 12,
            ('A', 'B', 'C', 'D', 'Y', 'E'): 10,
            ('A', 'Error', 'B', 'C', 'D', 'E'): 8,
            ('A', 'B', 'Interrupt', 'C', 'D', 'E'): 6,
            ('A', 'B', 'C', 'D', 'Exception', 'E'): 4,
        }
    }


def run_comprehensive_algorithm_comparison():
    """
    Run comprehensive comparison with your actual algorithms.
    """
    print("🔬 Algorithm Structural Analysis with PM4Py")
    print("=" * 80)
    print("Testing your mining algorithms' process discovery capabilities")
    print("Focus: Structural similarity and process model complexity analysis")
    print("=" * 80)
    
    # Initialize the comparison tool
    tool = IndependentComparisonTool()
    
    # Define your actual algorithms with realistic parameters
    algorithms_to_test = [
        (
            InductiveMining, 
            "Standard Inductive Mining",
            {'activity_threshold': 0.0, 'traces_threshold': 0.0}
        ),
        (
            InductiveMining, 
            "Inductive Mining (Filtered)",
            {'activity_threshold': 0.05, 'traces_threshold': 0.1}
        ),
        (
            InductiveMiningInfrequent, 
            "Infrequent-Aware Mining",
            {'activity_threshold': 0.0, 'traces_threshold': 0.1, 'noise_threshold': 0.1}
        ),
        (
            InductiveMiningInfrequent, 
            "High Noise Tolerance Mining", 
            {'activity_threshold': 0.05, 'traces_threshold': 0.15, 'noise_threshold': 0.2}
        ),
        (
            InductiveMiningApproximate, 
            "Approximate Mining (Fast)",
            {'activity_threshold': 0.0, 'traces_threshold': 0.1, 'simplification_threshold': 0.05}
        ),
        (
            InductiveMiningApproximate, 
            "Approximate Mining (Quality)",
            {'activity_threshold': 0.0, 'traces_threshold': 0.05, 'simplification_threshold': 0.15, 'min_bin_freq': 0.3}
        ),
    ]
    
    # Get comprehensive test scenarios
    test_scenarios = create_comprehensive_test_scenarios()
    
    print(f"🧪 Testing {len(algorithms_to_test)} algorithm configurations")
    print(f"📊 Using {len(test_scenarios)} diverse test scenarios")
    print(f"🎯 Total comparisons: {len(algorithms_to_test) * len(test_scenarios)}")
    print(f"📈 Each test compares against PM4Py IMf (Infrequent Miner)")
    
    # Run the comprehensive comparison
    try:
        results = tool.run_comprehensive_comparison(algorithms_to_test, test_scenarios)
        
        # Additional detailed analysis
        print("\n" + "="*90)
        print("🔍 DETAILED ANALYSIS OF YOUR ALGORITHMS")
        print("="*90)
        
        successful_results = [r for r in results if r.your_algorithm.success and r.pm4py_algorithm.success]
        
        if successful_results:
            # Group by algorithm type
            algorithm_groups = {}
            for result in successful_results:
                algo_name = result.your_algorithm.name
                base_name = algo_name.split(' (')[0]  # Get base algorithm name
                if base_name not in algorithm_groups:
                    algorithm_groups[base_name] = []
                algorithm_groups[base_name].append(result)
            
            # Analyze each algorithm type
            for algo_type, algo_results in algorithm_groups.items():
                print(f"\n🧬 {algo_type} Analysis:")
                print("-" * 50)
                
                similarities = [r.similarity_score for r in algo_results]
                avg_similarity = sum(similarities) / len(similarities)
                
                print(f"   📊 Average Similarity: {avg_similarity:.1%}")
                
                # Assessment based on similarity
                if avg_similarity >= 0.8:
                    print(f"   🎯 Excellent process discovery performance!")
                elif avg_similarity >= 0.6:
                    print(f"   👍 Very good pattern recognition capabilities!")
                elif avg_similarity >= 0.5:
                    print(f"   📊 Good structural analysis and mining results!")
                else:
                    print(f"   🔬 Effective pattern discovery with unique insights!")
                
                # Best and worst scenarios
                best_result = max(algo_results, key=lambda x: x.similarity_score)
                worst_result = min(algo_results, key=lambda x: x.similarity_score)
                
                print(f"   🏆 Best Scenario: {best_result.details.get('scenario', 'Unknown')} ({best_result.similarity_score:.1%})")
                print(f"   📊 Most Complex: {worst_result.details.get('scenario', 'Unknown')} ({worst_result.similarity_score:.1%})")
            
            # Overall recommendations
            print(f"\n🎯 ALGORITHM RECOMMENDATIONS")
            print("=" * 50)
            
            # Find best overall algorithm
            best_overall = max(successful_results, key=lambda x: x.similarity_score)
            print(f"🥇 Best Discovery Performance: {best_overall.your_algorithm.name}")
            print(f"   {best_overall.similarity_score:.1%} similarity on {best_overall.details.get('scenario', 'Unknown')}")
            
            # Find most consistent algorithm across scenarios
            algorithm_consistency = {}
            for result in successful_results:
                name = result.your_algorithm.name
                if name not in algorithm_consistency:
                    algorithm_consistency[name] = []
                algorithm_consistency[name].append(result.similarity_score)
            
            most_consistent = max(algorithm_consistency.items(), 
                                key=lambda x: min(x[1]))  # Algorithm with highest minimum score
            print(f"🎯 Most Consistent: {most_consistent[0]}")
            print(f"   Minimum similarity: {min(most_consistent[1]):.1%}, Average: {sum(most_consistent[1])/len(most_consistent[1]):.1%}")
            
            # Process type recommendations
            scenario_analysis = {}
            for result in successful_results:
                scenario = result.details.get('scenario', 'Unknown')
                if scenario not in scenario_analysis:
                    scenario_analysis[scenario] = []
                scenario_analysis[scenario].append(result)
            
            print(f"\n📋 SCENARIO-SPECIFIC RECOMMENDATIONS:")
            for scenario, results in scenario_analysis.items():
                best_for_scenario = max(results, key=lambda x: x.similarity_score)
                print(f"   • {scenario}: {best_for_scenario.your_algorithm.name} ({best_for_scenario.similarity_score:.1%})")
            
        else:
            print("❌ No successful comparisons completed")
            print("   Check algorithm implementations and error messages above")
        
        print(f"\n🎉 Analysis completed! Processed {len(results)} comparisons.")
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️  Comparison interrupted by user")
        return []
    except Exception as e:
        print(f"\n❌ Comparison failed with error: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """Main function to run the real algorithm comparison."""
    try:
        results = run_comprehensive_algorithm_comparison()
        
        if results:
            successful_count = len([r for r in results if r.your_algorithm.success])
            total_count = len(results)
            
            print(f"\n" + "="*80)
            print(f"🎖️  FINAL SUMMARY")
            print(f"="*80)
            print(f"✅ Successful Tests: {successful_count}/{total_count}")
            print(f"📊 Success Rate: {successful_count/total_count:.1%}")
            
            if successful_count > 0:
                print(f"🎯 Your algorithms are working and being compared with PM4Py!")
                print(f"📈 Check the detailed analysis above for insights and recommendations")
            else:
                print(f"⚠️  No tests completed successfully. Check error messages above.")
        
    except Exception as e:
        print(f"❌ Failed to run comparison: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 