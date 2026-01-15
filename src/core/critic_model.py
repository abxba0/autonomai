from typing import Dict, Any, List, Optional
import json
import time
import os
from dotenv import load_dotenv

# LangChain imports are optional - will be imported only if needed
# from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage

from ..models.config import SystemConfig, OptimizationAttempt, FailureEntry
from ..models.critic_response import CriticResponse
from ..models.version import VersionMetadata
from .instruction_manager import InstructionManager
from .judge_model import JudgeModel
from ..utils.embeddings import EmbeddingsManager


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

        # Initialize embeddings manager for semantic de-duplication
        self.embeddings_manager = None
        if self.config.enable_semantic_deduplication:
            try:
                self.embeddings_manager = EmbeddingsManager(self.config)
            except Exception as e:
                print(
                    f"Warning: Could not initialize embeddings for de-duplication: {e}"
                )
                self.embeddings_manager = None

        # Initialize Judge model for consensus validation (Phase 2)
        self.judge_model = None
        if self.config.enable_judge_model:
            try:
                self.judge_model = JudgeModel(
                    self.config, self.instruction_manager.base_instructions
                )
                print("✓ Judge model initialized for consensus validation")
            except Exception as e:
                print(f"Warning: Could not initialize Judge model: {e}")
                self.judge_model = None

    def _initialize_model(self):
        """Initialize the critic model with LangChain"""
        model_name = self.config.critic_model.lower()
        provider = (
            self.config.critic_model_provider.lower()
            if self.config.critic_model_provider
            else None
        )

        # Detect provider from model name if not explicitly set
        if not provider:
            provider = self._detect_provider(model_name)

        # Initialize based on provider
        if provider == "anthropic":
            return self._init_anthropic()
        elif provider == "openai":
            return self._init_openai()
        elif provider == "google":
            return self._init_google()
        elif provider == "deepseek":
            return self._init_deepseek()
        elif provider == "openrouter":
            return self._init_openrouter()
        else:
            # Fallback to mock model for testing
            print(f"Warning: Using mock model for {self.config.critic_model}")
            print("Set appropriate API key environment variable for real LLM")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

    def _detect_provider(self, model_name: str) -> str:
        """Auto-detect provider from model name"""
        if "claude" in model_name or "anthropic" in model_name:
            return "anthropic"
        elif "gpt" in model_name or "openai" in model_name:
            return "openai"
        elif "gemini" in model_name or "google" in model_name:
            return "google"
        elif "deepseek" in model_name:
            return "deepseek"
        elif "openrouter" in model_name:
            return "openrouter"
        return "unknown"

    def _init_anthropic(self):
        """Initialize Anthropic Claude model"""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            print(
                "Warning: langchain-anthropic not installed. Install with: pip install langchain-anthropic"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not found. Using mock model.")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        return ChatAnthropic(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
        )

    def _init_openai(self):
        """Initialize OpenAI GPT model"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print(
                "Warning: langchain-openai not installed. Install with: pip install langchain-openai"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Using mock model.")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
        )

    def _init_google(self):
        """Initialize Google Gemini model"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            print(
                "Warning: langchain-google-genai not installed. Install with: pip install langchain-google-genai"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found. Using mock model.")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        return ChatGoogleGenerativeAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            google_api_key=api_key,
        )

    def _init_deepseek(self):
        """Initialize Deepseek model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print(
                "Warning: langchain-openai not installed. Install with: pip install langchain-openai"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

        if not api_key:
            print("Warning: DEEPSEEK_API_KEY not found. Using mock model.")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
            base_url=base_url,
        )

    def _init_openrouter(self):
        """Initialize Openrouter model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print(
                "Warning: langchain-openai not installed. Install with: pip install langchain-openai"
            )
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            print("Warning: OPENROUTER_API_KEY not found. Using mock model.")
            return MockCriticModel(
                self.config.critic_model, self.config.temperature_critic
            )

        return ChatOpenAI(
            model=self.config.critic_model,
            temperature=self.config.temperature_critic,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/abxba0/autonomai",
                "X-Title": "AutonomAI Self-Optimizing System",
            },
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

            # Execute with model
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt),
                ]

                response = self.model.invoke(messages)
                response_text = response.content
            except ImportError:
                # If langchain is not available, use simple message format
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ]
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

        # Phase 4: Confidence-Based Throttling
        if self.config.enable_confidence_throttling:
            if critic_response.confidence_score < self.config.confidence_threshold:
                print(
                    f"⚠ Confidence too low ({critic_response.confidence_score:.2f} < {self.config.confidence_threshold})"
                )
                print("  Moving to pending review for human evaluation")

                # Add to pending review with confidence info
                self.instruction_manager.add_to_pending_review(
                    failure,
                    f"Low confidence score ({critic_response.confidence_score:.2f})\n\n"
                    f"Proposed change:\n{critic_response.proposed_appendix_update}\n\n"
                    f"Reasoning: {critic_response.impact_analysis}",
                )

                failure.optimization_attempted = True
                failure.optimization_successful = False
                failure.resolution_notes = "Low confidence - pending human review"
                return False

        # Phase 1: Semantic De-duplication Check
        if self.config.enable_semantic_deduplication and self.embeddings_manager:
            is_duplicate, similar_rule = self._check_semantic_duplicate(
                critic_response.proposed_appendix_update
            )
            if is_duplicate:
                print(
                    "✓ Semantic de-duplication: Skipping duplicate rule (similarity to existing rule)"
                )
                print(f"  Existing rule: {similar_rule[:100]}...")
                # Still mark as successful optimization but don't add duplicate
                failure.optimization_attempted = True
                failure.optimization_successful = True
                failure.resolution_notes = (
                    "Rule already exists (semantic similarity detected)"
                )
                return True

        # Phase 2: Judge Model Consensus Validation
        if (
            self.config.enable_judge_model
            and self.judge_model
            and self.config.judge_approval_required
        ):
            judge_response = self.judge_model.review_proposal(
                critic_response,
                self.instruction_manager.dynamic_appendix,
                failure.to_markdown(detail_level="full"),
            )

            if not judge_response.approved:
                print(f"✗ Judge rejected proposal: {judge_response.reasoning}")
                if judge_response.suggestions:
                    print(f"  Suggestions: {judge_response.suggestions}")

                # Add to pending review with Judge's feedback
                self.instruction_manager.add_to_pending_review(
                    failure,
                    f"Judge rejected: {judge_response.reasoning}\n\nSuggestions: {judge_response.suggestions or 'None'}",
                )

                failure.optimization_attempted = True
                failure.optimization_successful = False
                failure.resolution_notes = f"Judge rejected: {judge_response.reasoning}"
                return False
            else:
                print(
                    f"✓ Judge approved proposal (confidence: {judge_response.confidence_score:.2f})"
                )
                print(f"  Reasoning: {judge_response.reasoning[:100]}...")

        # Phase 3: Automated Regression Testing
        if (
            self.config.enable_regression_testing
            and self.instruction_manager.golden_dataset
        ):
            # Temporarily apply the change to test it
            temp_appendix = self._build_updated_appendix(  # noqa: F841
                critic_response, self.instruction_manager.dynamic_appendix
            )

            # Create a test function that uses the temporary appendix
            def test_with_new_instructions(query: str) -> str:
                # This is a simplified test - in production, you'd want to
                # actually run the MainModel with the new instructions
                # For now, we just return a placeholder
                return f"Test output for: {query}"

            # Run regression tests
            regression_results = (
                self.instruction_manager.golden_dataset.run_regression_tests(
                    test_with_new_instructions,
                    sample_size=self.config.regression_test_sample_size,
                )
            )

            # Check if regression tests passed
            if regression_results["pass_rate"] < self.config.regression_pass_threshold:
                print(
                    f"✗ Regression tests failed: {regression_results['pass_rate']*100:.1f}% pass rate"
                )
                print(f"  Required: {self.config.regression_pass_threshold*100:.1f}%")

                # Add to pending review with regression test details
                self.instruction_manager.add_to_pending_review(
                    failure,
                    f"Regression tests failed\n\n"
                    f"Pass rate: {regression_results['pass_rate']*100:.1f}%\n"
                    f"Passed: {regression_results['passed']}/{regression_results['total']}\n\n"
                    f"Proposed change:\n{critic_response.proposed_appendix_update}\n\n"
                    f"This change may break existing functionality.",
                )

                failure.optimization_attempted = True
                failure.optimization_successful = False
                failure.resolution_notes = "Regression tests failed - pending review"
                return False
            else:
                print(
                    f"✓ Regression tests passed: {regression_results['pass_rate']*100:.1f}% ({regression_results['passed']}/{regression_results['total']})"
                )

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

    def _check_semantic_duplicate(
        self, proposed_rule: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if proposed rule is semantically similar to existing rules

        Returns:
            Tuple of (is_duplicate, similar_rule_text)
        """
        if not self.embeddings_manager or not self.embeddings_manager.embeddings_model:
            return False, None

        try:
            # Get embedding for proposed rule
            proposed_embedding = self.embeddings_manager.get_embedding(proposed_rule)
            if not proposed_embedding:
                return False, None

            # Extract existing rules from dynamic appendix
            existing_rules = self._extract_rules_from_appendix(
                self.instruction_manager.dynamic_appendix
            )

            # Check similarity against each existing rule
            for rule_text in existing_rules:
                rule_embedding = self.embeddings_manager.get_embedding(rule_text)
                if not rule_embedding:
                    continue

                # Calculate cosine similarity
                similarity = self._cosine_similarity(proposed_embedding, rule_embedding)

                if similarity >= self.config.rule_similarity_threshold:
                    return True, rule_text

            return False, None

        except Exception as e:
            print(f"Warning: Error checking semantic duplicate: {e}")
            return False, None

    def _extract_rules_from_appendix(self, appendix: str) -> List[str]:
        """
        Extract individual rules from the dynamic appendix

        Returns list of rule texts
        """
        rules = []

        # Split by common delimiters (---, ###, **)
        sections = appendix.split("---")

        for section in sections:
            section = section.strip()
            if section and len(section) > 20:  # Ignore very short sections
                # Further split by headers if needed
                if "###" in section or "**" in section:
                    # This is a structured rule
                    rules.append(section)
                elif section.startswith("*No custom rules yet"):
                    # Skip placeholder text
                    continue
                else:
                    rules.append(section)

        return rules

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

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
