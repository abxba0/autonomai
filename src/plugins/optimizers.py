"""
Optimizer/Critic plugin interface for extending optimization capabilities.
"""

from abc import abstractmethod
from typing import Optional, Dict, Any, List

from .base import BasePlugin, PluginMetadata, PluginConfig
from ..models.config import FailureEntry
from ..models.critic_response import CriticResponse


class OptimizerPlugin(BasePlugin):
    """
    Base class for optimizer plugins.
    
    Optimizer plugins can add custom failure analysis and instruction
    optimization strategies to the system.
    """
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)
    
    @abstractmethod
    def analyze_failure(
        self,
        failure: FailureEntry,
        current_instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CriticResponse]:
        """
        Analyze a failure and propose instruction updates.
        
        Args:
            failure: The failure entry to analyze
            current_instructions: Current instruction text
            context: Additional context for analysis
            
        Returns:
            CriticResponse with proposed changes, or None if no changes needed
        """
        pass
    
    @abstractmethod
    def can_handle(self, failure: FailureEntry) -> bool:
        """
        Determine if this optimizer can handle the given failure.
        
        Args:
            failure: The failure entry to check
            
        Returns:
            True if this optimizer can handle the failure
        """
        pass
    
    def initialize(self) -> bool:
        """Initialize the optimizer plugin"""
        # Default implementation - can be overridden
        return True
    
    def cleanup(self):
        """Clean up optimizer resources"""
        pass
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate optimizer plugin configuration"""
        if self.metadata.plugin_type != "optimizer":
            return False, f"Plugin type must be 'optimizer', got '{self.metadata.plugin_type}'"
        return True, None


class FailureAnalyzerPlugin(OptimizerPlugin):
    """
    Specialized optimizer plugin focused on failure analysis.
    
    This type of plugin extracts patterns and insights from failures
    without necessarily proposing instruction changes.
    """
    
    @abstractmethod
    def extract_patterns(
        self,
        failures: List[FailureEntry],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract patterns from a collection of failures.
        
        Args:
            failures: List of failures to analyze
            context: Additional context
            
        Returns:
            Dictionary containing extracted patterns and insights
        """
        pass
    
    def analyze_failure(
        self,
        failure: FailureEntry,
        current_instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CriticResponse]:
        """
        Default implementation - uses pattern extraction.
        Can be overridden for more sophisticated analysis.
        """
        patterns = self.extract_patterns([failure], context)
        
        if not patterns:
            return None
        
        # This is a simple default - specialized analyzers should override
        return None
