"""
Example validator plugin that checks for specific keywords.

This plugin demonstrates how to create a custom validator that
integrates with the AutonomAI validation pipeline.
"""

from typing import Optional, Dict, Any
from src.plugins import ValidatorPlugin, PluginMetadata, PluginConfig
from src.core.validator import BaseValidator, ValidationResult


class KeywordValidator(BaseValidator):
    """Validator that checks for required or forbidden keywords"""
    
    def __init__(self, name: str, required_keywords=None, forbidden_keywords=None):
        super().__init__(name)
        self.required_keywords = required_keywords or []
        self.forbidden_keywords = forbidden_keywords or []
    
    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate that output contains required and excludes forbidden keywords"""
        output_lower = output.lower()
        
        # Check required keywords
        missing_required = [
            kw for kw in self.required_keywords
            if kw.lower() not in output_lower
        ]
        if missing_required:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Missing required keywords: {missing_required}",
                error_details={"missing_keywords": missing_required},
            )
        
        # Check forbidden keywords
        found_forbidden = [
            kw for kw in self.forbidden_keywords
            if kw.lower() in output_lower
        ]
        if found_forbidden:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message=f"Found forbidden keywords: {found_forbidden}",
                error_details={"forbidden_keywords": found_forbidden},
            )
        
        return ValidationResult(passed=True, validator_name=self.name)


class KeywordValidatorPlugin(ValidatorPlugin):
    """Plugin wrapper for KeywordValidator"""
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="keyword_validator",
            version="1.0.0",
            author="AutonomAI Team",
            description="Validates output for required and forbidden keywords",
            plugin_type="validator",
            tags=["validation", "keywords", "content-checking"],
        )
    
    def create_validator(self) -> BaseValidator:
        """Create the keyword validator with configured keywords"""
        required = self.config.get("required_keywords", [])
        forbidden = self.config.get("forbidden_keywords", [])
        
        return KeywordValidator(
            name=self.metadata.name,
            required_keywords=required,
            forbidden_keywords=forbidden,
        )


# Example usage:
if __name__ == "__main__":
    from src.plugins import PluginConfig
    from src.core.validator import ValidationPipeline
    
    # Create plugin with configuration
    config = PluginConfig(
        enabled=True,
        priority=50,
        settings={
            "required_keywords": ["important", "verified"],
            "forbidden_keywords": ["error", "failed"],
        }
    )
    
    plugin = KeywordValidatorPlugin(
        KeywordValidatorPlugin.get_metadata(),
        config
    )
    
    # Initialize plugin
    if plugin.initialize():
        print(f"✓ Plugin {plugin.metadata.name} initialized")
        
        # Test validation
        test_output = "This is an important and verified result"
        result = plugin.validator.validate(test_output)
        print(f"Validation result: {'PASS' if result.passed else 'FAIL'}")
        if not result.passed:
            print(f"  Error: {result.error_message}")
    else:
        print(f"✗ Plugin initialization failed")
