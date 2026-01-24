"""Spam detection validator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from src.plugins.base import ValidatorPlugin, PluginMetadata
from src.core.validator import ValidationResult
from typing import Dict, Any
import re


class SpamValidator(ValidatorPlugin):
    """Detects spam, promotional content, and scams"""

    def __init__(self, link_threshold: int = 3, repetition_threshold: int = 5):
        super().__init__()
        self.link_threshold = link_threshold
        self.repetition_threshold = repetition_threshold

        self.spam_patterns = [
            r"(buy|click|visit|check\s+out|limited\s+time|act\s+now|free\s+money)",
            r"(www\.|https?://|bit\.ly)",
            r"(click\s+here|buy\s+now|order\s+now)",
            r"(\$\d+|\d+\s*USD|\d+\s*EUR)",
        ]

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="spam_validator",
            version="1.0.0",
            description="Detects spam and promotional content",
            author="AutonomAI Team",
            plugin_type="validator"
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        text_lower = output.lower()
        spam_score = 0.0

        # Count links
        links = re.findall(r'https?://\S+|www\.\S+', text_lower)
        if len(links) >= self.link_threshold:
            spam_score += 0.4

        # Check for spam patterns
        pattern_matches = 0
        for pattern in self.spam_patterns:
            if re.search(pattern, text_lower):
                pattern_matches += 1
        spam_score += min(0.5, pattern_matches * 0.15)

        # Check for repetition
        words = text_lower.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.5:  # High repetition
                spam_score += 0.3

        # Check for ALL CAPS
        if len(output) > 10 and output.isupper():
            spam_score += 0.2

        spam_score = min(1.0, spam_score)

        if spam_score >= 0.5:
            return ValidationResult(
                passed=False,
                message=f"Spam detected (score: {spam_score:.2f})",
                metadata={
                    "violation_type": "spam",
                    "severity": spam_score,
                    "confidence": 0.75,
                    "evidence": f"{len(links)} links, {pattern_matches} spam patterns"
                }
            )

        return ValidationResult(passed=True, message="No spam detected")
