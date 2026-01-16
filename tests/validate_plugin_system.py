#!/usr/bin/env python3
"""
Plugin System Validation Script

This script validates that the plugin system is working correctly
by running all major functionality tests.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.plugins import (
    PluginManager,
    PluginMetadata,
    PluginConfig,
    PluginLifecycle,
    ValidatorPlugin,
    OptimizerPlugin,
    WorkflowStepPlugin,
)
from src.core.validator import BaseValidator, ValidationResult
from src.models.config import FailureEntry
from src.models.critic_response import CriticResponse
from src.models.workflow import WorkflowStep, StepStatus


def test_plugin_creation():
    """Test that plugins can be created"""
    print("✓ Testing plugin creation...")
    
    class TestValidator(ValidatorPlugin):
        @classmethod
        def get_metadata(cls):
            return PluginMetadata(
                name="test_validator",
                version="1.0.0",
                author="Test",
                description="Test validator",
                plugin_type="validator",
            )
        
        def create_validator(self):
            class V(BaseValidator):
                def validate(self, output, context=None):
                    return ValidationResult(passed=True, validator_name=self.name)
            return V("test")
    
    plugin = TestValidator(TestValidator.get_metadata())
    assert plugin.initialize()
    print("  ✓ Plugin creation works")


def test_plugin_manager():
    """Test plugin manager functionality"""
    print("✓ Testing plugin manager...")
    
    manager = PluginManager()
    assert manager.registry is not None
    assert manager.loader is not None
    print("  ✓ Plugin manager initialization works")


def test_plugin_registration():
    """Test plugin registration"""
    print("✓ Testing plugin registration...")
    
    from examples.plugins.keyword_validator_plugin import KeywordValidatorPlugin
    
    manager = PluginManager()
    plugin = KeywordValidatorPlugin(
        KeywordValidatorPlugin.get_metadata(),
        PluginConfig(enabled=True)
    )
    
    assert manager.register_plugin(plugin)
    assert plugin.lifecycle_state == PluginLifecycle.ACTIVE
    print("  ✓ Plugin registration works")


def test_validator_integration():
    """Test validator plugin integration"""
    print("✓ Testing validator integration...")
    
    from src import SelfOptimizingSystem
    from examples.plugins.keyword_validator_plugin import KeywordValidatorPlugin
    
    system = SelfOptimizingSystem()
    manager = PluginManager()
    
    plugin = KeywordValidatorPlugin(
        KeywordValidatorPlugin.get_metadata(),
        PluginConfig(
            enabled=True,
            settings={
                "required_keywords": ["test"],
                "forbidden_keywords": [],
            }
        )
    )
    
    manager.register_plugin(plugin)
    
    for validator in manager.get_validators_for_pipeline():
        system.add_validator(validator)
    
    # Test validation
    passed, results = system.validation_pipeline.validate("This is a test")
    assert passed
    print("  ✓ Validator integration works")


def test_optimizer_plugin():
    """Test optimizer plugin"""
    print("✓ Testing optimizer plugin...")
    
    from examples.plugins.failure_analyzer_plugin import PatternAnalyzerPlugin
    
    manager = PluginManager()
    plugin = PatternAnalyzerPlugin(
        PatternAnalyzerPlugin.get_metadata(),
        PluginConfig(enabled=True)
    )
    
    assert manager.register_plugin(plugin)
    
    failure = FailureEntry(
        trigger_type="auto_validation",
        failure_description="Test failure",
    )
    
    optimizer = manager.find_optimizer_for_failure(failure)
    assert optimizer is not None
    print("  ✓ Optimizer plugin works")


def test_workflow_step_plugin():
    """Test workflow step plugin"""
    print("✓ Testing workflow step plugin...")
    
    from examples.plugins.workflow_step_plugin import DataTransformStepPlugin
    
    manager = PluginManager()
    plugin = DataTransformStepPlugin(
        DataTransformStepPlugin.get_metadata(),
        PluginConfig(enabled=True)
    )
    
    assert manager.register_plugin(plugin)
    
    step = WorkflowStep(name="test", description="uppercase: test")
    step.step_type = "data_transform"
    step.inputs = {"data": "hello"}
    
    executor = manager.find_workflow_step_executor(step)
    assert executor is not None
    
    status, outputs = executor.execute_step(step, {})
    assert status == StepStatus.COMPLETED
    assert outputs["transformed_data"] == "HELLO"
    print("  ✓ Workflow step plugin works")


def test_plugin_lifecycle():
    """Test plugin lifecycle management"""
    print("✓ Testing plugin lifecycle...")
    
    from examples.plugins.keyword_validator_plugin import KeywordValidatorPlugin
    
    manager = PluginManager()
    plugin = KeywordValidatorPlugin(
        KeywordValidatorPlugin.get_metadata(),
        PluginConfig(enabled=True)
    )
    
    # Register
    assert manager.register_plugin(plugin)
    assert plugin.lifecycle_state == PluginLifecycle.ACTIVE
    
    # Disable
    assert manager.disable_plugin("keyword_validator")
    assert not plugin.config.enabled
    
    # Enable
    assert manager.enable_plugin("keyword_validator")
    assert plugin.config.enabled
    
    # Unload
    assert manager.unload_plugin("keyword_validator")
    assert manager.registry.get("keyword_validator") is None
    
    print("  ✓ Plugin lifecycle management works")


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Plugin System Validation")
    print("=" * 60)
    print()
    
    tests = [
        test_plugin_creation,
        test_plugin_manager,
        test_plugin_registration,
        test_validator_integration,
        test_optimizer_plugin,
        test_workflow_step_plugin,
        test_plugin_lifecycle,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Validation Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✓ All validation tests passed!")
        print()
        print("Plugin system is ready for production use.")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
