from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

from ..models.config import SystemConfig, FailureEntry
from .instruction_manager import InstructionManager
from .validator import ValidationPipeline
from .correction_detector import CorrectionDetector
from .cache_initializer import initialize_cache
from .providers import detect_provider, initialize_provider

logger = logging.getLogger(__name__)


class MainModel:
    """The Actor - executes user requests with current instructions"""

    def __init__(
        self,
        config: SystemConfig,
        instruction_manager: InstructionManager,
        validation_pipeline: Optional[ValidationPipeline] = None,
    ):
        self.config = config
        self.instruction_manager = instruction_manager
        self.validation_pipeline = validation_pipeline or ValidationPipeline()

        # Initialize correction detector if enabled
        self.correction_detector = None
        if config.enable_correction_detection:
            self.correction_detector = CorrectionDetector(
                confidence_threshold=config.correction_detection_confidence_threshold
            )

        # Track last response for correction detection
        self.last_response = None

        # Load environment variables
        load_dotenv()

        # Initialize cache if enabled
        self.cache_manager = None
        self.llm_cache = None
        if config.enable_caching and config.cache_llm_responses:
            self._initialize_cache()

        # Initialize model with LangChain
        self.model = self._initialize_model()

    def _initialize_cache(self):
        """Initialize cache manager and LLM response cache"""
        self.cache_manager, self.llm_cache = initialize_cache(self.config)

    def _initialize_model(self):
        """Initialize the language model with LangChain"""
        return initialize_provider(self.config)

    def _detect_provider(self, model_name: str) -> str:
        """Auto-detect provider from model name"""
        return detect_provider(model_name)

    def execute(
        self,
        user_query: str,
        conversation_context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute user query with current instructions

        Returns:
            Dict containing:
                - output: str
                - validation_passed: bool
                - validation_results: List
                - failure_entry: Optional[FailureEntry]
                - cache_hit: bool (if caching enabled)
        """

        # Get current instructions
        system_instructions = self.instruction_manager.get_full_instructions()

        # Try to get cached response if caching is enabled
        cache_hit = False
        if self.llm_cache:
            try:
                cached_response = self.llm_cache.get_cached_response(
                    user_query=user_query,
                    system_instructions=system_instructions,
                    model_name=self.config.main_model,
                    temperature=self.config.temperature_main,
                    conversation_context=conversation_context,
                )

                if cached_response is not None:
                    cache_hit = True
                    logger.info("Cache HIT - returning cached response")
                    # Add cache_hit flag to response
                    cached_response["cache_hit"] = True
                    return cached_response

            except Exception as e:
                logger.error(f"Error checking cache: {e}")
                # Continue with normal execution

        # Build LangChain messages
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [SystemMessage(content=system_instructions)]

            # Add conversation context if provided
            if conversation_context:
                for msg in conversation_context:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        messages.append(SystemMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_query))
        except ImportError:
            # If langchain is not available, use simple message format
            messages = [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_query},
            ]
            if conversation_context:
                messages = (
                    [{"role": "system", "content": system_instructions}]
                    + conversation_context
                    + [{"role": "user", "content": user_query}]
                )

        # Execute with model
        try:
            # Check if messages are LangChain message objects or simple dicts
            if hasattr(messages[0], "content"):
                # LangChain message objects
                response = self.model.invoke(messages)
                output = response.content
            else:
                # Simple dict format - extract user query
                user_query_from_messages = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_query_from_messages = msg.get("content")
                        break

                if user_query_from_messages:
                    response = self.model.invoke(messages)
                    output = response.content
                else:
                    # Fallback to mock generation
                    output = self._mock_generate(system_instructions, user_query)
        except Exception as e:
            # Fallback to mock model if real LLM fails
            print(f"LLM call failed: {e}. Using mock model.")
            output = self._mock_generate(system_instructions, user_query)

        # Validate if enabled
        validation_passed = True
        validation_results = []
        failure_entry = None
        correction_detected = False
        correction_confidence = 0.0

        # Check for implicit corrections if enabled
        if self.correction_detector and self.last_response:
            is_correction, confidence, correction_type = (
                self.correction_detector.detect_correction(
                    user_query,
                    previous_response=self.last_response,
                    conversation_history=conversation_context,
                )
            )

            if is_correction:
                correction_detected = True
                correction_confidence = confidence

                # Create failure entry for implicit feedback
                correction_description = (
                    self.correction_detector.create_correction_description(
                        user_query, correction_type, confidence, self.last_response
                    )
                )

                failure_entry = FailureEntry(
                    trigger_type="implicit_feedback",
                    failure_description=correction_description,
                    user_query=user_query,
                    last_model_output=self.last_response,
                    severity="moderate",
                )
                self.instruction_manager.add_failure(failure_entry)

        if self.config.enable_auto_validation:
            validation_passed, validation_results = self.validation_pipeline.validate(
                output, context={"query": user_query}
            )

            # Create failure entry if validation failed (only if not already created by correction detector)
            if not validation_passed and not correction_detected:
                failure_entry = self._create_validation_failure(
                    user_query, output, validation_results
                )
                self.instruction_manager.add_failure(failure_entry)

        # Store current response for next correction detection
        self.last_response = output

        # Cache the response if caching is enabled
        if self.llm_cache and not cache_hit:
            try:
                response_to_cache = {
                    "output": output,
                    "validation_passed": validation_passed,
                    "validation_results": validation_results,
                    "failure_entry": failure_entry,
                    "cache_hit": False,
                }
                self.llm_cache.cache_response(
                    user_query=user_query,
                    system_instructions=system_instructions,
                    model_name=self.config.main_model,
                    temperature=self.config.temperature_main,
                    response=response_to_cache,
                    conversation_context=conversation_context,
                )
            except Exception as e:
                logger.error(f"Error caching response: {e}")

        # Phase 3: Add successful interactions to golden dataset
        if (
            validation_passed
            and not correction_detected
            and self.config.enable_regression_testing
            and self.instruction_manager.golden_dataset
            and self.validation_pipeline.validators
        ):

            # Only add interactions that had validators and passed
            try:
                validation_rules = [
                    v.__class__.__name__ for v in self.validation_pipeline.validators
                ]
                self.instruction_manager.golden_dataset.add_interaction(
                    user_query=user_query,
                    output=output,
                    instructions_version=self.instruction_manager.current_version
                    or "unknown",
                    model_used=self.config.main_model,
                    validation_rules=validation_rules,
                    tags=["auto_collected"],
                )
            except Exception as e:
                # Don't fail if golden dataset collection fails
                print(f"Warning: Could not add to golden dataset: {e}")

        return {
            "output": output,
            "validation_passed": validation_passed,
            "validation_results": validation_results,
            "failure_entry": failure_entry,
            "correction_detected": correction_detected,
            "correction_confidence": correction_confidence,
            "cache_hit": cache_hit,
        }

    def _create_validation_failure(
        self, user_query: str, output: str, validation_results: List
    ) -> FailureEntry:
        """Create FailureEntry from validation failure"""

        failed_validators = [r for r in validation_results if not r.passed]

        validation_errors = {
            r.validator_name: {"message": r.error_message, "details": r.error_details}
            for r in failed_validators
        }

        failure_description = f"Validation failed: {', '.join([r.validator_name for r in failed_validators])}"

        return FailureEntry(
            trigger_type="auto_validation",
            failure_description=failure_description,
            user_query=user_query,
            last_model_output=output,
            validation_errors=validation_errors,
        )
