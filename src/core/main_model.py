from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

# LangChain imports are optional - will be imported only if needed
# from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage

from ..models.config import SystemConfig, FailureEntry
from .instruction_manager import InstructionManager
from .validator import ValidationPipeline
from .correction_detector import CorrectionDetector


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

        # Initialize model with LangChain
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Initialize the language model with LangChain"""
        model_name = self.config.main_model.lower()
        provider = self.config.main_model_provider.lower() if self.config.main_model_provider else None

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
            print(f"Warning: Using mock model for {self.config.main_model}")
            print("Set appropriate API key environment variable for real LLM")
            return MockModel(self.config.main_model, self.config.temperature_main)

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
            print("Warning: langchain-anthropic not installed. Install with: pip install langchain-anthropic")
            return MockModel(self.config.main_model, self.config.temperature_main)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not found. Using mock model.")
            return MockModel(self.config.main_model, self.config.temperature_main)

        return ChatAnthropic(
            model=self.config.main_model,
            temperature=self.config.temperature_main,
            api_key=api_key,
        )

    def _init_openai(self):
        """Initialize OpenAI GPT model"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print("Warning: langchain-openai not installed. Install with: pip install langchain-openai")
            return MockModel(self.config.main_model, self.config.temperature_main)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Using mock model.")
            return MockModel(self.config.main_model, self.config.temperature_main)

        return ChatOpenAI(
            model=self.config.main_model,
            temperature=self.config.temperature_main,
            api_key=api_key,
        )

    def _init_google(self):
        """Initialize Google Gemini model"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            print("Warning: langchain-google-genai not installed. Install with: pip install langchain-google-genai")
            return MockModel(self.config.main_model, self.config.temperature_main)

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found. Using mock model.")
            return MockModel(self.config.main_model, self.config.temperature_main)

        return ChatGoogleGenerativeAI(
            model=self.config.main_model,
            temperature=self.config.temperature_main,
            google_api_key=api_key,
        )

    def _init_deepseek(self):
        """Initialize Deepseek model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print("Warning: langchain-openai not installed. Install with: pip install langchain-openai")
            return MockModel(self.config.main_model, self.config.temperature_main)

        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        
        if not api_key:
            print("Warning: DEEPSEEK_API_KEY not found. Using mock model.")
            return MockModel(self.config.main_model, self.config.temperature_main)

        return ChatOpenAI(
            model=self.config.main_model,
            temperature=self.config.temperature_main,
            api_key=api_key,
            base_url=base_url,
        )

    def _init_openrouter(self):
        """Initialize Openrouter model (via OpenAI-compatible API)"""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print("Warning: langchain-openai not installed. Install with: pip install langchain-openai")
            return MockModel(self.config.main_model, self.config.temperature_main)

        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("Warning: OPENROUTER_API_KEY not found. Using mock model.")
            return MockModel(self.config.main_model, self.config.temperature_main)

        return ChatOpenAI(
            model=self.config.main_model,
            temperature=self.config.temperature_main,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/abxba0/autonomai",
                "X-Title": "AutonomAI Self-Optimizing System",
            },
        )

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
            is_correction, confidence, correction_type = self.correction_detector.detect_correction(
                user_query,
                previous_response=self.last_response,
                conversation_history=conversation_context
            )
            
            if is_correction:
                correction_detected = True
                correction_confidence = confidence
                
                # Create failure entry for implicit feedback
                correction_description = self.correction_detector.create_correction_description(
                    user_query,
                    correction_type,
                    confidence,
                    self.last_response
                )
                
                failure_entry = FailureEntry(
                    trigger_type="implicit_feedback",
                    failure_description=correction_description,
                    user_query=user_query,
                    last_model_output=self.last_response,
                    severity="moderate"
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
        
        # Phase 3: Add successful interactions to golden dataset
        if (validation_passed and not correction_detected and 
            self.config.enable_regression_testing and 
            self.instruction_manager.golden_dataset and
            self.validation_pipeline.validators):
            
            # Only add interactions that had validators and passed
            try:
                validation_rules = [v.__class__.__name__ for v in self.validation_pipeline.validators]
                self.instruction_manager.golden_dataset.add_interaction(
                    user_query=user_query,
                    output=output,
                    instructions_version=self.instruction_manager.current_version or "unknown",
                    model_used=self.config.main_model,
                    validation_rules=validation_rules,
                    tags=["auto_collected"]
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
        
        # Check if JSON is expected in the prompt
        prompt_text = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                prompt_text += msg.content.lower()
        
        # Determine response content based on prompt analysis
        # Note: This is a simple heuristic for testing. Real models would use more sophisticated logic.
        is_json_request = "json" in prompt_text and any(
            keyword in prompt_text for keyword in ["extract", "return", "output"]
        )
        
        # Check if code generation is requested
        is_code_request = any(
            keyword in prompt_text for keyword in ["write a python", "create a python", "python function", "def ", "function called"]
        )
        
        if is_code_request:
            # Return sample Python code based on the request
            if "add" in prompt_text or "sum" in prompt_text:
                response_content = """```python
def add_numbers(a, b):
    \"\"\"Add two numbers and return the sum.\"\"\"
    return a + b
```"""
            elif "filter" in prompt_text and "even" in prompt_text:
                response_content = """```python
def filter_even_numbers(numbers):
    \"\"\"Filter even numbers from a list.\"\"\"
    return [num for num in numbers if num % 2 == 0]
```"""
            elif "reverse" in prompt_text and "word" in prompt_text:
                response_content = """```python
def reverse_words(sentence):
    \"\"\"Reverse each word in a sentence while maintaining word order.\"\"\"
    words = sentence.split()
    reversed_words = [word[::-1] for word in words]
    return ' '.join(reversed_words)
```"""
            elif "hello" in prompt_text or "print" in prompt_text:
                response_content = """```python
def hello_world():
    \"\"\"Print Hello, World!\"\"\"
    print('Hello, World!')
```"""
            else:
                # Generic function example
                response_content = """```python
def example_function():
    \"\"\"Example function demonstrating proper Python structure.\"\"\"
    result = "This is a mock function"
    return result
```"""
        elif is_json_request:
            # Return a sample JSON response for extraction tasks
            # In production, this would be replaced by actual model inference
            response_content = """{
    "invoice_number": "4582-2024",
    "date": "March 15th, 2024",
    "customer_name": "John Smith",
    "customer_email": "j.smith@example.com",
    "customer_phone": "(555) 123-4567",
    "item_name": "Widget Pro Model X",
    "item_price": "$249.99",
    "quantity": "2",
    "shipping": "$15.50",
    "tax": "$43.82",
    "total_amount": "$559.30",
    "payment_method": "Credit Card ending in 8742",
    "tracking_number": "TRK-9384756ABC",
    "order_status": "SHIPPED"
}"""
        else:
            response_content = "Mock response from test model"

        class MockResponse:
            content = response_content

        return MockResponse()
