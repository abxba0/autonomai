"""
Plugin loader with support for multiple discovery mechanisms.
"""

import importlib
import importlib.util
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
import json
import yaml

from .base import BasePlugin, PluginMetadata, PluginConfig
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Loads plugins from various sources.
    
    Supports:
    - Entry points (pkg_resources/importlib.metadata)
    - Directory scanning for .py files
    - Configuration file (YAML/JSON)
    - Explicit plugin instances
    """
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._loaded_modules = set()
    
    def load_from_entrypoints(self, group: str = "autonomai.plugins") -> List[str]:
        """
        Load plugins registered as entry points.
        
        In setup.py or pyproject.toml, plugins should be registered like:
        
        [project.entry-points."autonomai.plugins"]
        my_plugin = "my_package.plugin:MyPlugin"
        
        Args:
            group: Entry point group name
            
        Returns:
            List of loaded plugin names
        """
        loaded = []
        
        try:
            # Try importlib.metadata first (Python 3.8+)
            try:
                from importlib.metadata import entry_points
            except ImportError:
                # Fallback to pkg_resources
                try:
                    import pkg_resources
                    entry_points_dict = {
                        group: pkg_resources.iter_entry_points(group)
                    }
                    
                    for ep in entry_points_dict.get(group, []):
                        try:
                            plugin_class = ep.load()
                            plugin = self._instantiate_plugin(plugin_class)
                            if plugin and self.registry.register(plugin):
                                loaded.append(plugin.metadata.name)
                                logger.info(f"Loaded plugin from entry point: {ep.name}")
                        except Exception as e:
                            logger.error(f"Failed to load entry point {ep.name}: {e}")
                    
                    return loaded
                except ImportError:
                    logger.warning("Neither importlib.metadata nor pkg_resources available")
                    return loaded
            
            # Use importlib.metadata
            eps = entry_points()
            
            # Handle different return types across Python versions
            if hasattr(eps, 'select'):
                # Python 3.10+
                group_eps = eps.select(group=group)
            elif isinstance(eps, dict):
                # Python 3.9
                group_eps = eps.get(group, [])
            else:
                # Python 3.8
                group_eps = [ep for ep in eps if ep.group == group]
            
            for ep in group_eps:
                try:
                    plugin_class = ep.load()
                    plugin = self._instantiate_plugin(plugin_class)
                    if plugin and self.registry.register(plugin):
                        loaded.append(plugin.metadata.name)
                        logger.info(f"Loaded plugin from entry point: {ep.name}")
                except Exception as e:
                    logger.error(f"Failed to load entry point {ep.name}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading entry points: {e}")
        
        return loaded
    
    def load_from_directory(self, directory: Path, recursive: bool = False) -> List[str]:
        """
        Load plugins from Python files in a directory.
        
        Looks for classes that inherit from BasePlugin.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of loaded plugin names
        """
        loaded = []
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return loaded
        
        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"
        for py_file in directory.glob(pattern):
            if py_file.name.startswith("_"):
                continue
            
            try:
                # Import module
                module_name = f"autonomai_plugin_{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type) and
                            issubclass(attr, BasePlugin) and
                            attr is not BasePlugin
                        ):
                            plugin = self._instantiate_plugin(attr)
                            if plugin and self.registry.register(plugin):
                                loaded.append(plugin.metadata.name)
                                logger.info(f"Loaded plugin from file: {py_file.name}")
                
            except Exception as e:
                logger.error(f"Error loading plugin from {py_file}: {e}")
        
        return loaded
    
    def load_from_config(self, config_path: Path) -> List[str]:
        """
        Load plugins specified in a configuration file.
        
        Config format (YAML or JSON):
        plugins:
          - name: my_plugin
            module: my_package.plugin
            class: MyPlugin
            config:
              enabled: true
              priority: 100
              settings:
                option1: value1
        
        Args:
            config_path: Path to config file
            
        Returns:
            List of loaded plugin names
        """
        loaded = []
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Plugin config file does not exist: {config_path}")
            return loaded
        
        try:
            # Load config
            with open(config_path) as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # Load each plugin
            for plugin_spec in config.get("plugins", []):
                try:
                    module_name = plugin_spec["module"]
                    class_name = plugin_spec["class"]
                    
                    # Import module and get class
                    module = importlib.import_module(module_name)
                    plugin_class = getattr(module, class_name)
                    
                    # Create config
                    plugin_config = None
                    if "config" in plugin_spec:
                        plugin_config = PluginConfig(**plugin_spec["config"])
                    
                    # Instantiate and register
                    plugin = self._instantiate_plugin(plugin_class, plugin_config)
                    if plugin and self.registry.register(plugin):
                        loaded.append(plugin.metadata.name)
                        logger.info(f"Loaded plugin from config: {plugin_spec['name']}")
                
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_spec.get('name', 'unknown')}: {e}")
        
        except Exception as e:
            logger.error(f"Error reading plugin config {config_path}: {e}")
        
        return loaded
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register an explicitly created plugin instance.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registered successfully
        """
        return self.registry.register(plugin)
    
    def _instantiate_plugin(
        self,
        plugin_class: Type[BasePlugin],
        config: Optional[PluginConfig] = None
    ) -> Optional[BasePlugin]:
        """
        Create a plugin instance from a class.
        
        Args:
            plugin_class: Plugin class to instantiate
            config: Optional configuration
            
        Returns:
            Plugin instance or None if instantiation failed
        """
        try:
            # Check if class has get_metadata class method
            if hasattr(plugin_class, "get_metadata"):
                metadata = plugin_class.get_metadata()
            else:
                # Try to instantiate and get metadata
                # This is less ideal but provides fallback
                temp_instance = plugin_class(
                    metadata=PluginMetadata(
                        name="temp",
                        version="0.0.0",
                        author="unknown",
                        description="temporary",
                        plugin_type="unknown"
                    )
                )
                if hasattr(temp_instance, "metadata"):
                    metadata = temp_instance.metadata
                else:
                    logger.error(f"Plugin class {plugin_class.__name__} has no metadata")
                    return None
            
            # Create instance with proper metadata and config
            plugin = plugin_class(metadata, config)
            return plugin
            
        except Exception as e:
            logger.error(f"Error instantiating plugin {plugin_class.__name__}: {e}")
            return None
