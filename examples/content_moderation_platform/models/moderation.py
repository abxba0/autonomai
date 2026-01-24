"""
Moderation decision models
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class DecisionStatus(str, Enum):
    """Status of moderation decision"""
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"  # Requires human review
    PENDING = "pending"
    OVERRIDDEN = "overridden"


class ModerationAction(str, Enum):
    """Actions that can be taken"""
    ALLOW = "allow"
    REMOVE = "remove"
    SHADOW_BAN = "shadow_ban"
    FLAG_FOR_REVIEW = "flag_for_review"
    WARN_USER = "warn_user"
    SUSPEND_USER = "suspend_user"
    BAN_USER = "ban_user"


class ViolationType(str, Enum):
    """Types of violations"""
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    SPAM = "spam"
    HARASSMENT = "harassment"
    SEXUAL_CONTENT = "sexual_content"
    VIOLENCE = "violence"
    MISINFORMATION = "misinformation"
    SCAM = "scam"
    SELF_HARM = "self_harm"
    ILLEGAL_CONTENT = "illegal_content"
    TOXICITY = "toxicity"
    OTHER = "other"


class ViolationDetail(BaseModel):
    """Details about a specific violation"""
    violation_type: ViolationType
    confidence: float = Field(ge=0.0, le=1.0)
    severity: float = Field(ge=0.0, le=1.0)
    evidence: str  # What triggered this violation
    validator_name: str


class ModerationDecision(BaseModel):
    """AI moderation decision"""

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str
    tenant_id: str

    # Decision
    status: DecisionStatus
    action: ModerationAction
    confidence: float = Field(ge=0.0, le=1.0)

    # Violations
    violations: List[ViolationDetail] = Field(default_factory=list)
    primary_violation: Optional[ViolationType] = None

    # Reasoning
    reasoning: str
    ai_explanation: Optional[str] = None

    # Metadata
    model_used: str = "deepseek-chat"
    processing_time_ms: float = 0.0
    from_cache: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Human Override
    overridden: bool = False
    override_by: Optional[str] = None
    override_at: Optional[datetime] = None
    override_reason: Optional[str] = None
    original_status: Optional[DecisionStatus] = None

    def add_violation(
        self,
        violation_type: ViolationType,
        confidence: float,
        severity: float,
        evidence: str,
        validator_name: str
    ):
        """Add a violation to this decision"""
        violation = ViolationDetail(
            violation_type=violation_type,
            confidence=confidence,
            severity=severity,
            evidence=evidence,
            validator_name=validator_name
        )
        self.violations.append(violation)

        # Update primary violation if this is more severe
        if not self.primary_violation or severity > self._get_primary_severity():
            self.primary_violation = violation_type

    def _get_primary_severity(self) -> float:
        """Get severity of current primary violation"""
        for v in self.violations:
            if v.violation_type == self.primary_violation:
                return v.severity
        return 0.0

    def override(
        self,
        new_status: DecisionStatus,
        new_action: ModerationAction,
        moderator_id: str,
        reason: str
    ):
        """Override the AI decision"""
        self.original_status = self.status
        self.status = new_status
        self.action = new_action
        self.overridden = True
        self.override_by = moderator_id
        self.override_at = datetime.utcnow()
        self.override_reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "decision_id": self.decision_id,
            "content_id": self.content_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "action": self.action.value,
            "confidence": self.confidence,
            "violations": [
                {
                    "type": v.violation_type.value,
                    "confidence": v.confidence,
                    "severity": v.severity,
                    "evidence": v.evidence,
                    "validator": v.validator_name
                }
                for v in self.violations
            ],
            "primary_violation": self.primary_violation.value if self.primary_violation else None,
            "reasoning": self.reasoning,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
            "from_cache": self.from_cache,
            "created_at": self.created_at.isoformat(),
            "overridden": self.overridden,
            "override_by": self.override_by,
            "override_at": self.override_at.isoformat() if self.override_at else None,
            "override_reason": self.override_reason
        }

    class Config:
        use_enum_values = True


class ModerationResult(BaseModel):
    """Complete moderation result including content and decision"""

    content_id: str
    tenant_id: str
    text: str  # The moderated text
    decision: ModerationDecision
    cached: bool = False

    # Analytics
    similar_content_count: int = 0
    historical_override_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_id": self.content_id,
            "tenant_id": self.tenant_id,
            "text": self.text,
            "decision": self.decision.to_dict(),
            "cached": self.cached,
            "similar_content_count": self.similar_content_count,
            "historical_override_rate": self.historical_override_rate
        }
