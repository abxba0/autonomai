"""
Workflow models for the Self-Optimizing Workflow Orchestrator

Defines data structures for multi-step workflows with dynamic planning,
execution tracking, and failure recovery.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureSource(Enum):
    """Source of workflow step failure for targeted optimization"""
    PLANNING = "planning"  # Bad sequence, missing precondition, incorrect dependencies
    EXECUTION = "execution"  # Step instructions not robust, implementation issues


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow
    
    Attributes:
        id: Unique identifier for the step
        name: Human-readable step name
        description: Detailed description of what this step should do
        dependencies: List of step IDs that must complete before this step
        status: Current execution status
        inputs: Input data/parameters for this step
        outputs: Output data produced by this step
        error_message: Error details if step failed
        execution_log: Log of execution attempts and results
        created_at: Timestamp when step was created
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution completed
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error_message": self.error_message,
            "execution_log": self.execution_log,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create step from dictionary"""
        step = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            status=StepStatus(data.get("status", "pending")),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            error_message=data.get("error_message"),
            execution_log=data.get("execution_log", []),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            step.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            step.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            step.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return step


@dataclass
class WorkflowPlan:
    """
    Represents a complete workflow plan with multiple steps
    
    Attributes:
        id: Unique identifier for the workflow
        name: Human-readable workflow name
        description: Overall workflow description
        goal: The high-level goal this workflow aims to achieve
        steps: List of workflow steps (can form a DAG)
        metadata: Additional metadata about the workflow
        execution_log: Global execution log for the workflow
        created_at: Timestamp when workflow was created
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution completed
        planner_version: Version of planner instructions used
        actor_version: Version of actor instructions used
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    goal: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    planner_version: Optional[str] = None
    actor_version: Optional[str] = None
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by its ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """
        Get steps that are ready to execute (PENDING with all dependencies met)
        """
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            deps_met = True
            for dep_id in step.dependencies:
                dep_step = self.get_step_by_id(dep_id)
                if not dep_step or dep_step.status != StepStatus.COMPLETED:
                    deps_met = False
                    break
            
            if deps_met:
                ready.append(step)
        
        return ready
    
    def is_complete(self) -> bool:
        """Check if workflow is complete (all steps completed or skipped)"""
        for step in self.steps:
            if step.status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                return False
        return True
    
    def has_failures(self) -> bool:
        """Check if workflow has any failed steps"""
        return any(step.status == StepStatus.FAILED for step in self.steps)
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get all failed steps"""
        return [step for step in self.steps if step.status == StepStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow plan to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
            "execution_log": self.execution_log,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "planner_version": self.planner_version,
            "actor_version": self.actor_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowPlan":
        """Create workflow plan from dictionary"""
        plan = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            goal=data.get("goal", ""),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            metadata=data.get("metadata", {}),
            execution_log=data.get("execution_log", []),
            planner_version=data.get("planner_version"),
            actor_version=data.get("actor_version"),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            plan.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            plan.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            plan.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return plan


@dataclass
class WorkflowFailure:
    """
    Represents a workflow failure with context for Critic analysis
    
    Attributes:
        workflow_id: ID of the workflow that failed
        step_id: ID of the step that failed
        failure_source: Whether failure was due to planning or execution
        error_message: Error message from the failure
        step_context: Context of the failed step (inputs, description, etc.)
        workflow_context: Context of the entire workflow for trajectory analysis
        suggested_fix: Critic's suggested fix
        timestamp: When the failure occurred
    """
    workflow_id: str
    step_id: str
    failure_source: FailureSource
    error_message: str
    step_context: Dict[str, Any] = field(default_factory=dict)
    workflow_context: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert failure to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "failure_source": self.failure_source.value,
            "error_message": self.error_message,
            "step_context": self.step_context,
            "workflow_context": self.workflow_context,
            "suggested_fix": self.suggested_fix,
            "timestamp": self.timestamp.isoformat(),
        }
