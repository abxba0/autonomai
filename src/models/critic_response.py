from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class CriticResponse:
    """Structured output from Critic model"""

    # Analysis Phase
    impact_analysis: str
    conflict_analysis: str
    safety_declaration: bool
    safety_reasoning: str
    change_type: str
    proposed_appendix_update: str
    affected_rules: List[str] = field(default_factory=list)
    rules_to_deprecate: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    requires_human_review: bool = False

    def __post_init__(self):
        """Validate the response meets all requirements"""
        if not self.safety_declaration:
            raise ValueError(
                "Safety declaration must be True - Critic must explicitly confirm safety"
            )

        if len(self.impact_analysis) < 50:
            raise ValueError("Impact analysis too brief (minimum 50 characters)")

        if len(self.safety_reasoning) < 30:
            raise ValueError("Safety reasoning insufficient (minimum 30 characters)")

        if not self.proposed_appendix_update.strip():
            raise ValueError("No proposed update provided")

        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

    def is_valid(self) -> tuple[bool, Optional[str]]:
        """Validate the response meets all requirements"""
        try:
            self.__post_init__()
            return True, None
        except ValueError as e:
            return False, str(e)
