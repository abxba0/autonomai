#!/usr/bin/env python3
"""
Test for self_healing_code_assistant example
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from examples.self_healing_code_assistant import (
    PythonCodeValidator,
    CODE_GENERATION_TASKS
)
from src import SelfOptimizingSystem, SystemConfig


def test_python_code_validator_valid_code():
    """Test that the validator accepts valid Python code"""
    validator = PythonCodeValidator(check_style=True)
    
    valid_code = '''```python
def add_numbers(a, b):
    """Add two numbers."""
    return a + b
```'''
    
    result = validator.validate(valid_code)
    assert result.passed, f"Valid code should pass validation: {result.error_message}"


def test_python_code_validator_syntax_error():
    """Test that the validator catches syntax errors"""
    validator = PythonCodeValidator(check_style=True)
    
    invalid_code = '''```python
def broken_function(
    print("missing closing parenthesis"
```'''
    
    result = validator.validate(invalid_code)
    assert not result.passed, "Code with syntax error should fail validation"
    assert result.error_details is not None
    assert "syntax_error" in str(result.error_details).lower()


def test_python_code_validator_style_issues():
    """Test that the validator catches style issues"""
    validator = PythonCodeValidator(check_style=True)
    
    # Code without docstring
    code_no_docstring = '''```python
def no_docstring():
    return True
```'''
    
    result = validator.validate(code_no_docstring)
    assert not result.passed, "Code without docstring should fail validation"
    violations = result.error_details.get('violations', [])
    assert any('docstring' in str(v).lower() for v in violations)


def test_python_code_validator_no_style_check():
    """Test that style checking can be disabled"""
    validator = PythonCodeValidator(check_style=False)
    
    # Code without docstring but valid syntax
    code_no_docstring = '''```python
def no_docstring():
    return True
```'''
    
    result = validator.validate(code_no_docstring)
    # Should pass because style checking is disabled
    assert result.passed, "Valid syntax should pass when style checking is disabled"


def test_code_extraction_from_markdown():
    """Test that code is correctly extracted from markdown blocks"""
    validator = PythonCodeValidator(check_style=False)
    
    code_in_markdown = '''Here is some code:
```python
def hello():
    return "world"
```
And some text after.'''
    
    result = validator.validate(code_in_markdown)
    assert result.passed, "Should extract and validate code from markdown"


def test_code_extraction_plain_text():
    """Test that plain Python code is recognized"""
    validator = PythonCodeValidator(check_style=False)
    
    plain_code = '''def hello():
    return "world"
'''
    
    result = validator.validate(plain_code)
    assert result.passed, "Should validate plain Python code"


def test_self_healing_system_integration():
    """Test that the validator integrates with the self-optimizing system"""
    config = SystemConfig(
        main_model="gpt-4o-mini",
        main_model_provider="openai",
        enable_auto_optimization=False,  # Disable for testing
        temperature_main=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    validator = PythonCodeValidator(check_style=True)
    system.add_validator(validator)
    
    # Test with a simple code generation prompt
    result = system.execute("Write a Python function that returns Hello World")
    
    # Should have output
    assert result['output'] is not None
    assert len(result['output']) > 0
    
    # Validation should have been run
    assert 'validation_passed' in result
    assert 'validation_results' in result


def test_code_generation_tasks_structure():
    """Test that code generation tasks have the required structure"""
    assert len(CODE_GENERATION_TASKS) > 0, "Should have at least one test case"
    
    for task in CODE_GENERATION_TASKS:
        assert 'name' in task, "Task should have a name"
        assert 'prompt' in task, "Task should have a prompt"
        assert 'category' in task, "Task should have a category"
        assert isinstance(task['name'], str)
        assert isinstance(task['prompt'], str)
        assert len(task['prompt']) > 0, "Prompt should not be empty"


def test_validator_handles_empty_output():
    """Test that validator handles empty or invalid output gracefully"""
    validator = PythonCodeValidator(check_style=True)
    
    # Test with empty string
    result = validator.validate("")
    assert not result.passed, "Empty output should fail validation"
    
    # Test with no code
    result = validator.validate("This is just text without any code")
    assert not result.passed, "Text without code should fail validation"


def test_validator_handles_multiple_code_blocks():
    """Test that validator extracts the first code block when multiple are present"""
    validator = PythonCodeValidator(check_style=False)
    
    multiple_blocks = '''First block:
```python
def first():
    return 1
```

Second block:
```python
def second():
    return 2
```'''
    
    result = validator.validate(multiple_blocks)
    # Should validate the first block
    assert result.passed, "Should successfully validate first code block"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
