#!/usr/bin/env python3
"""
Self-Healing Code Assistant Example

Demonstrates an agent that generates Python scripts on user request. After generation,
a validator checks for valid Python syntax and optionally runs a linter. If the code
does not pass (syntax or style), the critic updates the instruction set to improve
code quality in future generations.

This example showcases:
1. Python code generation with syntax validation
2. Optional style checking with linting
3. Self-optimization when code quality issues are detected
4. Iterative improvement: fail → analyze → improve → retry
5. Learning from mistakes to write better code over time
"""

import sys
import os
import ast
import re
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig, CustomValidator
from src.core.validator import ValidationResult


# Configuration for demo
MAX_CODE_GENERATION_ATTEMPTS = 3  # Maximum attempts to generate valid code


class PythonCodeValidator(CustomValidator):
    """
    Validator that checks if generated Python code is syntactically valid
    and follows basic style guidelines.
    """

    # Style rules configuration
    STYLE_RULES = {
        "no_tabs": {
            "enabled": True,
            "severity": "moderate",
            "message": "Use spaces instead of tabs for indentation",
        },
        "require_docstrings": {
            "enabled": True,
            "severity": "moderate",
            "message": "Functions should have docstrings",
        },
        "max_line_length": {
            "enabled": True,
            "severity": "low",
            "limit": 120,
            "message": "Lines should not exceed 120 characters",
        },
        "no_bare_except": {
            "enabled": True,
            "severity": "high",
            "message": "Avoid bare except clauses - specify exception types",
        },
    }

    def __init__(self, check_style: bool = True):
        """
        Initialize the Python code validator.

        Args:
            check_style: If True, also check for style issues
        """
        self.check_style = check_style
        super().__init__("PythonCodeValidator", self.validate_python_code)

    def validate_python_code(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate that the output contains valid Python code.
        """
        # Extract code from output (handle markdown code blocks)
        code = self._extract_code(output)

        if not code:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message="No Python code found in output",
                error_details={
                    "error": "Output does not contain Python code",
                    "suggestion": "Ensure output includes Python code in ```python code blocks or as plain text",
                },
            )

        violations = []

        # Check 1: Syntax validation using AST
        syntax_valid, syntax_error = self._check_syntax(code)
        if not syntax_valid:
            violations.append(
                {
                    "type": "syntax_error",
                    "severity": "critical",
                    "message": f"Python syntax error: {syntax_error}",
                    "details": syntax_error,
                }
            )

        # Check 2: Style validation (if enabled and syntax is valid)
        if self.check_style and syntax_valid:
            style_issues = self._check_style_issues(code)
            violations.extend(style_issues)

        # If violations found, fail validation
        if violations:
            # Determine highest severity
            severity_order = {"low": 1, "moderate": 2, "high": 3, "critical": 4}
            max_severity = max(
                (severity_order.get(v.get("severity", "low"), 1) for v in violations),
                default=1,
            )
            highest_severity = next(
                (sev for sev, val in severity_order.items() if val == max_severity),
                "low",
            )

            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Code quality issues: Found {len(violations)} problem(s)",
                error_details={
                    "violations": violations,
                    "total_violations": len(violations),
                    "highest_severity": highest_severity,
                    "code_snippet": code[:200] + ("..." if len(code) > 200 else ""),
                },
            )

        return ValidationResult(
            passed=True,
            validator_name=self.name,
            error_message=None,
            error_details={
                "status": "valid",
                "code_lines": len(code.splitlines()),
                "message": "Code is syntactically valid and follows style guidelines",
            },
        )

    def _extract_code(self, output: str) -> str:
        """Extract Python code from output, handling markdown code blocks."""
        # Try to find code in markdown code blocks first
        code_block_pattern = r"```(?:python)?\s*\n(.*?)```"
        matches = re.findall(code_block_pattern, output, re.DOTALL)

        if matches:
            # Use the first code block found
            return matches[0].strip()

        # If no code blocks, check if the entire output looks like code
        # (starts with def, class, import, or has proper indentation)
        if re.match(r"^\s*(def|class|import|from|#)", output.strip(), re.MULTILINE):
            return output.strip()

        return ""

    def _check_syntax(self, code: str) -> tuple[bool, str]:
        """
        Check if code is syntactically valid using Python's AST parser.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  {e.text.strip()}"
            return False, error_msg
        except Exception as e:
            return False, str(e)

    def _check_style_issues(self, code: str) -> list[Dict[str, Any]]:
        """Check for common style issues in the code."""
        issues = []
        lines = code.splitlines()

        # Check for tabs
        if self.STYLE_RULES["no_tabs"]["enabled"]:
            if "\t" in code:
                issues.append(
                    {
                        "type": "style_issue",
                        "severity": self.STYLE_RULES["no_tabs"]["severity"],
                        "message": self.STYLE_RULES["no_tabs"]["message"],
                        "rule": "no_tabs",
                    }
                )

        # Check for bare except clauses
        if self.STYLE_RULES["no_bare_except"]["enabled"]:
            if re.search(r"except\s*:", code):
                issues.append(
                    {
                        "type": "style_issue",
                        "severity": self.STYLE_RULES["no_bare_except"]["severity"],
                        "message": self.STYLE_RULES["no_bare_except"]["message"],
                        "rule": "no_bare_except",
                    }
                )

        # Check for docstrings in functions
        if self.STYLE_RULES["require_docstrings"]["enabled"]:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check if function has a docstring
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            issues.append(
                                {
                                    "type": "style_issue",
                                    "severity": self.STYLE_RULES["require_docstrings"][
                                        "severity"
                                    ],
                                    "message": f"Function '{node.name}' is missing a docstring",
                                    "rule": "require_docstrings",
                                }
                            )
            except Exception:
                # If we can't parse, skip docstring check
                pass

        # Check line length
        if self.STYLE_RULES["max_line_length"]["enabled"]:
            max_length = self.STYLE_RULES["max_line_length"]["limit"]
            long_lines = [
                (i + 1, len(line))
                for i, line in enumerate(lines)
                if len(line) > max_length
            ]
            if long_lines:
                issues.append(
                    {
                        "type": "style_issue",
                        "severity": self.STYLE_RULES["max_line_length"]["severity"],
                        "message": f"{len(long_lines)} line(s) exceed {max_length} characters",
                        "rule": "max_line_length",
                        "details": f"Lines: {', '.join(str(line_num) for line_num, _ in long_lines[:3])}",
                    }
                )

        return issues


# Test cases for code generation
CODE_GENERATION_TASKS = [
    {
        "name": "Simple Calculator Function",
        "description": "Create a Python function that adds two numbers",
        "prompt": "Write a Python function called 'add_numbers' that takes two parameters and returns their sum.",
        "category": "basic",
    },
    {
        "name": "List Processing",
        "description": "Create a function that filters even numbers from a list",
        "prompt": "Write a Python function called 'filter_even_numbers' that takes a list of integers and returns a new list containing only the even numbers.",
        "category": "intermediate",
    },
    {
        "name": "String Manipulation",
        "description": "Create a function that reverses words in a sentence",
        "prompt": "Write a Python function called 'reverse_words' that takes a sentence (string) and returns the sentence with each word reversed, but maintaining the word order.",
        "category": "intermediate",
    },
]


def run_code_generation_test(
    system: SelfOptimizingSystem, test_case: Dict[str, str], attempt_num: int = 1
):
    """
    Run a single code generation test case.
    """
    print(f"\n{'='*70}")
    print(f"🧑‍💻 CODE GENERATION TEST - Attempt #{attempt_num}")
    print(f"{'='*70}")
    print(f"\nTask: {test_case['name']}")
    print(f"Category: {test_case['category']}")
    print(f"\n📝 Request:")
    print(f"   \"{test_case['prompt']}\"")
    print()

    result = system.execute(test_case["prompt"])

    print(f"🤖 Generated Code:")
    # Extract and display the code
    code_output = result["output"]
    print("-" * 70)
    print(code_output[:500] + ("..." if len(code_output) > 500 else ""))
    print("-" * 70)
    print()

    # Check validation result
    if result["validation_passed"]:
        print("✅ CODE VALIDATION: PASSED")
        print(
            "   The generated code is syntactically valid and follows style guidelines!"
        )

        # Show validation details
        for val_result in result.get("validation_results", []):
            if val_result.passed and val_result.error_details:
                details = val_result.error_details
                print(f"   ✓ Code lines: {details.get('code_lines', 'N/A')}")
                print(f"   ✓ Status: {details.get('message', 'Valid')}")
    else:
        print("❌ CODE VALIDATION: FAILED")
        print("   ⚠️  CODE QUALITY ISSUES DETECTED!")

        # Show violation details
        for val_result in result.get("validation_results", []):
            if not val_result.passed and val_result.error_details:
                violations = val_result.error_details.get("violations", [])
                print(f"\n   Found {len(violations)} issue(s):")
                for i, violation in enumerate(violations, 1):
                    print(
                        f"   {i}. [{violation.get('severity', 'unknown').upper()}] {violation['type']}"
                    )
                    print(f"      {violation['message']}")
                    if "details" in violation:
                        print(f"      Details: {violation['details']}")

        # Check if optimization was triggered
        if result.get("optimization_attempted"):
            opt_result = result["optimization_result"]
            print(
                f"\n🔄 SELF-HEALING: {'SUCCESS' if opt_result.get('success') else 'FAILED'}"
            )

            if opt_result.get("success"):
                print("   ✓ Code generation instructions have been updated!")
                print(
                    f"   ✓ Changes: {opt_result.get('diff_summary', 'Instructions improved for better code quality')}"
                )
                print("   ✓ System will now generate better code in future attempts")
            else:
                print(f"   ✗ Reason: {opt_result.get('message', 'Unknown error')}")

    return result


def main():
    """Demonstrate self-healing code assistant"""

    print("=" * 70)
    print("🛠️  SELF-HEALING CODE ASSISTANT DEMO")
    print("=" * 70)
    print()

    print("This example demonstrates:")
    print("  • Python code generation with validation")
    print("  • Syntax checking using Python's AST parser")
    print("  • Style validation (tabs, docstrings, line length, etc.)")
    print("  • Self-optimization when code quality issues are detected")
    print("  • Iterative improvement cycle for better code generation")
    print()
    print("-" * 70)

    # Initialize system with code generation configuration
    print("\n🔧 Initializing code assistant...")

    config = SystemConfig(
        main_model="gpt-4o-mini",
        main_model_provider="openai",
        critic_model="gpt-4o-mini",
        critic_model_provider="openai",
        enable_auto_optimization=True,
        max_optimization_attempts=3,
        temperature_main=0.3,  # Lower temperature for more consistent code
        temperature_critic=0.1,  # Very low for precise analysis
    )

    system = SelfOptimizingSystem(config)

    print(f"   ✓ System initialized")

    # Add the Python code validator
    code_validator = PythonCodeValidator(check_style=True)
    system.add_validator(code_validator)

    print("   ✓ PythonCodeValidator installed")
    print("   ✓ Checking for: syntax errors, style issues, docstrings, line length")

    # Run baseline test
    print("\n" + "=" * 70)
    print("🧪 BASELINE TEST")
    print("=" * 70)
    print("\nTesting with a simple request to verify system is operational...")

    baseline_task = {
        "name": "Hello World",
        "prompt": "Write a Python function that prints 'Hello, World!' with a docstring.",
        "category": "basic",
    }

    baseline = run_code_generation_test(system, baseline_task, attempt_num=1)

    # Run code generation tests
    print("\n\n" + "=" * 70)
    print("🎯 CODE GENERATION TEST SEQUENCE")
    print("=" * 70)
    print("\nTesting various code generation tasks to demonstrate self-healing...")

    successful_generations = 0
    failed_generations = 0
    optimizations_performed = 0

    for i, test_case in enumerate(CODE_GENERATION_TASKS, 1):
        result = run_code_generation_test(system, test_case, attempt_num=i)

        if result["validation_passed"]:
            successful_generations += 1
        else:
            failed_generations += 1
            if result.get("optimization_attempted") and result[
                "optimization_result"
            ].get("success"):
                optimizations_performed += 1

        # Small delay indication between tasks
        if i < len(CODE_GENERATION_TASKS):
            print("\n⏳ Preparing next task...\n")

    # Summary Report
    print("\n" + "=" * 70)
    print("📊 CODE GENERATION ASSESSMENT REPORT")
    print("=" * 70)

    total_tests = len(CODE_GENERATION_TASKS)
    success_rate = (
        (successful_generations / total_tests * 100) if total_tests > 0 else 0
    )

    print(f"\n📈 Test Results:")
    print(f"   • Total Generation Attempts: {total_tests}")
    print(f"   • Successful Generations: {successful_generations}")
    print(f"   • Failed Generations: {failed_generations}")
    print(f"   • Success Rate: {success_rate:.1f}%")
    print(f"\n🔄 Self-Healing Activity:")
    print(f"   • Optimizations Performed: {optimizations_performed}")
    print(
        f"   • Learning Status: {'ACTIVE' if optimizations_performed > 0 else 'NO ISSUES DETECTED'}"
    )

    # Show version history
    print(f"\n📚 Improvement History:")
    history = system.get_version_history()
    if history:
        for i, version in enumerate(history[-3:], 1):
            print(f"   {i}. {version['version_id']}")
            print(f"      Trigger: {version['trigger_type']}")
            print(f"      Changes: {version['diff_summary']}")
    else:
        print("   No updates recorded (using mock models)")

    # Final assessment
    print("\n" + "=" * 70)
    print("💡 KEY TAKEAWAYS")
    print("=" * 70)
    print(
        """
This example demonstrates practical AI code generation with quality assurance:

1. **Syntax Validation**: Uses Python's AST parser to ensure generated code
   is syntactically correct and will actually run without errors.

2. **Style Checking**: Enforces coding best practices like:
   - Proper indentation (spaces vs tabs)
   - Docstrings for functions
   - Reasonable line length
   - Specific exception handling (no bare except)

3. **Self-Healing**: When code fails validation, the system automatically:
   - Analyzes what went wrong
   - Updates its instructions to avoid similar mistakes
   - Improves code quality over time

4. **Iterative Improvement**: Each validation failure teaches the system
   to generate better code, moving toward:
   - Cleaner, more maintainable code
   - Consistent style across generations
   - Higher first-time success rates

5. **Real-World Applications**:
   - AI-powered code completion tools
   - Automated code generation from requirements
   - Code refactoring assistants
   - Educational tools for learning to code
   - Rapid prototyping and scaffolding

6. **Why This Matters**:
   - Users need code that actually works, not just looks right
   - Manual code review is time-consuming
   - Automated validation catches errors early
   - Learning from mistakes improves reliability
   - Moves toward autonomous development workflows

7. **Enterprise Value**:
   - Reduces debugging time for generated code
   - Ensures consistent code quality standards
   - Demonstrates LLMOps best practices
   - Enables safer AI-assisted development
   - Supports "shift-left" quality assurance
"""
    )

    print("\n" + "=" * 70)
    print("Example Complete!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("   • Try generating your own code with custom requirements")
    print("   • Customize style rules in PythonCodeValidator")
    print("   • Add more sophisticated validation (e.g., security checks)")
    print("   • Integrate with your development workflow")
    print("   • Experiment with different AI models for code generation")


if __name__ == "__main__":
    main()
