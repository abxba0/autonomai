from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class VersionMetadata:
    """Metadata for a single version"""

    trigger_type: str  # "auto_validation" | "human_feedback" | "consolidation"
    critic_justification: str
    diff_summary: str
    version_id: str = field(
        default_factory=lambda: f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_signature: Optional[str] = None
    rules_added: int = 0
    rules_modified: int = 0
    rules_deprecated: int = 0
    parent_version: Optional[str] = None
    user_approved: bool = False
    approval_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp,
            "trigger_type": self.trigger_type,
            "failure_signature": self.failure_signature,
            "critic_justification": self.critic_justification,
            "diff_summary": self.diff_summary,
            "rules_added": self.rules_added,
            "rules_modified": self.rules_modified,
            "rules_deprecated": self.rules_deprecated,
            "parent_version": self.parent_version,
            "user_approved": self.user_approved,
            "approval_notes": self.approval_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionMetadata":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class InstructionVersion:
    """Complete snapshot of instructions at a point in time"""

    metadata: VersionMetadata
    base_instructions: str
    dynamic_appendix: str

    def to_markdown(self) -> str:
        """Convert to markdown file format"""
        md = f"# Version {self.metadata.version_id}\n\n"
        md += f"**Timestamp**: {self.metadata.timestamp}\n"
        md += f"**Trigger**: {self.metadata.trigger_type}\n"
        md += f"**Changes**: {self.metadata.diff_summary}\n\n"
        md += "---\n\n"
        md += "## Base Instructions\n\n"
        md += self.base_instructions + "\n\n"
        md += "## Dynamic Appendix\n\n"
        md += self.dynamic_appendix + "\n"
        return md
