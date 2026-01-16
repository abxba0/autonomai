"""
Plugin manager for coordinating plugin system components.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base import BasePlugin, PluginMetadata, PluginConfig, PluginLifecycle
from .registry import PluginRegistry
from .loader import PluginLoader
from .validators import ValidatorPlugin, PluginValidator
from .optimizers import OptimizerPlugin, FailureAnalyzerPlugin
from .workflow_steps import WorkflowStepPlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    High-level manager for the plugin system.
    
    Provides a unified interface for:
    - Loading plugins from various sources
    - Managing plugin lifecycle
    - Querying available plugins
    - Integrating plugins with system components
    """
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)
        
        logger.info("Plugin manager initialized")
    
    def discover_and_load_plugins(
        self,
        entrypoint_group: str = "autonomai.plugins",
        plugin_dirs: Optional[List[Path]] = None,
        config_file: Optional[Path] = None
    ) -> Dict[str, List[str]]:
        """
        Discover and load plugins from all configured sources.
        
        Args:
            entrypoint_group: Entry point group name
            plugin_dirs: List of directories to scan for plugins
            config_file: Path to plugin configuration file
            
        Returns:
            Dictionary mapping source to list of loaded plugin names
        """
        results = {}
        
        # Load from entry points
        logger.info("Loading plugins from entry points...")
        results["entrypoints"] = self.loader.load_from_entrypoints(entrypoint_group)
        
        # Load from directories
        if plugin_dirs:
            results["directories"] = []
            for directory in plugin_dirs:
                logger.info(f"Loading plugins from directory: {directory}")
                loaded = self.loader.load_from_directory(directory)
                results["directories"].extend(loaded)
        
        # Load from config file
        if config_file:
            logger.info(f"Loading plugins from config: {config_file}")
            results["config"] = self.loader.load_from_config(config_file)
        
        # Initialize all loaded plugins
        logger.info("Initializing plugins...")
        init_results = self.registry.initialize_all()
        
        logger.info(f"Plugin discovery complete: {sum(len(v) for v in results.values())} plugins loaded")
        
        return results
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register and initialize a plugin instance.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registered and initialized successfully
        """
        if not self.loader.register_plugin(plugin):
            return False
        
        # Initialize the plugin
        try:
            if plugin.initialize():
                plugin.lifecycle_state = PluginLifecycle.INITIALIZED
                if plugin.config.enabled:
                    plugin.lifecycle_state = PluginLifecycle.ACTIVE
                return True
            else:
                plugin.set_error("Initialization returned False")
                return False
        except Exception as e:
            plugin.set_error(f"Initialization failed: {e}")
            logger.error(f"Failed to initialize plugin {plugin.metadata.name}: {e}")
            return False
    
    def get_validator_plugins(self) -> List[ValidatorPlugin]:
        """Get all enabled validator plugins"""
        plugins = self.registry.get_enabled("validator")
        return [p for p in plugins if isinstance(p, ValidatorPlugin)]
    
    def get_optimizer_plugins(self) -> List[OptimizerPlugin]:
        """Get all enabled optimizer plugins"""
        plugins = self.registry.get_enabled("optimizer")
        return [p for p in plugins if isinstance(p, OptimizerPlugin)]
    
    def get_workflow_step_plugins(self) -> List[WorkflowStepPlugin]:
        """Get all enabled workflow step plugins"""
        plugins = self.registry.get_enabled("workflow_step")
        return [p for p in plugins if isinstance(p, WorkflowStepPlugin)]
    
    def get_validators_for_pipeline(self) -> List[PluginValidator]:
        """
        Get validator wrappers ready for use in ValidationPipeline.
        
        Returns:
            List of PluginValidator instances that can be added to a pipeline
        """
        return [
            PluginValidator(plugin)
            for plugin in self.get_validator_plugins()
        ]
    
    def find_optimizer_for_failure(self, failure) -> Optional[OptimizerPlugin]:
        """
        Find the best optimizer plugin to handle a specific failure.
        
        Args:
            failure: FailureEntry to analyze
            
        Returns:
            OptimizerPlugin that can handle the failure, or None
        """
        for plugin in self.get_optimizer_plugins():
            try:
                if plugin.can_handle(failure):
                    return plugin
            except Exception as e:
                logger.error(f"Error checking if {plugin.metadata.name} can handle failure: {e}")
        
        return None
    
    def find_workflow_step_executor(self, step) -> Optional[WorkflowStepPlugin]:
        """
        Find a plugin that can execute a specific workflow step.
        
        Args:
            step: WorkflowStep to execute
            
        Returns:
            WorkflowStepPlugin that can execute the step, or None
        """
        for plugin in self.get_workflow_step_plugins():
            try:
                if plugin.can_execute(step):
                    return plugin
            except Exception as e:
                logger.error(f"Error checking if {plugin.metadata.name} can execute step: {e}")
        
        return None
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get information about loaded plugins.
        
        Args:
            plugin_type: Optional filter by type
            
        Returns:
            List of plugin information dictionaries
        """
        if plugin_type:
            plugins = self.registry.get_by_type(plugin_type)
        else:
            plugins = list(self.registry._plugins.values())
        
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "type": p.metadata.plugin_type,
                "author": p.metadata.author,
                "description": p.metadata.description,
                "enabled": p.config.enabled,
                "state": p.lifecycle_state.value,
                "priority": p.config.priority,
                "error": p.error_message if p.lifecycle_state == PluginLifecycle.ERROR else None,
            }
            for p in plugins
        ]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin by name"""
        plugin = self.registry.get(plugin_name)
        if not plugin:
            return False
        
        plugin.config.enabled = True
        if plugin.lifecycle_state == PluginLifecycle.INITIALIZED:
            plugin.lifecycle_state = PluginLifecycle.ACTIVE
        
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin by name"""
        plugin = self.registry.get(plugin_name)
        if not plugin:
            return False
        
        plugin.config.enabled = False
        if plugin.lifecycle_state == PluginLifecycle.ACTIVE:
            plugin.lifecycle_state = PluginLifecycle.INITIALIZED
        
        return True
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name"""
        return self.registry.unregister(plugin_name)
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin (unload and load again).
        
        Note: This works best for plugins loaded from files,
        not for entry points which are cached by Python.
        """
        plugin = self.registry.get(plugin_name)
        if not plugin:
            return False
        
        # Store plugin info
        plugin_class = type(plugin)
        config = plugin.config
        
        # Unload
        if not self.unload_plugin(plugin_name):
            return False
        
        # Reload (create new instance)
        try:
            new_plugin = plugin_class(plugin.metadata, config)
            return self.register_plugin(new_plugin)
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return False
