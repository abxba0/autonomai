"""
Workflow Orchestrator for Self-Optimizing Autonomous Workflows

This module is maintained for backward compatibility.
The implementation has been refactored into the src.core.workflow package.

Import from here or from src.core.workflow - both work identically.
"""

# Re-export from the new workflow package for backward compatibility
from .workflow import WorkflowOrchestrator, WorkflowInstructionManager

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowInstructionManager",
]
