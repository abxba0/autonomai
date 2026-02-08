"""
Self-Optimizing Instruction Library

A system that learns from failures and automatically improves its own instructions.
Includes a production-grade plugin system for extensibility.
"""

from typing import Optional, Dict, Any, List

from .core.main_model import MainModel
from .core.critic_model import CriticModel
from .core.instruction_manager import InstructionManager
from .core.context_analyzer import ContextAnalyzer
from .core.validator import (
    ValidationPipeline,
    JSONValidator,
    LengthValidator,
    RegexValidator,
    CustomValidator,
)
from .core.workflow import WorkflowOrchestrator
from .models.config import SystemConfig, FailureEntry
from .models.critic_response import CriticResponse
from .models.workflow import (
    WorkflowPlan,
    WorkflowStep,
    WorkflowFailure,
    StepStatus,
    FailureSource,
)

# Plugin system
from .plugins import (
    PluginManager,
    BasePlugin,
    PluginMetadata,
    PluginConfig,
    PluginLifecycle,
    ValidatorPlugin,
    OptimizerPlugin,
    FailureAnalyzerPlugin,
    WorkflowStepPlugin,
)

# Modular components
from .system_initializer import SystemInitializer
from .feedback_processor import FeedbackProcessor
from .workflow_manager import WorkflowManager
from .system_status import SystemStatus


class SelfOptimizingSystem:
    """Main interface for the self-optimizing system.

    Composes SystemInitializer, FeedbackProcessor, WorkflowManager,
    and SystemStatus to provide a unified API while keeping each
    concern in its own module.
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()

        # Initialize all components via SystemInitializer
        components = SystemInitializer.initialize(self.config)
        self.state_manager = components["state_manager"]
        self.instruction_manager = components["instruction_manager"]
        self.validation_pipeline = components["validation_pipeline"]
        self.main_model = components["main_model"]
        self.critic_model = components["critic_model"]
        self.context_analyzer = components["context_analyzer"]

        # Compose modular subsystems
        self._feedback_processor = FeedbackProcessor(
            self.instruction_manager,
            self.critic_model,
            self.context_analyzer,
            self.config,
        )
        self._workflow_manager = WorkflowManager(
            self.config, self.instruction_manager
        )
        self._system_status = SystemStatus(
            self.config, self.instruction_manager, self.validation_pipeline
        )

        # Track pending optimizations
        self.pending_optimizations = []

    def add_validator(self, validator):
        """Add a validator to the validation pipeline"""
        self.validation_pipeline.add_validator(validator)

    def execute(
        self,
        user_query: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a user query with automatic optimization

        Returns:
            Dict containing execution results and optimization status
        """
        # Execute query
        result = self.main_model.execute(user_query, conversation_context)

        # If validation failed OR correction detected, and auto-optimization is enabled, try to optimize
        should_optimize = (
            (
                not result["validation_passed"]
                or result.get("correction_detected", False)
            )
            and self.config.enable_auto_optimization
            and result["failure_entry"]
        )

        if should_optimize:
            optimization_result = self.critic_model.optimize(result["failure_entry"])
            result["optimization_attempted"] = True
            result["optimization_result"] = optimization_result
        else:
            result["optimization_attempted"] = False
            result["optimization_result"] = None

        return result

    def request_instruction_update(
        self,
        user_feedback: str,
        severity: str = "moderate",
        attach_last_output: bool = True,
    ):
        """Manually request instruction update based on user feedback"""
        failure = FailureEntry(
            trigger_type="human_feedback",
            failure_description=user_feedback,
            severity=severity,
            user_feedback=user_feedback,
        )

        self.instruction_manager.add_failure(failure)

        # Try to optimize
        if self.config.enable_auto_optimization:
            return self.critic_model.optimize(failure)

        return {"success": False, "message": "Auto-optimization disabled"}

    def get_version_history(self):
        """Get version history"""
        return self._system_status.get_version_history()

    def rollback(self, steps: int = 1) -> bool:
        """Rollback N versions"""
        return self._system_status.rollback(steps)

    def rollback_to_version(self, version_id: str) -> bool:
        """Rollback to specific version"""
        return self._system_status.rollback_to_version(version_id)

    def get_current_instructions(self) -> str:
        """Get current instructions"""
        return self._system_status.get_current_instructions()

    def process_failure(
        self,
        trigger_type: str,
        failure_description: str,
        user_query: str,
        last_model_output: str,
        validation_results: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """Process a failure and trigger optimization if enabled"""
        return self._feedback_processor.process_failure(
            trigger_type=trigger_type,
            failure_description=failure_description,
            user_query=user_query,
            last_model_output=last_model_output,
            validation_results=validation_results,
        )

    def process_feedback(
        self,
        user_query: str,
        model_output: str,
        feedback_type: str,
        feedback_details: str,
    ) -> Dict[str, Any]:
        """Process user feedback about model output"""
        return self._feedback_processor.process_feedback(
            user_query=user_query,
            model_output=model_output,
            feedback_type=feedback_type,
            feedback_details=feedback_details,
        )

    def validate_output(self, output: str) -> bool:
        """Validate model output using the validation pipeline"""
        passed, _ = self.validation_pipeline.validate(output)
        return passed

    def get_failure_history(self, limit: int = 50) -> List[FailureEntry]:
        """Get recent failure history"""
        return self._system_status.get_failure_history(limit)

    def get_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return self._system_status.get_status()

    def analyze_feedback_context(
        self,
        conversation_history: List[Dict[str, str]],
        focus_recent: int = 10,
        min_confidence: float = 0.6,
        auto_apply: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze conversation context to extract rules and patterns

        This implements the /feedback-context command functionality.

        Args:
            conversation_history: List of conversation messages
            focus_recent: Number of recent messages to focus on
            min_confidence: Minimum confidence for rule extraction
            auto_apply: Whether to automatically apply extracted rules

        Returns:
            Dict containing analysis results and extracted rules
        """
        return self._feedback_processor.analyze_feedback_context(
            conversation_history=conversation_history,
            focus_recent=focus_recent,
            min_confidence=min_confidence,
            auto_apply=auto_apply,
        )

    def execute_workflow(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute a multi-step workflow from a high-level goal

        This creates a workflow plan using the Planner, executes steps with the Executor,
        and automatically optimizes based on failures using the Critic.

        Args:
            goal: The high-level objective to achieve
            context: Optional context information for planning
            max_retries: Maximum retries for failed steps

        Returns:
            Dict with workflow execution results including:
            - workflow_id: Unique workflow identifier
            - status: completed or failed
            - steps_completed: Number of successful steps
            - results: Detailed results for each step
        """
        return self._workflow_manager.execute_workflow(goal, context, max_retries)


__all__ = [
    "SelfOptimizingSystem",
    "SystemConfig",
    "MainModel",
    "CriticModel",
    "InstructionManager",
    "ValidationPipeline",
    "JSONValidator",
    "LengthValidator",
    "RegexValidator",
    "CustomValidator",
    "FailureEntry",
    "CriticResponse",
    "WorkflowOrchestrator",
    "WorkflowPlan",
    "WorkflowStep",
    "WorkflowFailure",
    "StepStatus",
    "FailureSource",
    # Plugin system
    "PluginManager",
    "BasePlugin",
    "PluginMetadata",
    "PluginConfig",
    "PluginLifecycle",
    "ValidatorPlugin",
    "OptimizerPlugin",
    "FailureAnalyzerPlugin",
    "WorkflowStepPlugin",
    # Modular components
    "SystemInitializer",
    "FeedbackProcessor",
    "WorkflowManager",
    "SystemStatus",
]
