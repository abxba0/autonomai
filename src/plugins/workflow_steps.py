"""
Workflow step plugin interface for extending workflow capabilities.
"""

from abc import abstractmethod
from typing import Optional, Dict, Any

from .base import BasePlugin, PluginMetadata, PluginConfig
from ..models.workflow import WorkflowStep, StepStatus


class WorkflowStepPlugin(BasePlugin):
    """
    Base class for workflow step plugins.
    
    Workflow step plugins can add custom step types to the workflow
    orchestrator, enabling specialized step execution logic.
    """
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)
    
    @abstractmethod
    def execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> tuple[StepStatus, Dict[str, Any]]:
        """
        Execute a workflow step with custom logic.
        
        Args:
            step: The workflow step to execute
            context: Execution context containing inputs and shared state
            
        Returns:
            Tuple of (status, outputs) where:
                - status: StepStatus indicating success/failure
                - outputs: Dictionary of step outputs
        """
        pass
    
    @abstractmethod
    def can_execute(self, step: WorkflowStep) -> bool:
        """
        Determine if this plugin can execute the given step.
        
        Typically checks step.step_type or other step attributes.
        
        Args:
            step: The workflow step to check
            
        Returns:
            True if this plugin can execute the step
        """
        pass
    
    def validate_step(self, step: WorkflowStep) -> tuple[bool, Optional[str]]:
        """
        Validate a workflow step before execution.
        
        Args:
            step: The workflow step to validate
            
        Returns:
            (is_valid, error_message) tuple
        """
        # Default implementation - can be overridden
        return True, None
    
    def initialize(self) -> bool:
        """Initialize the workflow step plugin"""
        # Default implementation - can be overridden
        return True
    
    def cleanup(self):
        """Clean up workflow step resources"""
        pass
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate workflow step plugin configuration"""
        if self.metadata.plugin_type != "workflow_step":
            return False, f"Plugin type must be 'workflow_step', got '{self.metadata.plugin_type}'"
        return True, None
