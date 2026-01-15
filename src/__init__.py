"""
Self-Optimizing Instruction Library

A system that learns from failures and automatically improves its own instructions.
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
from .models.config import SystemConfig, FailureEntry
from .models.critic_response import CriticResponse


class SelfOptimizingSystem:
    """Main interface for the self-optimizing system"""

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()

        # Initialize components
        self.instruction_manager = InstructionManager(self.config)
        self.validation_pipeline = ValidationPipeline()
        self.main_model = MainModel(
            self.config, self.instruction_manager, self.validation_pipeline
        )
        self.critic_model = CriticModel(self.config, self.instruction_manager)

        # Initialize context analyzer with optional LLM support
        self.context_analyzer = ContextAnalyzer(
            use_llm=True,
            llm_model=self.critic_model.model,  # Use critic model for analysis
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
        return self.instruction_manager.version_controller.get_version_history()

    def rollback(self, steps: int = 1) -> bool:
        """Rollback N versions"""
        return self.instruction_manager.rollback(steps)

    def rollback_to_version(self, version_id: str) -> bool:
        """Rollback to specific version"""
        return self.instruction_manager.rollback_to_version(version_id)

    def get_current_instructions(self) -> str:
        """Get current instructions"""
        return self.instruction_manager.get_full_instructions()

    def process_failure(
        self,
        trigger_type: str,
        failure_description: str,
        user_query: str,
        last_model_output: str,
        validation_results: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """Process a failure and trigger optimization if enabled"""
        failure = FailureEntry(
            trigger_type=trigger_type,
            failure_description=failure_description,
            user_query=user_query,
            last_model_output=last_model_output,
            validation_errors=validation_results,
        )

        self.instruction_manager.add_failure(failure)

        if self.config.enable_auto_optimization:
            optimization_result = self.critic_model.optimize(failure)
            return {
                "success": True,
                "optimization_attempted": True,
                "optimization_result": optimization_result,
                "failure_id": failure.id,
            }

        return {
            "success": True,
            "optimization_attempted": False,
            "message": "Auto-optimization disabled",
            "failure_id": failure.id,
        }

    def process_feedback(
        self,
        user_query: str,
        model_output: str,
        feedback_type: str,
        feedback_details: str,
    ) -> Dict[str, Any]:
        """Process user feedback about model output"""
        return self.process_failure(
            trigger_type="human_feedback",
            failure_description=f"User feedback: {feedback_details}",
            user_query=user_query,
            last_model_output=model_output,
        )

    def validate_output(self, output: str) -> bool:
        """Validate model output using the validation pipeline"""
        passed, _ = self.validation_pipeline.validate(output)
        return passed

    def get_failure_history(self, limit: int = 50) -> List[FailureEntry]:
        """Get recent failure history"""
        # This would need to be implemented in InstructionManager
        # For now, return empty list
        return []

    def get_status(self) -> Dict[str, Any]:
        """Get system status information"""
        versions = self.get_version_history()
        return {
            "system": "Self-Optimizing Instruction Library",
            "status": "operational",
            "config": {
                "main_model": self.config.main_model,
                "critic_model": self.config.critic_model,
                "enable_auto_optimization": self.config.enable_auto_optimization,
                "enable_correction_detection": self.config.enable_correction_detection,
            },
            "versions": {
                "total": len(versions),
                "latest": versions[-1]["version_id"] if versions else None,
            },
            "validation": {
                "validators_count": len(self.validation_pipeline.validators),
            },
        }

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
        # Analyze the conversation
        analysis_result = self.context_analyzer.analyze_conversation(
            conversation_history,
            focus_recent=focus_recent,
            min_confidence=min_confidence,
        )

        if not analysis_result.get("success"):
            return analysis_result

        # Format rules for display
        formatted_display = self.context_analyzer.format_rules_for_display(
            analysis_result
        )

        # Create instruction updates
        instruction_updates = self.context_analyzer.create_instruction_updates(
            analysis_result, format="markdown"
        )

        result = {
            "success": True,
            "analysis": analysis_result,
            "formatted_display": formatted_display,
            "instruction_updates": instruction_updates,
            "rules_count": len(analysis_result.get("rules", [])),
            "dont_rules_count": len(analysis_result.get("dont_rules", [])),
            "patterns_count": len(analysis_result.get("patterns", [])),
        }

        # Optionally auto-apply the rules
        if auto_apply and instruction_updates:
            apply_result = self._apply_context_rules(
                instruction_updates, analysis_result
            )
            result["auto_apply_result"] = apply_result

        return result

    def _apply_context_rules(
        self, instruction_updates: str, analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply extracted rules from context analysis to system instructions

        Args:
            instruction_updates: Formatted instruction updates
            analysis_result: Analysis result from context analyzer

        Returns:
            Dict with application status
        """
        try:
            # Create a feedback entry for this context-based update
            feedback_description = f"Context analysis extracted {analysis_result.get('rules_count', 0)} positive rules and {analysis_result.get('dont_rules_count', 0)} negative rules"

            failure = FailureEntry(
                trigger_type="human_feedback",
                failure_description=feedback_description,
                severity="moderate",
                user_feedback=instruction_updates,
            )

            self.instruction_manager.add_failure(failure)

            # Try to optimize with the extracted rules
            if self.config.enable_auto_optimization:
                optimization_result = self.critic_model.optimize(failure)
                return {
                    "success": True,
                    "optimization_attempted": True,
                    "optimization_result": optimization_result,
                }
            else:
                return {
                    "success": True,
                    "optimization_attempted": False,
                    "message": "Auto-optimization is disabled. Rules logged for manual review.",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to apply context rules",
            }


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
]
