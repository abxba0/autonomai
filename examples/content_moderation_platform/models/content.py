"""
Content models for moderation platform
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import hashlib
import uuid


class ContentType(str, Enum):
    """Types of content that can be moderated"""
    COMMENT = "comment"
    POST = "post"
    MESSAGE = "message"
    REVIEW = "review"
    BIO = "bio"
    USERNAME = "username"
    LISTING = "listing"
    IMAGE_TEXT = "image_text"  # OCR extracted text


class Content(BaseModel):
    """Content to be moderated"""

    # Identification
    content_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    author_id: str
    parent_id: Optional[str] = None  # For replies/comments

    # Content
    text: str
    content_type: ContentType = ContentType.COMMENT
    language: str = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context for AI
    author_reputation: Optional[float] = None  # 0.0 - 1.0
    author_history_violations: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Processing
    processed: bool = False
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    def get_content_hash(self) -> str:
        """Generate hash of content for de-duplication"""
        content_str = f"{self.text}{self.content_type}{self.author_id}"
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content_id": self.content_id,
            "tenant_id": self.tenant_id,
            "author_id": self.author_id,
            "parent_id": self.parent_id,
            "text": self.text,
            "content_type": self.content_type.value,
            "language": self.language,
            "metadata": self.metadata,
            "context": self.context,
            "author_reputation": self.author_reputation,
            "author_history_violations": self.author_history_violations,
            "created_at": self.created_at.isoformat(),
            "submitted_at": self.submitted_at.isoformat(),
        }

    class Config:
        use_enum_values = True
