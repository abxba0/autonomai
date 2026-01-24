"""Hate speech detection validator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from src.plugins.base import ValidatorPlugin, PluginMetadata
from src.core.validator import ValidationResult
from typing import Dict, Any
import re


class HateSpeechValidator(ValidatorPlugin):
    """Detects hate speech and discriminatory content"""

    def __init__(self, severity_threshold: float = 0.6):
        super().__init__()
        self.severity_threshold = severity_threshold

        # Categories of hate speech indicators
        self.indicators = {
            "racial": ["slur1", "slur2"],  # Censored - use real list in production
            "gender": ["misogynist", "sexist"],
            "religious": ["religious_slur"],
            "lgbtq": ["homophobic_term"],
            "disability": ["ableist_term"]
        }

        # Hate speech patterns
        self.patterns = [
            r"\b(all|every)\s+(jews|muslims|christians|blacks|whites|asians|latinos)\s+(are|should)\b",
            r"\b(kill|murder|eliminate)\s+all\s+\w+",
            r"\bgo\s+back\s+to\s+(your\s+country|africa|mexico)",
        ]

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="hate_speech_validator",
            version="1.0.0",
            description="Detects hate speech and discrimination",
            author="AutonomAI Team",
            plugin_type="validator"
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        text_lower = output.lower()
        violations = []
        max_severity = 0.0

        # Check for indicator words
        for category, terms in self.indicators.items():
            for term in terms:
                if term in text_lower:
                    violations.append(f"{category}: {term}")
                    max_severity = max(max_severity, 0.8)

        # Check for patterns
        for pattern in self.patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                violations.append(f"hate_pattern_detected")
                max_severity = max(max_severity, 0.9)

        if violations and max_severity >= self.severity_threshold:
            return ValidationResult(
                passed=False,
                message=f"Hate speech detected (severity: {max_severity:.2f})",
                metadata={
                    "violation_type": "hate_speech",
                    "severity": max_severity,
                    "confidence": 0.85,
                    "evidence": f"Found {len(violations)} hate speech indicators"
                }
            )

        return ValidationResult(passed=True, message="No hate speech detected")
