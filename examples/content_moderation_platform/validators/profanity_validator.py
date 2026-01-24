"""
Profanity detection validator
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from src.plugins.base import ValidatorPlugin, PluginMetadata
from src.core.validator import ValidationResult
from typing import Dict, Any, Set
import re


class ProfanityValidator(ValidatorPlugin):
    """
    Detects profanity and offensive language in content.

    Features:
    - Configurable word lists
    - Leetspeak detection (f*ck, fu€k, etc.)
    - Context-aware scoring
    - Severity levels
    """

    def __init__(
        self,
        custom_wordlist: Set[str] = None,
        severity_threshold: float = 0.5,
        allow_mild_profanity: bool = False
    ):
        super().__init__()
        self.severity_threshold = severity_threshold
        self.allow_mild_profanity = allow_mild_profanity

        # Default profanity wordlist (mild for demonstration)
        self.severe_words = {
            "f***", "s***", "b****", "d***",  # Censored for safety
            # In production, use comprehensive lists or libraries like better-profanity
        }

        self.mild_words = {
            "damn", "hell", "crap", "suck"
        }

        # Combine with custom wordlist
        if custom_wordlist:
            self.severe_words.update(custom_wordlist)

        # Leetspeak mappings
        self.leetspeak_map = {
            '0': 'o', '1': 'i', '3': 'e', '4': 'a',
            '5': 's', '7': 't', '8': 'b', '9': 'g',
            '@': 'a', '$': 's', '!': 'i', '€': 'e'
        }

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="profanity_validator",
            version="1.0.0",
            description="Detects profanity and offensive language",
            author="AutonomAI Team",
            plugin_type="validator",
            config_schema={
                "severity_threshold": {
                    "type": "float",
                    "default": 0.5,
                    "description": "Minimum severity to fail validation"
                },
                "allow_mild_profanity": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to allow mild profanity"
                }
            }
        )

    def normalize_leetspeak(self, text: str) -> str:
        """Convert leetspeak to normal characters"""
        normalized = text.lower()
        for leet, normal in self.leetspeak_map.items():
            normalized = normalized.replace(leet, normal)
        return normalized

    def detect_profanity(self, text: str) -> Dict[str, Any]:
        """Detect profanity and calculate severity"""
        normalized_text = self.normalize_leetspeak(text)
        words = re.findall(r'\b\w+\b', normalized_text)

        severe_matches = []
        mild_matches = []

        for word in words:
            # Check severe profanity
            for severe_word in self.severe_words:
                if severe_word in word or self._fuzzy_match(word, severe_word):
                    severe_matches.append(word)
                    break

            # Check mild profanity
            if word in self.mild_words:
                mild_matches.append(word)

        # Calculate severity (0.0 - 1.0)
        severity = 0.0
        if severe_matches:
            severity = min(1.0, 0.6 + (len(severe_matches) * 0.2))
        elif mild_matches:
            severity = min(0.5, 0.2 + (len(mild_matches) * 0.1))

        return {
            "has_profanity": len(severe_matches) > 0 or (not self.allow_mild_profanity and len(mild_matches) > 0),
            "severity": severity,
            "severe_count": len(severe_matches),
            "mild_count": len(mild_matches),
            "matches": severe_matches + mild_matches
        }

    def _fuzzy_match(self, word: str, pattern: str) -> bool:
        """Fuzzy match for profanity with wildcards"""
        # Simple fuzzy matching - in production use more sophisticated algorithms
        if len(word) < len(pattern) - pattern.count('*'):
            return False

        pattern_regex = pattern.replace('*', '.')
        return bool(re.search(pattern_regex, word))

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate content for profanity"""

        # Get tenant-specific settings if provided
        if context:
            self.allow_mild_profanity = context.get("allow_mild_profanity", self.allow_mild_profanity)
            self.severity_threshold = context.get("severity_threshold", self.severity_threshold)

        result = self.detect_profanity(output)

        if result["has_profanity"] and result["severity"] >= self.severity_threshold:
            match_str = ", ".join(result["matches"][:3])  # Show first 3 matches
            if len(result["matches"]) > 3:
                match_str += f", and {len(result["matches"]) - 3} more"

            return ValidationResult(
                passed=False,
                message=f"Profanity detected (severity: {result['severity']:.2f}): {match_str}",
                metadata={
                    "violation_type": "profanity",
                    "severity": result["severity"],
                    "confidence": min(1.0, result["severity"] + 0.2),
                    "evidence": f"Found {result['severe_count']} severe and {result['mild_count']} mild profane words"
                }
            )

        return ValidationResult(
            passed=True,
            message="No significant profanity detected",
            metadata={
                "severity": result["severity"],
                "clean": True
            }
        )
