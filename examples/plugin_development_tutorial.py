#!/usr/bin/env python3
"""
Plugin Development Tutorial

This example demonstrates how to develop custom plugins for AutonomAI.
Learn how to create:
- Custom validators
- Custom workflow step executors
- Custom failure analyzers

The plugin system allows you to extend AutonomAI without modifying core code.

Usage:
    python examples/plugin_development_tutorial.py
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from src.plugins.base import ValidatorPlugin, WorkflowStepPlugin, PluginMetadata
from src.core.validator import ValidationResult
from dotenv import load_dotenv


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")


# ==============================================================================
# Example 1: Custom Validator Plugin
# ==============================================================================

class EmailValidatorPlugin(ValidatorPlugin):
    """
    Custom validator that checks if output contains valid email addresses.

    This demonstrates:
    - Inheriting from ValidatorPlugin
    - Implementing validate() method
    - Providing metadata
    - Basic string pattern matching
    """

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="email_validator",
            version="1.0.0",
            description="Validates that output contains valid email addresses",
            author="AutonomAI Team",
            plugin_type="validator"
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate that output contains at least one valid email address.

        Args:
            output: The text to validate
            context: Optional context with 'require_domain' key

        Returns:
            ValidationResult with success status and message
        """
        import re

        # Email regex pattern (simplified)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Find all emails
        emails = re.findall(email_pattern, output)

        if not emails:
            return ValidationResult(
                passed=False,
                message="No valid email addresses found in output"
            )

        # Check for required domain if specified
        if context and "require_domain" in context:
            required_domain = context["require_domain"]
            domain_found = any(required_domain in email for email in emails)

            if not domain_found:
                return ValidationResult(
                    passed=False,
                    message=f"No email with required domain '{required_domain}' found"
                )

        return ValidationResult(
            passed=True,
            message=f"Found {len(emails)} valid email address(es)"
        )


# ==============================================================================
# Example 2: Advanced Validator with Configuration
# ==============================================================================

class SentimentValidatorPlugin(ValidatorPlugin):
    """
    Validates that text has positive sentiment.

    This demonstrates:
    - Configuration options
    - More complex validation logic
    - Threshold-based validation
    """

    def __init__(self, min_positive_score: float = 0.6):
        """
        Initialize with configuration.

        Args:
            min_positive_score: Minimum positive sentiment score (0.0 - 1.0)
        """
        super().__init__()
        self.min_positive_score = min_positive_score

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sentiment_validator",
            version="1.0.0",
            description="Validates text sentiment is positive",
            author="AutonomAI Team",
            plugin_type="validator",
            config_schema={
                "min_positive_score": {
                    "type": "float",
                    "default": 0.6,
                    "min": 0.0,
                    "max": 1.0,
                    "description": "Minimum positive sentiment score required"
                }
            }
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Simple sentiment analysis (counting positive/negative words).

        In production, you'd use a real sentiment analysis library.
        """
        # Simple word-based sentiment analysis
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful',
                         'fantastic', 'love', 'happy', 'perfect', 'best'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'hate',
                         'worst', 'poor', 'disappointing', 'sad', 'angry'}

        words = output.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            # Neutral - default to passing
            return ValidationResult(
                passed=True,
                message="No clear sentiment detected (neutral)"
            )

        positive_score = positive_count / total_sentiment_words

        if positive_score >= self.min_positive_score:
            return ValidationResult(
                passed=True,
                message=f"Positive sentiment detected (score: {positive_score:.2f})"
            )
        else:
            return ValidationResult(
                passed=False,
                message=f"Insufficient positive sentiment (score: {positive_score:.2f}, required: {self.min_positive_score:.2f})"
            )


# ==============================================================================
# Example 3: Custom Workflow Step Plugin
# ==============================================================================

class DataEnrichmentStepPlugin(WorkflowStepPlugin):
    """
    Custom workflow step that enriches data with external information.

    This demonstrates:
    - Workflow step execution
    - State management
    - Error handling
    - Result formatting
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="data_enrichment",
            version="1.0.0",
            description="Enriches data with additional context",
            author="AutonomAI Team",
            plugin_type="workflow_step"
        )

    def execute(
        self,
        step_input: Any,
        context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the data enrichment step.

        Args:
            step_input: Input data to enrich
            context: Execution context
            state: Workflow state

        Returns:
            Dict with enriched data and metadata
        """
        try:
            # Simulate data enrichment
            enriched_data = {
                "original": step_input,
                "enriched_fields": {
                    "timestamp": "2026-01-24T12:00:00Z",
                    "source": "data_enrichment_plugin",
                    "confidence": 0.95,
                    "metadata": {
                        "processor": self.get_metadata().name,
                        "version": self.get_metadata().version
                    }
                }
            }

            return {
                "success": True,
                "data": enriched_data,
                "message": "Data enriched successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Enrichment failed: {e}"
            }


# ==============================================================================
# Example 4: Utility Plugin with Multiple Methods
# ==============================================================================

class TextProcessingPlugin(ValidatorPlugin):
    """
    Multi-purpose text processing plugin.

    This demonstrates:
    - Multiple utility methods
    - Helper functions
    - Reusable components
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="text_processing",
            version="1.0.0",
            description="Advanced text processing and validation",
            author="AutonomAI Team",
            plugin_type="validator"
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validates text meets quality standards.
        """
        checks = context.get("checks", ["length", "formatting"]) if context else ["length", "formatting"]

        issues = []

        if "length" in checks:
            if len(output.split()) < 10:
                issues.append("Text too short (minimum 10 words)")

        if "formatting" in checks:
            if not output[0].isupper():
                issues.append("Text should start with capital letter")

            if not output.rstrip().endswith(('.', '!', '?')):
                issues.append("Text should end with proper punctuation")

        if "professionalism" in checks:
            unprofessional_words = ['very', 'really', 'just', 'maybe']
            found = [word for word in unprofessional_words if word in output.lower()]
            if found:
                issues.append(f"Avoid filler words: {', '.join(found)}")

        if issues:
            return ValidationResult(
                passed=False,
                message=f"Quality issues found: {'; '.join(issues)}"
            )

        return ValidationResult(
            passed=True,
            message="Text meets quality standards"
        )

    # Helper methods (not part of plugin interface, but useful)
    def count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())

    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        import re
        return re.split(r'[.!?]+', text)


# ==============================================================================
# Demonstration Functions
# ==============================================================================

def demo_1_email_validator():
    """Demo 1: Using the email validator plugin"""
    print_section("Demo 1: Email Validator Plugin")

    validator = EmailValidatorPlugin()

    # Show metadata
    metadata = validator.get_metadata()
    print(f"\nPlugin: {metadata.name} v{metadata.version}")
    print(f"Description: {metadata.description}")
    print(f"Type: {metadata.plugin_type}")

    print_subsection("Test Cases")

    test_cases = [
        ("Contact us at support@example.com", None, True),
        ("No email here!", None, False),
        ("Reach out: admin@acme.com, sales@acme.com", None, True),
        ("Email: user@example.com", {"require_domain": "acme.com"}, False),
        ("Email: admin@acme.com", {"require_domain": "acme.com"}, True),
    ]

    for i, (text, context, expected) in enumerate(test_cases, 1):
        result = validator.validate(text, context)
        status = "✓" if result.passed == expected else "✗"
        print(f"\n{status} Test {i}: {text[:40]}...")
        print(f"  Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"  Message: {result.message}")


def demo_2_sentiment_validator():
    """Demo 2: Using the sentiment validator plugin"""
    print_section("Demo 2: Sentiment Validator Plugin")

    validator = SentimentValidatorPlugin(min_positive_score=0.6)

    print_subsection("Test Cases")

    test_cases = [
        "This is absolutely amazing and wonderful!",
        "This is terrible and awful.",
        "This is a neutral statement about facts.",
        "I love this! It's great and fantastic.",
        "Not bad, but could be better.",
    ]

    for i, text in enumerate(test_cases, 1):
        result = validator.validate(text)
        status = "✓" if result.passed else "✗"
        print(f"\n{status} Test {i}: {text}")
        print(f"  Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"  Message: {result.message}")


def demo_3_workflow_step_plugin():
    """Demo 3: Using the workflow step plugin"""
    print_section("Demo 3: Workflow Step Plugin")

    plugin = DataEnrichmentStepPlugin()

    print_subsection("Enriching Data")

    test_data = {
        "user_id": "12345",
        "action": "purchase",
        "amount": 99.99
    }

    print(f"\nOriginal Data: {test_data}")

    result = plugin.execute(
        step_input=test_data,
        context={},
        state={}
    )

    if result["success"]:
        print(f"\n✓ Enrichment successful!")
        print(f"  Enriched Data: {result['data']}")
    else:
        print(f"\n✗ Enrichment failed: {result['message']}")


def demo_4_text_processing_plugin():
    """Demo 4: Using the text processing plugin"""
    print_section("Demo 4: Text Processing Plugin")

    validator = TextProcessingPlugin()

    print_subsection("Quality Checks")

    test_cases = [
        ("Short text.", ["length"]),
        ("this text has issues with formatting", ["formatting"]),
        ("This is a properly formatted sentence.", ["formatting"]),
        ("This is very really just maybe a sentence.", ["professionalism"]),
        ("This is a well-written professional sentence with proper formatting.", ["length", "formatting", "professionalism"]),
    ]

    for i, (text, checks) in enumerate(test_cases, 1):
        result = validator.validate(text, {"checks": checks})
        status = "✓" if result.passed else "✗"
        print(f"\n{status} Test {i}: {text}")
        print(f"  Checks: {', '.join(checks)}")
        print(f"  Result: {'PASS' if result.passed else 'FAIL'}")
        print(f"  Message: {result.message}")


def demo_5_plugin_integration():
    """Demo 5: Integrating plugins with AutonomAI"""
    print_section("Demo 5: Plugin Integration with AutonomAI")

    load_dotenv()

    print("\nNote: This demonstrates the concept of plugin integration.")
    print("To fully integrate plugins, you would:")
    print("  1. Register plugins with the PluginManager")
    print("  2. Add plugins to the system's validator pipeline")
    print("  3. Configure plugin-specific settings")

    print_subsection("Example Integration Code")

    print("""
# Pseudo-code for plugin integration:

from src.plugins.manager import PluginManager
from src import SelfOptimizingSystem, SystemConfig

# Initialize plugin manager
plugin_manager = PluginManager()

# Load and register custom plugins
email_validator = EmailValidatorPlugin()
sentiment_validator = SentimentValidatorPlugin(min_positive_score=0.7)

plugin_manager.register_plugin(email_validator)
plugin_manager.register_plugin(sentiment_validator)

# Create system with plugin manager
config = SystemConfig(
    main_model="mock",
    critic_model="mock"
)

system = SelfOptimizingSystem(config)

# Add plugin validators to the validation pipeline
system.validation_pipeline.validators.extend([
    email_validator,
    sentiment_validator
])

# Now when you execute queries, plugins will be used
result = system.execute("Generate an email with positive tone")
    """)


def main():
    """Run all plugin development demos"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   Plugin Development Tutorial                            ║
║                                                                           ║
║  Learn how to create custom plugins for AutonomAI:                       ║
║  - Custom validators                                                     ║
║  - Workflow step executors                                               ║
║  - Failure analyzers                                                     ║
║  - Integration with the plugin system                                    ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        demo_1_email_validator()
        demo_2_sentiment_validator()
        demo_3_workflow_step_plugin()
        demo_4_text_processing_plugin()
        demo_5_plugin_integration()

        print_section("Plugin Development Best Practices")
        print("""
✓ Plugin Design Principles:
  1. Single Responsibility: Each plugin does one thing well
  2. Clear Metadata: Provide comprehensive plugin information
  3. Error Handling: Gracefully handle all errors
  4. Configuration: Make plugins configurable when appropriate
  5. Documentation: Document parameters and return values
  6. Testing: Write unit tests for your plugins
  7. Versioning: Use semantic versioning for plugins

✓ Plugin Types Available:
  - ValidatorPlugin: Custom validation logic
  - WorkflowStepPlugin: Custom workflow executors
  - OptimizerPlugin: Custom failure analysis (advanced)

✓ Plugin Distribution:
  1. Entry Points: Use setuptools entry_points for discovery
  2. Directory: Place in src/plugins/custom/
  3. Configuration: Define in plugin_config.yaml
  4. Package: Distribute as separate pip package

✓ Development Workflow:
  1. Create plugin class inheriting from base plugin type
  2. Implement required methods (get_metadata, validate/execute)
  3. Test plugin in isolation
  4. Register with PluginManager
  5. Integrate with system
  6. Document usage

✓ Advanced Features:
  - State Management: Plugins can maintain state
  - Context Awareness: Use context for dynamic behavior
  - Chaining: Combine multiple plugins
  - Async Support: Support async operations
  - Caching: Cache plugin results for performance

For more information, see:
  - docs/plugin-system.md
  - src/plugins/README.md
  - examples/plugins/ (example plugins)
        """)

    except KeyboardInterrupt:
        print("\n\nTutorial interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error in tutorial: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
