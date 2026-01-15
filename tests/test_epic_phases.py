"""
Tests for Phase 1-4 implementations
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path - must be done before any imports
test_dir = os.path.dirname(__file__)
src_dir = os.path.join(test_dir, "..", "src")
sys.path.insert(0, src_dir)


def test_semantic_deduplication_config():
    """Test semantic de-duplication configuration"""
    from models.config import SystemConfig
    
    config = SystemConfig(
        enable_semantic_deduplication=True,
        rule_similarity_threshold=0.8
    )
    
    assert config.enable_semantic_deduplication is True
    assert config.rule_similarity_threshold == 0.8
    print("✓ Semantic de-duplication config works")


def test_judge_model_config():
    """Test Judge model configuration"""
    from models.config import SystemConfig
    
    config = SystemConfig(
        enable_judge_model=True,
        judge_approval_required=True
    )
    
    assert config.enable_judge_model is True
    assert config.judge_approval_required is True
    print("✓ Judge model config works")


def test_confidence_throttling_config():
    """Test confidence-based throttling configuration"""
    from models.config import SystemConfig
    
    config = SystemConfig(
        enable_confidence_throttling=True,
        confidence_threshold=0.7
    )
    
    assert config.enable_confidence_throttling is True
    assert config.confidence_threshold == 0.7
    print("✓ Confidence throttling config works")


def test_regression_testing_config():
    """Test regression testing configuration"""
    from models.config import SystemConfig
    
    config = SystemConfig(
        enable_regression_testing=True,
        golden_dataset_max_size=100,
        regression_test_sample_size=10,
        regression_pass_threshold=0.9
    )
    
    assert config.enable_regression_testing is True
    assert config.golden_dataset_max_size == 100
    assert config.regression_test_sample_size == 10
    assert config.regression_pass_threshold == 0.9
    print("✓ Regression testing config works")


def test_golden_interaction():
    """Test GoldenInteraction model"""
    from core.golden_dataset import GoldenInteraction
    
    interaction = GoldenInteraction(
        user_query="What is 2+2?",
        expected_output="4",
        validation_rules=["LengthValidator"],
        tags=["math", "simple"]
    )
    
    assert interaction.user_query == "What is 2+2?"
    assert interaction.expected_output == "4"
    assert "LengthValidator" in interaction.validation_rules
    assert "math" in interaction.tags
    
    # Test to_dict and from_dict
    data = interaction.to_dict()
    restored = GoldenInteraction.from_dict(data)
    assert restored.user_query == interaction.user_query
    
    print("✓ GoldenInteraction model works")


def test_golden_dataset():
    """Test GoldenDataset functionality"""
    from core.golden_dataset import GoldenDataset
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "golden_dataset.json"
        dataset = GoldenDataset(storage_path, max_size=5)
        
        # Add some interactions
        dataset.add_interaction(
            user_query="Test query 1",
            output="Test output 1",
            instructions_version="v1",
            model_used="test-model",
            tags=["test"]
        )
        
        dataset.add_interaction(
            user_query="Test query 2",
            output="Test output 2",
            instructions_version="v1",
            model_used="test-model",
            tags=["test"]
        )
        
        assert len(dataset.interactions) == 2
        
        # Test duplicate detection
        dataset.add_interaction(
            user_query="Test query 1",  # Duplicate
            output="Different output",
            instructions_version="v1",
            model_used="test-model"
        )
        
        # Should still be 2 (duplicate not added)
        assert len(dataset.interactions) == 2
        
        # Test persistence
        dataset._save()
        assert storage_path.exists()
        
        # Load in new instance
        dataset2 = GoldenDataset(storage_path, max_size=5)
        assert len(dataset2.interactions) == 2
        
        print("✓ GoldenDataset works")


def test_integration():
    """Test full integration of new features"""
    from models.config import SystemConfig
    from core.instruction_manager import InstructionManager
    from core.critic_model import CriticModel
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        config = SystemConfig(
            instructions_dir=Path(tmpdir),
            enable_semantic_deduplication=True,
            enable_judge_model=True,
            enable_confidence_throttling=True,
            enable_regression_testing=True
        )
        
        instruction_manager = InstructionManager(config)
        critic = CriticModel(config, instruction_manager)
        
        # Check that components are initialized
        assert critic.config.enable_semantic_deduplication is True
        assert critic.config.enable_judge_model is True
        assert critic.config.enable_confidence_throttling is True
        
        # Judge model should be initialized
        assert critic.judge_model is not None
        
        # Golden dataset should be initialized
        assert instruction_manager.golden_dataset is not None
        
        print("✓ Full integration works")


if __name__ == "__main__":
    print("\n=== Running Phase 1-4 Tests ===\n")
    
    test_semantic_deduplication_config()
    test_judge_model_config()
    test_confidence_throttling_config()
    test_regression_testing_config()
    test_golden_interaction()
    test_golden_dataset()
    test_integration()
    
    print("\n=== All Phase 1-4 Tests Passed ===\n")

