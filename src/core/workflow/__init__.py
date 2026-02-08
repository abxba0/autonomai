"""
Workflow Orchestration Package

Implements the Planner-Executor-Critic pattern for dynamic, multi-step workflows
with self-optimization capabilities.

This package splits the monolithic WorkflowOrchestrator into focused modules:
- orchestrator: Top-level coordination
- planner: LLM plan generation
- executor: Step execution dispatch
- control_flow: Conditionals, loops, subworkflows
- instruction_manager: Workflow-specific instruction management
- optimizer: Critic-based step optimization
"""

from .orchestrator import WorkflowOrchestrator
from .instruction_manager import WorkflowInstructionManager
from .planner import WorkflowPlanner
from .executor import WorkflowExecutor
from .control_flow import ControlFlowEngine
from .optimizer import StepOptimizer

__all__ = [
    "WorkflowOrchestrator",
    "WorkflowInstructionManager",
    "WorkflowPlanner",
    "WorkflowExecutor",
    "ControlFlowEngine",
    "StepOptimizer",
]
