"""
Feedback processing for SelfOptimizingSystem.

Handles user feedback and context analysis for instruction improvement.
"""

from typing import Optional, Dict, Any, List

from .models.config import FailureEntry


class FeedbackProcessor:
    """Processes user feedback and context analysis for optimization.

    Works with the instruction manager, critic model, and context analyzer
    to turn user feedback into instruction improvements.
    """

    def __init__(self, instruction_manager, critic_model, context_analyzer, config):
        self.instruction_manager = instruction_manager
        self.critic_model = critic_model
        self.context_analyzer = context_analyzer
        self.config = config

    def process_feedback(
        self,
        user_query: str,
        model_output: str,
        feedback_type: str,
        feedback_details: str,
    ) -> Dict[str, Any]:
        """Process user feedback about model output."""
        return self.process_failure(
            trigger_type="human_feedback",
            failure_description=f"User feedback: {feedback_details}",
            user_query=user_query,
            last_model_output=model_output,
        )

    def process_failure(
        self,
        trigger_type: str,
        failure_description: str,
        user_query: str = "",
        last_model_output: str = "",
        validation_results: Optional[List[tuple]] = None,
    ) -> Dict[str, Any]:
        """Process a failure and trigger optimization if enabled."""
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

    def analyze_feedback_context(
        self,
        conversation_history: List[Dict[str, str]],
        focus_recent: int = 10,
        min_confidence: float = 0.6,
        auto_apply: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze conversation context to extract rules and patterns.

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
        Apply extracted rules from context analysis to system instructions.

        Args:
            instruction_updates: Formatted instruction updates
            analysis_result: Analysis result from context analyzer

        Returns:
            Dict with application status
        """
        try:
            feedback_description = (
                f"Context analysis extracted {analysis_result.get('rules_count', 0)} "
                f"positive rules and {analysis_result.get('dont_rules_count', 0)} negative rules"
            )

            failure = FailureEntry(
                trigger_type="human_feedback",
                failure_description=feedback_description,
                severity="moderate",
                user_feedback=instruction_updates,
            )

            self.instruction_manager.add_failure(failure)

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
