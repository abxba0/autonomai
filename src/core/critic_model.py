from typing import Optional, Dict, Any, List
import json
import time
import os
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..models.config import SystemConfig, OptimizationAttempt
from ..models.failure import FailureEntry
from ..models.critic_response import CriticResponse
from ..models.version import VersionMetadata
from .instruction_manager import InstructionManager


class CriticModel:
    """The Optimizer - analyzes failures and updates instructions"""

    def __init__(self, config: SystemConfig, instruction_manager: InstructionManager):
        self.config = config
        self.instruction_manager = instruction_manager

        # Load environment variables
        load_dotenv()

        # Initialize model with LangChain
        self.model = self._initialize_model()

        # System prompt for Critic
        self.system_prompt = self._build_system_prompt()

    def _initialize_model(self):
        """Initialize the language model with LangChain"""
        model_name = self.config.critic_model.lower()

        if "claude" in model_name or "anthropic" in model_name:
            # Use Anthropic Claude
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

            return ChatAnthropic(
                model=self.config.critic_model,
                temperature=self.config.temperature_critic,
                api_key=api_key,
            )

        elif "gpt" in model_name or "openai" in model_name:
            # Use OpenAI GPT
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            return ChatOpenAI(
                model=self.config.critic_model,
                temperature=self.config.temperature_critic,
                api_key=api_key,
            )

        else:
            # Fallback to mock model for testing
            print(f"Warning: Using mock model for {self.config.critic_model}")
            print(
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable for real LLM"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

    def optimize(self, failure: FailureEntry) -> Dict[str, Any]:
        """
        Attempt to optimize instructions based on failure

        Returns:
            Dict containing:
                - success: bool
                - critic_response: Optional[CriticResponse]
                - attempts: List[OptimizationAttempt]
                - error_message: Optional[str]
        """

        # Track attempts
        attempts = []

        for attempt_num in range(1, self.config.max_optimization_attempts + 1):
            attempt_result = self._attempt_optimization(failure, attempt_num)
            attempts.append(attempt_result)

            if attempt_result.success:
                return {
                    "success": True,
                    "critic_response": attempt_result.critic_response,
                    "attempts": attempts,
                    "error_message": None,
                }

            # Cooldown between attempts
            if attempt_num < self.config.max_optimization_attempts:
                time.sleep(self.config.retry_cooldown_seconds)

        # All attempts failed - add to pending review
        self.instruction_manager.add_to_pending_review(
            failure,
            f"Critic failed after {self.config.max_optimization_attempts} attempts",
        )

        return {
            "success": False,
            "critic_response": None,
            "attempts": attempts,
            "error_message": "All optimization attempts failed",
        }

    def _attempt_optimization(
        self, failure: FailureEntry, attempt_number: int
    ) -> OptimizationAttempt:
        """Single optimization attempt"""

        try:
            # Build context
            context = self._build_critic_context(failure)

            # Build prompt
            prompt = self._build_optimization_prompt(failure, context, attempt_number)

            # Execute with LangChain
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt),
            ]

            try:
                response = self.model.invoke(messages)
                response_text = response.content
            except Exception as e:
                # Fallback to mock if real LLM fails
                print(f"Critic LLM call failed: {e}. Using mock response.")
                response_text = self._mock_generate_critic_response(failure)

            # Parse response into CriticResponse
            critic_response = self._parse_critic_response(response_text)

            # Validate response
            is_valid, error_msg = critic_response.is_valid()

            if not is_valid:
                return OptimizationAttempt(
                    attempt_number=attempt_number,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    success=False,
                    error_message=f"Invalid critic response: {error_msg}",
                )

            # Apply the optimization
            success = self._apply_optimization(critic_response, failure)

            if success:
                # Update failure entry
                failure.optimization_attempted = True
                failure.optimization_successful = True
                failure.resolution_notes = critic_response.impact_analysis

                return OptimizationAttempt(
                    attempt_number=attempt_number,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    success=True,
                    critic_response=critic_response,
                )
            else:
                return OptimizationAttempt(
                    attempt_number=attempt_number,
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    success=False,
                    error_message="Failed to apply optimization",
                )

        except Exception as e:
            return OptimizationAttempt(
                attempt_number=attempt_number,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                success=False,
                error_message=f"Exception: {str(e)}",
            )

    def _apply_optimization(
        self, critic_response: CriticResponse, failure: FailureEntry
    ) -> bool:
        """Apply the critic's proposed changes"""

        # Build new appendix
        new_appendix = self._build_updated_appendix(
            critic_response, self.instruction_manager.dynamic_appendix
        )

        # Create version metadata
        metadata = VersionMetadata(
            trigger_type=failure.trigger_type,
            critic_justification=critic_response.impact_analysis,
            diff_summary=f"Added rule to prevent: {failure.failure_description[:50]}...",
            failure_signature=failure.failure_signature,
            rules_added=1 if critic_response.change_type == "append" else 0,
            rules_modified=1 if critic_response.change_type == "modify" else 0,
            rules_deprecated=len(critic_response.rules_to_deprecate),
        )

        # Update via InstructionManager
        success = self.instruction_manager.update_appendix(
            new_appendix, metadata, critic_response.rules_to_deprecate
        )

        return success

    def _build_updated_appendix(
        self, critic_response: CriticResponse, current_appendix: str
    ) -> str:
        """Build the updated appendix based on critic's recommendation"""

        new_appendix = current_appendix

        if critic_response.change_type == "append":
            # Simply append new rule
            new_appendix += f"\n\n---\n\n{critic_response.proposed_appendix_update}\n"

        elif critic_response.change_type == "modify":
            # Add modification with supersedes marker
            new_appendix += f"\n\n---\n\n### Updated Rule\n{critic_response.proposed_appendix_update}\n"

            # Mark deprecated rules
            for rule in critic_response.rules_to_deprecate:
                new_appendix = new_appendix.replace(rule, f"~~{rule}~~ [SUPERSEDED]")

        elif critic_response.change_type == "replace":
            # Replace specific sections
            for rule in critic_response.rules_to_deprecate:
                new_appendix = new_appendix.replace(rule, "")

            new_appendix += f"\n\n{critic_response.proposed_appendix_update}\n"

        elif critic_response.change_type == "consolidate":
            # Full replacement during consolidation
            new_appendix = critic_response.proposed_appendix_update

        return new_appendix

    def _parse_critic_response(self, response_text: str) -> CriticResponse:
        """Parse Critic model output into CriticResponse"""

        # Expect JSON output from Critic
        try:
            # Clean potential markdown formatting
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            data = json.loads(clean_text.strip())
            return CriticResponse(**data)

        except Exception as e:
            raise ValueError(f"Failed to parse Critic response: {str(e)}")

    def _build_system_prompt(self) -> str:
        """Build the Critic's system prompt"""
        return """You are an AI System Instruction Optimizer. Your role is to analyze failures in an AI system's performance and propose improvements to its dynamic instruction set.

# Your Responsibilities

1. **Analyze Failures**: Carefully examine why the Main Model failed
2. **Propose Solutions**: Suggest specific instruction updates that will prevent this failure
3. **Ensure Safety**: Verify your changes won't break previous fixes
4. **Be Precise**: Provide clear, actionable instruction updates

# Critical Rules

- You MUST provide a detailed impact analysis (minimum 50 characters)
- You MUST explicitly declare safety with reasoning (minimum 30 characters)
- You MUST specify which existing rules are affected
- You MUST analyze potential conflicts with the failure log history
- You MUST output your response as valid JSON matching the CriticResponse schema

# Output Format

Return ONLY a JSON object with this structure:
```json
{
  "impact_analysis": "Detailed explanation of why this change is needed...",
  "affected_rules": ["rule description 1", "rule description 2"],
  "conflict_analysis": "Explanation of any conflicts...",
  "safety_declaration": true,
  "safety_reasoning": "Why this change is safe...",
  "change_type": "append|modify|replace|consolidate",
  "proposed_appendix_update": "The actual instruction text to add...",
  "rules_to_deprecate": ["old rule 1", "old rule 2"],
  "confidence_score": 0.85,
  "requires_human_review": false
}
```

# Change Types

- **append**: Add new rule without touching existing ones
- **modify**: Update existing rule(s) while marking old ones as superseded
- **replace**: Remove old rule(s) and add new one(s)
- **consolidate**: Full rewrite of appendix (only during consolidation phase)

# Conflict Resolution

When you detect a contradiction:
1. Explain the conflict in `conflict_analysis`
2. Use `modify` or `replace` change type
3. List deprecated rules in `rules_to_deprecate`
4. Mark them with [SUPERSEDES: previous_rule] in your update

# Safety Requirements

Before setting `safety_declaration: true`, you MUST:
1. Check the failure log for similar past failures
2. Verify your change addresses the root cause
3. Confirm it won't break fixes for previous failures
4. Explain your reasoning in `safety_reasoning`

If you cannot guarantee safety, set `requires_human_review: true` instead.
"""

    def _build_critic_context(self, failure: FailureEntry) -> Dict[str, Any]:
        """Build context for critic"""
        return {
            "current_failure": failure.to_markdown(detail_level="full"),
            "current_appendix": self.instruction_manager.dynamic_appendix,
            "failure_history": self.instruction_manager.failure_log.to_markdown(
                self.config
            ),
        }

    def _build_optimization_prompt(
        self, failure: FailureEntry, context: Dict[str, Any], attempt_number: int
    ) -> str:
        """Build the prompt for optimization request"""

        prompt = f"""# Optimization Request (Attempt {attempt_number}/{self.config.max_optimization_attempts})

## Current Failure

{failure.to_markdown(detail_level="full")}

## Current Dynamic Appendix

{context["current_appendix"]}

## Relevant Failure History

{context["failure_history"]}

## Your Task

Analyze this failure and propose an instruction update that will prevent it from recurring.

Consider:
- What specific instruction would have prevented this failure?
- Does this conflict with any existing rules or past fixes?
- Is this a root cause fix or just a symptom treatment?
- What's the minimal change needed?

"""

        if attempt_number > 1:
            prompt += f"\n**Note**: This is attempt #{attempt_number}. Previous attempts failed. Review your approach and try a different strategy.\n"

        prompt += "\nProvide your response as a JSON object matching the CriticResponse schema."

        return prompt

    def _mock_generate_critic_response(self, failure: FailureEntry) -> str:
        """Mock critic response for testing"""
        import json

        if (
            "JSON" in failure.failure_description
            or "json" in failure.failure_description
        ):
            return json.dumps(
                {
                    "impact_analysis": "The model failed to produce valid JSON. We need to add a rule that ensures JSON output is properly formatted and includes required fields.",
                    "affected_rules": [],
                    "conflict_analysis": "No conflicts with existing rules.",
                    "safety_declaration": True,
                    "safety_reasoning": "This rule only adds validation for JSON output, which doesn't affect other response types.",
                    "change_type": "append",
                    "proposed_appendix_update": "**JSON Output Rule**: When the user requests JSON output, ensure the response is valid JSON with proper structure. Always include a 'status' field and validate the output before returning.",
                    "rules_to_deprecate": [],
                    "confidence_score": 0.9,
                    "requires_human_review": False,
                }
            )
        else:
            return json.dumps(
                {
                    "impact_analysis": "The model's response was too brief. We need to ensure responses are sufficiently detailed and address all aspects of the user's query.",
                    "affected_rules": [],
                    "conflict_analysis": "No conflicts with existing rules.",
                    "safety_declaration": True,
                    "safety_reasoning": "This rule encourages more detailed responses without restricting other aspects of the model's behavior.",
                    "change_type": "append",
                    "proposed_appendix_update": "**Response Detail Rule**: Ensure responses are comprehensive and address all parts of the user's query. If the query has multiple components, address each one systematically.",
                    "rules_to_deprecate": [],
                    "confidence_score": 0.85,
                    "requires_human_review": False,
                }
            )


class MockCriticModel:
    """Mock critic model for testing"""

    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, messages: List) -> Any:
        """Mock invoke for LangChain compatibility"""

        class MockResponse:
            content = json.dumps(
                {
                    "impact_analysis": "Mock critic analysis for testing purposes.",
                    "affected_rules": [],
                    "conflict_analysis": "No conflicts with existing rules.",
                    "safety_declaration": True,
                    "safety_reasoning": "This is a mock response for testing.",
                    "change_type": "append",
                    "proposed_appendix_update": "**Mock Rule**: This is a test rule added by the mock critic model.",
                    "rules_to_deprecate": [],
                    "confidence_score": 0.8,
                    "requires_human_review": False,
                }
            )

        return MockResponse()
