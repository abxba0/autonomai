"""
Example failure analyzer plugin.

This plugin demonstrates how to create a custom failure analyzer that
extracts patterns from failures and provides insights.
"""

from typing import Optional, Dict, Any, List
from collections import Counter
import re

from src.plugins import FailureAnalyzerPlugin, PluginMetadata, PluginConfig
from src.models.failure import FailureEntry
from src.models.critic_response import CriticResponse


class PatternAnalyzerPlugin(FailureAnalyzerPlugin):
    """
    Analyzes failures to extract common patterns and root causes.
    """
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="pattern_analyzer",
            version="1.0.0",
            author="AutonomAI Team",
            description="Extracts patterns from failures to identify root causes",
            plugin_type="optimizer",
            tags=["analysis", "patterns", "failure-detection"],
        )
    
    def can_handle(self, failure: FailureEntry) -> bool:
        """This analyzer can handle any failure"""
        return True
    
    def extract_patterns(
        self,
        failures: List[FailureEntry],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract patterns from a collection of failures.
        """
        if not failures:
            return {}
        
        # Extract validation errors
        validation_errors = []
        for failure in failures:
            if hasattr(failure, 'validation_results'):
                for result in failure.validation_results:
                    if not result.passed:
                        validation_errors.append(result.error_message)
        
        # Count most common error types
        error_counter = Counter(validation_errors)
        
        # Extract keywords from error messages
        all_errors = " ".join(validation_errors)
        keywords = re.findall(r'\b[a-z]{4,}\b', all_errors.lower())
        keyword_counts = Counter(keywords).most_common(10)
        
        return {
            "total_failures": len(failures),
            "unique_error_types": len(error_counter),
            "most_common_errors": error_counter.most_common(5),
            "common_keywords": keyword_counts,
            "failure_rate": len(failures) / max(1, context.get("total_attempts", 1)) if context else None,
        }
    
    def analyze_failure(
        self,
        failure: FailureEntry,
        current_instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CriticResponse]:
        """
        Analyze a single failure and propose improvements.
        """
        # Extract patterns from this failure
        patterns = self.extract_patterns([failure], context)
        
        if patterns.get("most_common_errors"):
            # Get the most common error
            most_common_error, count = patterns["most_common_errors"][0]
            
            # Generate a simple suggestion based on the error
            suggestion = f"Add specific handling for: {most_common_error}"
            
            # Create a basic critic response
            # Note: In a real plugin, you'd use an LLM or more sophisticated logic
            return CriticResponse(
                should_update=True,
                confidence=0.7,
                proposed_changes=suggestion,
                reasoning=f"Pattern detected: {most_common_error} occurred {count} time(s)",
                affected_sections=["validation"],
            )
        
        return None


class FailureFrequencyAnalyzerPlugin(FailureAnalyzerPlugin):
    """
    Analyzes failure frequency and timing patterns.
    """
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="failure_frequency_analyzer",
            version="1.0.0",
            author="AutonomAI Team",
            description="Analyzes failure frequency and timing patterns",
            plugin_type="optimizer",
            tags=["analysis", "frequency", "timing"],
        )
    
    def can_handle(self, failure: FailureEntry) -> bool:
        """Can handle failures with timestamp information"""
        return hasattr(failure, 'timestamp') and failure.timestamp is not None
    
    def extract_patterns(
        self,
        failures: List[FailureEntry],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract timing and frequency patterns"""
        if not failures:
            return {}
        
        # Sort by timestamp
        sorted_failures = sorted(
            failures,
            key=lambda f: f.timestamp if hasattr(f, 'timestamp') and f.timestamp else ""
        )
        
        # Calculate time between failures
        intervals = []
        for i in range(1, len(sorted_failures)):
            if hasattr(sorted_failures[i], 'timestamp') and hasattr(sorted_failures[i-1], 'timestamp'):
                # This is simplified - in reality you'd parse timestamps
                pass
        
        return {
            "total_failures": len(failures),
            "time_span": f"{sorted_failures[0].timestamp} to {sorted_failures[-1].timestamp}"
                if len(sorted_failures) > 1 else "single failure",
            "failure_frequency": "high" if len(failures) > 10 else "moderate" if len(failures) > 5 else "low",
        }


# Example usage:
if __name__ == "__main__":
    from src.plugins import PluginManager
    
    # Create and register plugin
    manager = PluginManager()
    
    plugin = PatternAnalyzerPlugin(
        PatternAnalyzerPlugin.get_metadata(),
        PluginConfig(enabled=True, priority=100)
    )
    
    if manager.register_plugin(plugin):
        print(f"✓ Plugin {plugin.metadata.name} registered and initialized")
        
        # Example: Find optimizer for a failure
        # failure = FailureEntry(...)
        # optimizer = manager.find_optimizer_for_failure(failure)
        # if optimizer:
        #     response = optimizer.analyze_failure(failure, "current instructions")
    else:
        print(f"✗ Plugin registration failed")
