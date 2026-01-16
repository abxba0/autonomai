"""
Validator plugin interface for extending validation capabilities.
"""

from abc import abstractmethod
from typing import Optional, Dict, Any

from .base import BasePlugin, PluginMetadata, PluginConfig
from ..core.validator import BaseValidator, ValidationResult


class ValidatorPlugin(BasePlugin):
    """
    Base class for validator plugins.
    
    Validator plugins can add custom validation logic to the system.
    They integrate with the existing ValidationPipeline.
    """
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)
        self._validator_instance: Optional[BaseValidator] = None
    
    @abstractmethod
    def create_validator(self) -> BaseValidator:
        """
        Create and return the validator instance.
        
        This method should return a properly configured BaseValidator
        that will be used by the validation pipeline.
        
        Returns:
            BaseValidator instance
        """
        pass
    
    def initialize(self) -> bool:
        """Initialize the validator plugin"""
        try:
            self._validator_instance = self.create_validator()
            return self._validator_instance is not None
        except Exception as e:
            self.set_error(f"Failed to create validator: {e}")
            return False
    
    def cleanup(self):
        """Clean up validator resources"""
        self._validator_instance = None
    
    @property
    def validator(self) -> Optional[BaseValidator]:
        """Get the validator instance"""
        return self._validator_instance
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate validator plugin configuration"""
        # Check that plugin type is correct
        if self.metadata.plugin_type != "validator":
            return False, f"Plugin type must be 'validator', got '{self.metadata.plugin_type}'"
        return True, None


class PluginValidator(BaseValidator):
    """
    Wrapper that makes a ValidatorPlugin usable as a BaseValidator.
    
    This allows ValidatorPlugins to be added to ValidationPipeline.
    """
    
    def __init__(self, plugin: ValidatorPlugin):
        super().__init__(plugin.metadata.name)
        self.plugin = plugin
    
    def validate(
        self, output: str, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Delegate validation to the plugin's validator"""
        if self.plugin.validator:
            return self.plugin.validator.validate(output, context)
        else:
            return ValidationResult(
                passed=False,
                validator_name=self.name,
                error_message="Plugin validator not initialized",
            )
