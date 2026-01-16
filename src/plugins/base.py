"""
Base plugin interfaces and metadata for the plugin system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum


class PluginLifecycle(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"


@dataclass
class PluginMetadata:
    """Metadata describing a plugin"""
    name: str
    version: str
    author: str
    description: str
    plugin_type: str  # validator, optimizer, workflow_step, etc.
    
    # Optional fields
    homepage: Optional[str] = None
    license: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Compatibility
    min_system_version: Optional[str] = None
    max_system_version: Optional[str] = None


@dataclass
class PluginConfig:
    """Configuration for a plugin instance"""
    enabled: bool = True
    priority: int = 100  # Lower numbers = higher priority
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value with default fallback"""
        return self.settings.get(key, default)


class BasePlugin(ABC):
    """
    Base class for all plugins.
    
    Plugins must implement this interface to be loaded by the system.
    Each plugin type (validator, optimizer, etc.) will have its own
    specialized subclass with additional methods.
    """
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        self.metadata = metadata
        self.config = config or PluginConfig()
        self._lifecycle_state = PluginLifecycle.UNLOADED
        self._error_message: Optional[str] = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin. Called once after loading.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up plugin resources. Called before unloading.
        """
        pass
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate plugin configuration.
        
        Returns:
            (is_valid, error_message) tuple
        """
        # Default implementation - can be overridden
        return True, None
    
    @property
    def lifecycle_state(self) -> PluginLifecycle:
        """Get current lifecycle state"""
        return self._lifecycle_state
    
    @lifecycle_state.setter
    def lifecycle_state(self, state: PluginLifecycle):
        """Set lifecycle state"""
        self._lifecycle_state = state
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if in ERROR state"""
        return self._error_message
    
    def set_error(self, message: str):
        """Set error state with message"""
        self._lifecycle_state = PluginLifecycle.ERROR
        self._error_message = message
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.metadata.name}, "
            f"version={self.metadata.version}, "
            f"state={self._lifecycle_state.value})"
        )
