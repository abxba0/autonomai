"""
Pytest configuration and shared fixtures for tests.

This file provides common fixtures that can be used across all test files.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import mock classes
from tests.mocks.models import (
    MockModel,
    MockCriticModel,
    MockJudgeModel,
    MockRuleGraph,
    MockMultiModalValidator,
    MockTenantManager,
)


@pytest.fixture
def mock_model():
    """Provide a mock model for testing"""
    return MockModel(model_name="test-model", temperature=0.0)


@pytest.fixture
def mock_critic_model():
    """Provide a mock critic model for testing"""
    return MockCriticModel(model_name="test-critic", temperature=0.0)


@pytest.fixture
def mock_judge_model():
    """Provide a mock judge model for testing"""
    return MockJudgeModel(model_name="test-judge", temperature=0.0)


@pytest.fixture
def mock_rule_graph():
    """Provide a mock rule graph for testing"""
    return MockRuleGraph()


@pytest.fixture
def mock_multimodal_validator():
    """Provide a mock multimodal validator for testing"""
    return MockMultiModalValidator()


@pytest.fixture
def mock_tenant_manager():
    """Provide a mock tenant manager for testing"""
    return MockTenantManager()
