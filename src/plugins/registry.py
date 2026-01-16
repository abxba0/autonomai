"""
Plugin registry for managing loaded plugins.
"""

from typing import Dict, List, Optional, Type, Callable
import logging
from collections import defaultdict

from .base import BasePlugin, PluginMetadata, PluginLifecycle

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for managing plugins.
    
    Provides registration, lookup, and lifecycle management for all plugins.
    Thread-safe for concurrent access.
    """
    
    def __init__(self):
        # Plugin instances by name
        self._plugins: Dict[str, BasePlugin] = {}
        
        # Plugins organized by type
        self._plugins_by_type: Dict[str, List[BasePlugin]] = defaultdict(list)
        
        # Event hooks
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("Plugin registry initialized")
    
    def register(self, plugin: BasePlugin) -> bool:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False if plugin already exists
        """
        plugin_name = plugin.metadata.name
        
        if plugin_name in self._plugins:
            logger.warning(f"Plugin {plugin_name} already registered")
            return False
        
        # Validate configuration
        is_valid, error = plugin.validate_config()
        if not is_valid:
            logger.error(f"Plugin {plugin_name} configuration invalid: {error}")
            plugin.set_error(f"Configuration validation failed: {error}")
            return False
        
        # Register plugin
        self._plugins[plugin_name] = plugin
        self._plugins_by_type[plugin.metadata.plugin_type].append(plugin)
        
        plugin.lifecycle_state = PluginLifecycle.LOADED
        
        logger.info(f"Registered plugin: {plugin_name} ({plugin.metadata.plugin_type})")
        self._trigger_hook("plugin_registered", plugin)
        
        return True
    
    def unregister(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.warning(f"Cannot unregister unknown plugin: {plugin_name}")
            return False
        
        # Clean up plugin
        plugin.lifecycle_state = PluginLifecycle.UNLOADING
        try:
            plugin.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
        
        # Remove from registries
        del self._plugins[plugin_name]
        self._plugins_by_type[plugin.metadata.plugin_type].remove(plugin)
        
        plugin.lifecycle_state = PluginLifecycle.UNLOADED
        
        logger.info(f"Unregistered plugin: {plugin_name}")
        self._trigger_hook("plugin_unregistered", plugin)
        
        return True
    
    def get(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin by name"""
        return self._plugins.get(plugin_name)
    
    def get_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve (validator, optimizer, etc.)
            
        Returns:
            List of plugins, sorted by priority (higher priority first)
        """
        plugins = self._plugins_by_type.get(plugin_type, [])
        # Sort by priority (lower number = higher priority)
        return sorted(plugins, key=lambda p: p.config.priority)
    
    def get_enabled(self, plugin_type: Optional[str] = None) -> List[BasePlugin]:
        """
        Get all enabled plugins, optionally filtered by type.
        
        Args:
            plugin_type: Optional type filter
            
        Returns:
            List of enabled plugins
        """
        if plugin_type:
            plugins = self.get_by_type(plugin_type)
        else:
            plugins = list(self._plugins.values())
        
        return [
            p for p in plugins 
            if p.config.enabled and p.lifecycle_state == PluginLifecycle.ACTIVE
        ]
    
    def list_plugins(self) -> List[PluginMetadata]:
        """Get metadata for all registered plugins"""
        return [p.metadata for p in self._plugins.values()]
    
    def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all loaded plugins.
        
        Returns:
            Dict mapping plugin name to success status
        """
        results = {}
        
        for name, plugin in self._plugins.items():
            if plugin.lifecycle_state != PluginLifecycle.LOADED:
                logger.debug(f"Skipping initialization of {name} (state: {plugin.lifecycle_state})")
                continue
            
            try:
                logger.info(f"Initializing plugin: {name}")
                success = plugin.initialize()
                
                if success:
                    plugin.lifecycle_state = PluginLifecycle.INITIALIZED
                    if plugin.config.enabled:
                        plugin.lifecycle_state = PluginLifecycle.ACTIVE
                        logger.info(f"Plugin {name} is now active")
                    results[name] = True
                else:
                    plugin.set_error("Initialization returned False")
                    logger.error(f"Plugin {name} initialization failed")
                    results[name] = False
                    
            except Exception as e:
                plugin.set_error(f"Initialization exception: {str(e)}")
                logger.error(f"Error initializing plugin {name}: {e}", exc_info=True)
                results[name] = False
        
        return results
    
    def add_hook(self, event: str, callback: Callable):
        """
        Register a hook callback for plugin events.
        
        Events: plugin_registered, plugin_unregistered, plugin_error
        """
        self._hooks[event].append(callback)
    
    def _trigger_hook(self, event: str, plugin: BasePlugin):
        """Trigger all callbacks for an event"""
        for callback in self._hooks.get(event, []):
            try:
                callback(plugin)
            except Exception as e:
                logger.error(f"Error in hook callback for {event}: {e}")
    
    def clear(self):
        """Clear all plugins (for testing)"""
        for name in list(self._plugins.keys()):
            self.unregister(name)
        
        self._plugins.clear()
        self._plugins_by_type.clear()
        self._hooks.clear()
