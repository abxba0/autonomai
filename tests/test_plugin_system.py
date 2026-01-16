"""
Tests for the plugin system.
"""

import pytest
from pathlib import Path
from typing import Optional, Dict, Any

from src.plugins import (
    BasePlugin,
    PluginMetadata,
    PluginConfig,
    PluginLifecycle,
    PluginRegistry,
    PluginLoader,
    PluginManager,
    ValidatorPlugin,
    OptimizerPlugin,
    WorkflowStepPlugin,
)
from src.core.validator import BaseValidator, ValidationResult
from src.models.failure import FailureEntry
from src.models.critic_response import CriticResponse
from src.models.workflow import WorkflowStep, StepStatus


# Mock plugins for testing
class MockValidatorPlugin(ValidatorPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="mock_validator",
            version="1.0.0",
            author="Test",
            description="Mock validator for testing",
            plugin_type="validator",
        )
    
    def create_validator(self):
        class MockValidator(BaseValidator):
            def validate(self, output, context=None):
                return ValidationResult(passed=True, validator_name="mock_validator")
        return MockValidator("mock_validator")


class MockOptimizerPlugin(OptimizerPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="mock_optimizer",
            version="1.0.0",
            author="Test",
            description="Mock optimizer for testing",
            plugin_type="optimizer",
        )
    
    def can_handle(self, failure):
        return True
    
    def analyze_failure(self, failure, current_instructions, context=None):
        return CriticResponse(
            should_update=True,
            confidence=0.8,
            proposed_changes="Test changes",
            reasoning="Test reasoning",
        )


class MockWorkflowStepPlugin(WorkflowStepPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="mock_workflow_step",
            version="1.0.0",
            author="Test",
            description="Mock workflow step for testing",
            plugin_type="workflow_step",
        )
    
    def can_execute(self, step):
        return step.step_type == "mock"
    
    def execute_step(self, step, context):
        return StepStatus.COMPLETED, {"result": "success"}


class TestPluginMetadata:
    def test_metadata_creation(self):
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test description",
            plugin_type="validator",
        )
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.plugin_type == "validator"
    
    def test_metadata_with_optional_fields(self):
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test description",
            plugin_type="validator",
            homepage="https://example.com",
            license="MIT",
            dependencies=["dep1", "dep2"],
            tags=["tag1", "tag2"],
        )
        assert metadata.homepage == "https://example.com"
        assert len(metadata.dependencies) == 2
        assert len(metadata.tags) == 2


class TestPluginConfig:
    def test_config_defaults(self):
        config = PluginConfig()
        assert config.enabled is True
        assert config.priority == 100
        assert len(config.settings) == 0
    
    def test_config_get(self):
        config = PluginConfig(
            settings={"key1": "value1", "key2": 42}
        )
        assert config.get("key1") == "value1"
        assert config.get("key2") == 42
        assert config.get("key3", "default") == "default"


class TestPluginRegistry:
    def test_register_plugin(self):
        registry = PluginRegistry()
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert registry.register(plugin) is True
        assert registry.get("mock_validator") == plugin
    
    def test_register_duplicate_plugin(self):
        registry = PluginRegistry()
        plugin1 = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        plugin2 = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert registry.register(plugin1) is True
        assert registry.register(plugin2) is False
    
    def test_unregister_plugin(self):
        registry = PluginRegistry()
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        registry.register(plugin)
        assert registry.unregister("mock_validator") is True
        assert registry.get("mock_validator") is None
    
    def test_get_by_type(self):
        registry = PluginRegistry()
        
        validator = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        optimizer = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        
        registry.register(validator)
        registry.register(optimizer)
        
        validators = registry.get_by_type("validator")
        assert len(validators) == 1
        assert validators[0].metadata.name == "mock_validator"
        
        optimizers = registry.get_by_type("optimizer")
        assert len(optimizers) == 1
        assert optimizers[0].metadata.name == "mock_optimizer"
    
    def test_get_enabled(self):
        registry = PluginRegistry()
        
        enabled_plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig(enabled=True)
        )
        disabled_plugin = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig(enabled=False)
        )
        
        registry.register(enabled_plugin)
        registry.register(disabled_plugin)
        
        # Initialize plugins
        registry.initialize_all()
        
        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].metadata.name == "mock_validator"
    
    def test_initialize_all(self):
        registry = PluginRegistry()
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        registry.register(plugin)
        results = registry.initialize_all()
        
        assert results["mock_validator"] is True
        assert plugin.lifecycle_state == PluginLifecycle.ACTIVE
    
    def test_priority_sorting(self):
        registry = PluginRegistry()
        
        high_priority = MockValidatorPlugin(
            PluginMetadata(
                name="high_priority",
                version="1.0.0",
                author="Test",
                description="High priority",
                plugin_type="validator",
            ),
            PluginConfig(priority=10)
        )
        
        low_priority = MockValidatorPlugin(
            PluginMetadata(
                name="low_priority",
                version="1.0.0",
                author="Test",
                description="Low priority",
                plugin_type="validator",
            ),
            PluginConfig(priority=100)
        )
        
        registry.register(low_priority)
        registry.register(high_priority)
        
        validators = registry.get_by_type("validator")
        assert validators[0].metadata.name == "high_priority"
        assert validators[1].metadata.name == "low_priority"


class TestPluginLoader:
    def test_register_plugin(self):
        registry = PluginRegistry()
        loader = PluginLoader(registry)
        
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert loader.register_plugin(plugin) is True
        assert registry.get("mock_validator") is not None


class TestPluginManager:
    def test_manager_initialization(self):
        manager = PluginManager()
        assert manager.registry is not None
        assert manager.loader is not None
    
    def test_register_validator_plugin(self):
        manager = PluginManager()
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert manager.register_plugin(plugin) is True
        validators = manager.get_validator_plugins()
        assert len(validators) == 1
    
    def test_register_optimizer_plugin(self):
        manager = PluginManager()
        plugin = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert manager.register_plugin(plugin) is True
        optimizers = manager.get_optimizer_plugins()
        assert len(optimizers) == 1
    
    def test_register_workflow_step_plugin(self):
        manager = PluginManager()
        plugin = MockWorkflowStepPlugin(
            MockWorkflowStepPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert manager.register_plugin(plugin) is True
        workflow_plugins = manager.get_workflow_step_plugins()
        assert len(workflow_plugins) == 1
    
    def test_find_optimizer_for_failure(self):
        manager = PluginManager()
        plugin = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        
        manager.register_plugin(plugin)
        
        # Create a mock failure
        failure = FailureEntry(
            query="test query",
            output="test output",
            error_message="test error",
        )
        
        optimizer = manager.find_optimizer_for_failure(failure)
        assert optimizer is not None
        assert optimizer.metadata.name == "mock_optimizer"
    
    def test_find_workflow_step_executor(self):
        manager = PluginManager()
        plugin = MockWorkflowStepPlugin(
            MockWorkflowStepPlugin.get_metadata(),
            PluginConfig()
        )
        
        manager.register_plugin(plugin)
        
        # Create a mock workflow step
        step = WorkflowStep(
            step_id="step1",
            step_type="mock",
            description="Test step",
            inputs={},
            outputs={},
            dependencies=[],
        )
        
        executor = manager.find_workflow_step_executor(step)
        assert executor is not None
        assert executor.metadata.name == "mock_workflow_step"
    
    def test_enable_disable_plugin(self):
        manager = PluginManager()
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig(enabled=True)
        )
        
        manager.register_plugin(plugin)
        
        # Disable plugin
        assert manager.disable_plugin("mock_validator") is True
        assert plugin.config.enabled is False
        
        # Enable plugin
        assert manager.enable_plugin("mock_validator") is True
        assert plugin.config.enabled is True
    
    def test_list_plugins(self):
        manager = PluginManager()
        
        validator = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        optimizer = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        
        manager.register_plugin(validator)
        manager.register_plugin(optimizer)
        
        plugins = manager.list_plugins()
        assert len(plugins) == 2
        
        validator_plugins = manager.list_plugins("validator")
        assert len(validator_plugins) == 1
        assert validator_plugins[0]["name"] == "mock_validator"


class TestValidatorPlugin:
    def test_validator_plugin_initialization(self):
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        
        assert plugin.initialize() is True
        assert plugin.validator is not None
    
    def test_validator_plugin_validation(self):
        plugin = MockValidatorPlugin(
            MockValidatorPlugin.get_metadata(),
            PluginConfig()
        )
        plugin.initialize()
        
        result = plugin.validator.validate("test output")
        assert result.passed is True


class TestOptimizerPlugin:
    def test_optimizer_plugin_can_handle(self):
        plugin = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        plugin.initialize()
        
        failure = FailureEntry(
            query="test",
            output="output",
            error_message="error",
        )
        
        assert plugin.can_handle(failure) is True
    
    def test_optimizer_plugin_analyze_failure(self):
        plugin = MockOptimizerPlugin(
            MockOptimizerPlugin.get_metadata(),
            PluginConfig()
        )
        plugin.initialize()
        
        failure = FailureEntry(
            query="test",
            output="output",
            error_message="error",
        )
        
        response = plugin.analyze_failure(failure, "current instructions")
        assert response is not None
        assert response.should_update is True


class TestWorkflowStepPlugin:
    def test_workflow_step_plugin_can_execute(self):
        plugin = MockWorkflowStepPlugin(
            MockWorkflowStepPlugin.get_metadata(),
            PluginConfig()
        )
        plugin.initialize()
        
        step = WorkflowStep(
            step_id="step1",
            step_type="mock",
            description="Test",
            inputs={},
            outputs={},
            dependencies=[],
        )
        
        assert plugin.can_execute(step) is True
    
    def test_workflow_step_plugin_execute(self):
        plugin = MockWorkflowStepPlugin(
            MockWorkflowStepPlugin.get_metadata(),
            PluginConfig()
        )
        plugin.initialize()
        
        step = WorkflowStep(
            step_id="step1",
            step_type="mock",
            description="Test",
            inputs={},
            outputs={},
            dependencies=[],
        )
        
        status, outputs = plugin.execute_step(step, {})
        assert status == StepStatus.COMPLETED
        assert outputs["result"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
