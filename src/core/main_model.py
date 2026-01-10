from typing import Optional, Dict, Any, List
import time
import os
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..models.config import SystemConfig
from ..models.failure import FailureEntry
from .instruction_manager import InstructionManager
from .validator import ValidationPipeline


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

        # Load environment variables
        load_dotenv()

        # Initialize model with LangChain
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Initialize the language model with LangChain"""
        model_name = self.config.main_model.lower()

        if "claude" in model_name or "anthropic" in model_name:
            # Use Anthropic Claude
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

            return ChatAnthropic(
                model=self.config.main_model,
                temperature=self.config.temperature_main,
                api_key=api_key,
            )

        elif "gpt" in model_name or "openai" in model_name:
            # Use OpenAI GPT
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            return ChatOpenAI(
                model=self.config.main_model,
                temperature=self.config.temperature_main,
                api_key=api_key,
            )

        else:
            # Fallback to mock model for testing
            print(f"Warning: Using mock model for {self.config.main_model}")
            print(
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable for real LLM"
            )
            return MockModel(self.config.main_model, self.config.temperature_main)

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
        """

        # Get current instructions
        system_instructions = self.instruction_manager.get_full_instructions()

        # Build LangChain messages
        messages = [SystemMessage(content=system_instructions)]

        # Add conversation context if provided
        if conversation_context:
            for msg in conversation_context:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(SystemMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_query))

        # Execute with LangChain
        try:
            response = self.model.invoke(messages)
            output = response.content
        except Exception as e:
            # Fallback to mock model if real LLM fails
            print(f"LLM call failed: {e}. Using mock model.")
            output = self._mock_generate(system_instructions, user_query)

        # Validate if enabled
        validation_passed = True
        validation_results = []
        failure_entry = None

        if self.config.enable_auto_validation:
            validation_passed, validation_results = self.validation_pipeline.validate(
                output, context={"query": user_query}
            )

            # Create failure entry if validation failed
            if not validation_passed:
                failure_entry = self._create_validation_failure(
                    user_query, output, validation_results
                )
                self.instruction_manager.add_failure(failure_entry)

        return {
            "output": output,
            "validation_passed": validation_passed,
            "validation_results": validation_results,
            "failure_entry": failure_entry,
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

    def _mock_generate(self, system_instructions: str, user_query: str) -> str:
        """Mock generation for testing without API calls"""
        if "json" in user_query.lower():
            return '{"status": "success", "result": "Mock JSON response"}'
        elif "error" in user_query.lower():
            return "This is an error response that should fail validation."
        else:
            return f"Mock response to: {user_query[:50]}...\n\nBased on system instructions: {system_instructions[:100]}..."


class MockModel:
    """Mock model for testing without actual API calls"""

    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, messages: List) -> Any:
        """Mock invoke for LangChain compatibility"""

        class MockResponse:
            content = "Mock response from test model"

        return MockResponse()
