"""
Example: Using Epic Enhancements (Phases 1-4)

This example demonstrates the new reliability and safety features:
1. Semantic De-duplication
2. Judge Model (Consensus Critic)
3. Automated Regression Testing
4. Confidence-Based Throttling
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src import SelfOptimizingSystem, JSONValidator, LengthValidator
from src.models.config import SystemConfig


def main():
    print("\n" + "="*70)
    print("Epic Enhancements Demo: Advanced Reliability Features")
    print("="*70 + "\n")
    
    # Configure system with all enhancements enabled
    config = SystemConfig(
        # Phase 1: Semantic De-duplication
        enable_semantic_deduplication=True,
        rule_similarity_threshold=0.8,
        
        # Phase 2: Judge Pattern
        enable_judge_model=True,
        judge_approval_required=True,
        
        # Phase 3: Regression Testing
        enable_regression_testing=True,
        golden_dataset_max_size=50,
        regression_test_sample_size=5,
        regression_pass_threshold=0.9,
        
        # Phase 4: Confidence Throttling
        enable_confidence_throttling=True,
        confidence_threshold=0.7,
        
        # Use mock models for demo
        main_model="mock-gpt-4",
        critic_model="mock-claude-3",
    )
    
    # Initialize system
    print("Initializing self-optimizing system with all enhancements...")
    system = SelfOptimizingSystem(config)
    
    # Add validators
    system.add_validator(JSONValidator(required_fields=["status", "message"]))
    system.add_validator(LengthValidator(min_length=20, max_length=500))
    
    print("✓ System initialized with:")
    print(f"  - Semantic De-duplication: {config.enable_semantic_deduplication}")
    print(f"  - Judge Model: {config.enable_judge_model}")
    print(f"  - Regression Testing: {config.enable_regression_testing}")
    print(f"  - Confidence Throttling: {config.enable_confidence_throttling}")
    print()
    
    # Example 1: Successful execution (adds to golden dataset)
    print("-" * 70)
    print("Example 1: Successful Execution")
    print("-" * 70)
    
    result = system.execute("Generate a JSON status message saying 'System operational'")
    
    print(f"Output: {result['output'][:100]}...")
    print(f"Validation passed: {result['validation_passed']}")
    
    if result['validation_passed']:
        print("✓ Success! This interaction was added to the golden dataset.")
        if system.instruction_manager.golden_dataset:
            total = len(system.instruction_manager.golden_dataset.interactions)
            print(f"  Golden dataset now has {total} interaction(s)")
    print()
    
    # Example 2: Another successful execution
    print("-" * 70)
    print("Example 2: Another Successful Execution")
    print("-" * 70)
    
    result = system.execute("Generate a JSON error message saying 'File not found'")
    
    print(f"Output: {result['output'][:100]}...")
    print(f"Validation passed: {result['validation_passed']}")
    print()
    
    # Example 3: Intentional failure to trigger optimization
    print("-" * 70)
    print("Example 3: Validation Failure (Triggers Optimization)")
    print("-" * 70)
    
    result = system.execute("Say hi")  # Too short, will fail validation
    
    print(f"Output: {result['output']}")
    print(f"Validation passed: {result['validation_passed']}")
    print(f"Optimization attempted: {result.get('optimization_attempted', False)}")
    
    if result.get('optimization_result'):
        opt_result = result['optimization_result']
        print(f"Optimization successful: {opt_result.get('success', False)}")
        
        if not opt_result.get('success'):
            print("\nOptimization was blocked by safety checks:")
            print("  Possible reasons:")
            print("  1. Confidence score too low (< 0.7)")
            print("  2. Judge rejected the proposal")
            print("  3. Regression tests failed")
            print("  4. Semantic duplicate detected")
            print("\n  Check 'instructions/pending_review.md' for details")
    print()
    
    # Show golden dataset status
    if system.instruction_manager.golden_dataset:
        print("-" * 70)
        print("Golden Dataset Status")
        print("-" * 70)
        
        dataset = system.instruction_manager.golden_dataset
        print(f"Total interactions collected: {len(dataset.interactions)}")
        
        if dataset.interactions:
            print("\nRecent interactions:")
            for i, interaction in enumerate(dataset.get_recent_interactions(3), 1):
                print(f"\n{i}. Query: {interaction.user_query[:50]}...")
                print(f"   Version: {interaction.instructions_version}")
                print(f"   Tags: {', '.join(interaction.tags)}")
        
        print()
    
    # Show system status
    print("-" * 70)
    print("System Status")
    print("-" * 70)
    
    status = system.get_status()
    print(f"Main Model: {status['config']['main_model']}")
    print(f"Critic Model: {status['config']['critic_model']}")
    print(f"Auto Optimization: {status['config']['enable_auto_optimization']}")
    print(f"Validators: {status['validation']['validators_count']}")
    print(f"Version: {status['versions']['latest'] or 'initial'}")
    print()
    
    # Show feature benefits
    print("-" * 70)
    print("Feature Benefits Demonstrated")
    print("-" * 70)
    print("""
Phase 1 - Semantic De-duplication:
  ✓ Prevents adding duplicate rules with similar meanings
  ✓ Keeps instruction set clean and focused
  ✓ Uses embeddings for semantic comparison

Phase 2 - Judge Model (Consensus Critic):
  ✓ Second model reviews all proposed changes
  ✓ Checks for contradictions with base instructions
  ✓ Provides detailed reasoning for decisions
  ✓ Routes rejections to pending review with feedback

Phase 3 - Automated Regression Testing:
  ✓ Collects successful interactions automatically
  ✓ Tests proposed changes against golden dataset
  ✓ Blocks changes that break previous successes
  ✓ Configurable pass threshold (default 90%)

Phase 4 - Confidence-Based Throttling:
  ✓ Only applies high-confidence changes automatically
  ✓ Routes low-confidence changes for human review
  ✓ Prevents unsafe or uncertain optimizations
  ✓ Maintains system quality standards
    """)
    
    print("-" * 70)
    print("Configuration Guide")
    print("-" * 70)
    print("""
Adjust safety levels by modifying SystemConfig:

Conservative (Production):
  confidence_threshold=0.85        # High confidence required
  rule_similarity_threshold=0.9     # Very strict dedup
  regression_pass_threshold=0.95    # 95% tests must pass
  judge_approval_required=True      # Always use judge

Balanced (Default):
  confidence_threshold=0.7          # Good confidence
  rule_similarity_threshold=0.8     # Reasonable dedup
  regression_pass_threshold=0.9     # 90% tests must pass
  judge_approval_required=True      # Use judge

Aggressive (Development):
  confidence_threshold=0.6          # Lower bar
  rule_similarity_threshold=0.7     # More lenient dedup
  regression_pass_threshold=0.8     # 80% tests ok
  judge_approval_required=False     # Skip judge for speed
    """)
    
    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70 + "\n")
    
    print("Next steps:")
    print("1. Check 'instructions/instructions.md' for system state")
    print("2. Review 'instructions/pending_review.md' for blocked changes")
    print("3. Examine 'instructions/golden_dataset.json' for collected tests")
    print("4. Adjust configuration thresholds based on your needs")
    print()


if __name__ == "__main__":
    main()
