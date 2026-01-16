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


# Default maximum iterations for loop steps to prevent infinite loops
DEFAULT_MAX_ITERATIONS = 100


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """Type of workflow step"""
    STANDARD = "standard"  # Regular execution step
    CONDITIONAL = "conditional"  # If/else or switch/case branching
    LOOP = "loop"  # While, for, foreach iteration
    SUBWORKFLOW = "subworkflow"  # Nested workflow execution


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
        step_type: Type of step (standard, conditional, loop, subworkflow)
        inputs: Input data/parameters for this step
        outputs: Output data produced by this step
        error_message: Error details if step failed
        execution_log: Log of execution attempts and results
        created_at: Timestamp when step was created
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution completed
        
        # Conditional-specific attributes
        condition: Optional condition expression for conditional/loop steps
        branches: Dict of branch_name -> list of step IDs for conditional steps
        
        # Loop-specific attributes
        loop_type: Type of loop (while, for, foreach)
        loop_variable: Variable name for loop iteration
        loop_collection: Collection to iterate over (for foreach)
        max_iterations: Maximum iterations to prevent infinite loops
        
        # Subworkflow-specific attributes
        subworkflow_id: ID of the subworkflow to execute
        subworkflow_plan: Nested WorkflowPlan for subworkflows
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    step_type: StepType = StepType.STANDARD
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Conditional-specific attributes
    condition: Optional[str] = None
    branches: Dict[str, List[str]] = field(default_factory=dict)
    
    # Loop-specific attributes
    loop_type: Optional[str] = None  # "while", "for", "foreach"
    loop_variable: Optional[str] = None
    loop_collection: Optional[List[Any]] = None
    max_iterations: int = field(default_factory=lambda: DEFAULT_MAX_ITERATIONS)
    iteration_count: int = 0
    
    # Subworkflow-specific attributes
    subworkflow_id: Optional[str] = None
    subworkflow_plan: Optional['WorkflowPlan'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "step_type": self.step_type.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error_message": self.error_message,
            "execution_log": self.execution_log,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        
        # Add conditional-specific fields
        if self.step_type == StepType.CONDITIONAL:
            result["condition"] = self.condition
            result["branches"] = self.branches
        
        # Add loop-specific fields
        if self.step_type == StepType.LOOP:
            result["loop_type"] = self.loop_type
            result["loop_variable"] = self.loop_variable
            result["loop_collection"] = self.loop_collection
            result["max_iterations"] = self.max_iterations
            result["iteration_count"] = self.iteration_count
        
        # Add subworkflow-specific fields
        if self.step_type == StepType.SUBWORKFLOW:
            result["subworkflow_id"] = self.subworkflow_id
            if self.subworkflow_plan:
                result["subworkflow_plan"] = self.subworkflow_plan.to_dict()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create step from dictionary"""
        step = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            status=StepStatus(data.get("status", "pending")),
            step_type=StepType(data.get("step_type", "standard")),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            error_message=data.get("error_message"),
            execution_log=data.get("execution_log", []),
            condition=data.get("condition"),
            branches=data.get("branches", {}),
            loop_type=data.get("loop_type"),
            loop_variable=data.get("loop_variable"),
            loop_collection=data.get("loop_collection"),
            max_iterations=data.get("max_iterations", DEFAULT_MAX_ITERATIONS),
            iteration_count=data.get("iteration_count", 0),
            subworkflow_id=data.get("subworkflow_id"),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            step.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            step.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            step.completed_at = datetime.fromisoformat(data["completed_at"])
        
        # Parse subworkflow plan if present
        if data.get("subworkflow_plan"):
            step.subworkflow_plan = WorkflowPlan.from_dict(data["subworkflow_plan"])
            
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
    
    def insert_step(self, step: WorkflowStep, after_step_id: Optional[str] = None) -> bool:
        """
        Dynamically insert a new step into the workflow
        
        Args:
            step: The step to insert
            after_step_id: ID of step to insert after. If None, appends to end
            
        Returns:
            True if successful, False otherwise
        """
        if after_step_id is None:
            self.steps.append(step)
            return True
        
        for i, s in enumerate(self.steps):
            if s.id == after_step_id:
                self.steps.insert(i + 1, step)
                return True
        
        return False
    
    def remove_step(self, step_id: str) -> bool:
        """
        Dynamically remove a step from the workflow
        
        Args:
            step_id: ID of the step to remove
            
        Returns:
            True if successful, False if step not found
        """
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                # Check if any other steps depend on this one
                for other_step in self.steps:
                    if step_id in other_step.dependencies:
                        other_step.dependencies.remove(step_id)
                
                self.steps.pop(i)
                return True
        
        return False
    
    def update_step(self, step_id: str, updates: Dict[str, Any]) -> bool:
        """
        Dynamically update a step's attributes
        
        Args:
            step_id: ID of the step to update
            updates: Dictionary of attribute updates
            
        Returns:
            True if successful, False if step not found
        """
        step = self.get_step_by_id(step_id)
        if not step:
            return False
        
        for key, value in updates.items():
            if hasattr(step, key):
                setattr(step, key, value)
        
        return True


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
