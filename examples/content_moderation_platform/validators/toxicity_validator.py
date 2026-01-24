"""Toxicity detection validator"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from src.plugins.base import ValidatorPlugin, PluginMetadata
from src.core.validator import ValidationResult
from typing import Dict, Any


class ToxicityValidator(ValidatorPlugin):
    """Detects overall toxic behavior - combines multiple signals"""

    def __init__(self, toxicity_threshold: float = 0.6):
        super().__init__()
        self.toxicity_threshold = toxicity_threshold

        self.toxic_indicators = {
            "aggressive": ["attack", "destroy", "idiotic", "stupid", "moron"],
            "dismissive": ["whatever", "nobody cares", "shut up", "go away"],
            "insulting": ["loser", "pathetic", "worthless", "trash"],
        }

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="toxicity_validator",
            version="1.0.0",
            description="Detects toxic and hostile behavior",
            author="AutonomAI Team",
            plugin_type="validator"
        )

    def validate(self, output: str, context: Dict[str, Any] = None) -> ValidationResult:
        text_lower = output.lower()
        toxicity_score = 0.0
        matches = []

        for category, terms in self.toxic_indicators.items():
            for term in terms:
                if term in text_lower:
                    matches.append(f"{category}:{term}")
                    toxicity_score += 0.15

        # Check for excessive punctuation (!!! ???)
        if output.count('!') > 3 or output.count('?') > 3:
            toxicity_score += 0.1

        toxicity_score = min(1.0, toxicity_score)

        if toxicity_score >= self.toxicity_threshold:
            return ValidationResult(
                passed=False,
                message=f"Toxic content detected (score: {toxicity_score:.2f})",
                metadata={
                    "violation_type": "toxicity",
                    "severity": toxicity_score,
                    "confidence": 0.70,
                    "evidence": f"Found {len(matches)} toxic indicators"
                }
            )

        return ValidationResult(passed=True, message="No toxicity detected")
