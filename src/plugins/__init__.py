"""
Plugin System for AutonomAI

This module provides a production-grade plugin architecture that enables
third-party extensions for validators, workflow steps, optimizers, and more.

Usage:
    from src.plugins import PluginManager
    
    # Initialize plugin manager
    manager = PluginManager()
    
    # Discover and load plugins
    manager.discover_and_load_plugins(
        plugin_dirs=[Path("./plugins")],
        config_file=Path("./plugin_config.yaml")
    )
    
    # Get validators for pipeline
    validators = manager.get_validators_for_pipeline()
    for validator in validators:
        validation_pipeline.add_validator(validator)
"""

from .base import (
    BasePlugin,
    PluginMetadata,
    PluginConfig,
    PluginLifecycle,
)
from .registry import PluginRegistry
from .loader import PluginLoader
from .validators import ValidatorPlugin, PluginValidator
from .optimizers import OptimizerPlugin, FailureAnalyzerPlugin
from .workflow_steps import WorkflowStepPlugin
from .manager import PluginManager

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginConfig",
    "PluginLifecycle",
    "PluginRegistry",
    "PluginLoader",
    "ValidatorPlugin",
    "PluginValidator",
    "OptimizerPlugin",
    "FailureAnalyzerPlugin",
    "WorkflowStepPlugin",
    "PluginManager",
]
