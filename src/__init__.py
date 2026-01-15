"""
Self-Optimizing Instruction Library

A system that learns from failures and automatically improves its own instructions.
"""

from typing import Optional, Dict, Any, List

from .core.main_model import MainModel
from .core.critic_model import CriticModel
from .core.instruction_manager import InstructionManager
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
            (not result["validation_passed"] or result.get("correction_detected", False))
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
            },
            "versions": {
                "total": len(versions),
                "latest": versions[-1]["version_id"] if versions else None,
            },
            "validation": {
                "validators_count": len(self.validation_pipeline.validators),
            },
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
