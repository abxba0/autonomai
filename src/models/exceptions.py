"""
Custom exceptions for the self-optimizing system.
"""


class ConfigurationError(Exception):
    """
    Raised when the system is not properly configured.
    
    This typically occurs when required API keys or configuration
    parameters are missing.
    """
    pass
