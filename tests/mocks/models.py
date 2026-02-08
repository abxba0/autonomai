"""
Mock implementations of core components for testing without API calls.

These mock classes simulate the behavior of real LLM models and system components
without making actual API calls or performing expensive operations.
"""

import json
import sys
import os
from typing import Any, List, Dict, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.core.rule_graph import RuleGraph
from src.core.multimodal_validator import MultiModalValidator, VisionValidationResult, AudioValidationResult
from src.core.tenant_manager import TenantManager

# Import demo data fixtures
from .fixtures import (
    MOCK_INVOICE_JSON,
    MOCK_CODE_ADD_NUMBERS,
    MOCK_CODE_FILTER_EVEN,
    MOCK_CODE_REVERSE_WORDS,
    MOCK_CODE_HELLO_WORLD,
    MOCK_CODE_GENERIC,
    MOCK_GENERIC_RESPONSE,
)


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
            if hasattr(msg, "content"):
                prompt_text += msg.content.lower()

        # Determine response content based on prompt analysis
        # Note: This is a simple heuristic for testing. Real models would use more sophisticated logic.
        is_json_request = "json" in prompt_text and any(
            keyword in prompt_text for keyword in ["extract", "return", "output"]
        )

        # Check if code generation is requested
        is_code_request = any(
            keyword in prompt_text
            for keyword in [
                "write a python",
                "create a python",
                "python function",
                "def ",
                "function called",
            ]
        )

        if is_code_request:
            # Return sample Python code based on the request
            if "add" in prompt_text or "sum" in prompt_text:
                response_content = MOCK_CODE_ADD_NUMBERS
            elif "filter" in prompt_text and "even" in prompt_text:
                response_content = MOCK_CODE_FILTER_EVEN
            elif "reverse" in prompt_text and "word" in prompt_text:
                response_content = MOCK_CODE_REVERSE_WORDS
            elif "hello" in prompt_text or "print" in prompt_text:
                response_content = MOCK_CODE_HELLO_WORLD
            else:
                # Generic function example
                response_content = MOCK_CODE_GENERIC
        elif is_json_request:
            # Return a sample JSON response for extraction tasks
            # In production, this would be replaced by actual model inference
            response_content = MOCK_INVOICE_JSON
        else:
            response_content = MOCK_GENERIC_RESPONSE

        class MockResponse:
            content = response_content

        return MockResponse()


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


class MockJudgeModel:
    """Mock judge model for testing"""

    def __init__(self, model_name: str, temperature: float):
        self.model_name = model_name
        self.temperature = temperature

    def invoke(self, messages):
        """Mock invoke for LangChain compatibility"""

        class MockResponse:
            content = json.dumps(
                {
                    "approved": True,
                    "reasoning": "Mock judge approval. This proposed change looks reasonable and doesn't appear to contradict the base instructions.",
                    "conflicts_detected": False,
                    "conflict_details": None,
                    "confidence_score": 0.85,
                    "suggestions": None,
                }
            )

        return MockResponse()


class MockRuleGraph(RuleGraph):
    """Mock rule graph for testing without actual storage"""

    def save(self):
        """Override save to do nothing in tests"""
        pass

    def load(self):
        """Override load to do nothing in tests"""
        pass


class MockMultiModalValidator(MultiModalValidator):
    """Mock validator for testing without actual multi-modal processing"""

    def __init__(self, config=None):
        super().__init__(config)
        self.mock_results = {}

    def set_mock_result(self, modality: str, result: Dict[str, Any]):
        """Set mock result for testing"""
        self.mock_results[modality] = result

    def validate_vision(self, *args, **kwargs) -> VisionValidationResult:
        """Return mock vision result"""
        if "vision" in self.mock_results:
            return VisionValidationResult(**self.mock_results["vision"])
        return VisionValidationResult(is_valid=True, confidence=1.0)

    def validate_audio(self, *args, **kwargs) -> AudioValidationResult:
        """Return mock audio result"""
        if "audio" in self.mock_results:
            return AudioValidationResult(**self.mock_results["audio"])
        return AudioValidationResult(is_valid=True, confidence=1.0)


class MockTenantManager(TenantManager):
    """Mock tenant manager for testing without actual storage"""

    def save(self):
        """Override save to do nothing in tests"""
        pass

    def load(self):
        """Override load to do nothing in tests"""
        pass
