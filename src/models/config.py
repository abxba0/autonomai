from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import hashlib
import json


@dataclass
class SystemConfig:
    """Main configuration for the self-optimizing system"""

    # File Paths
    instructions_dir: Path = Path("instructions")
    instructions_file: str = "instructions.md"
    versions_dir: str = ".versions"
    pending_review_file: str = "pending_review.md"
    archived_failures_file: str = "archived_failures.md"

    # Model Configuration
    main_model: str = "claude-3-5-sonnet-20241022"
    critic_model: str = "claude-3-haiku-20240307"
    temperature_main: float = 0.7
    temperature_critic: float = 0.3

    # Provider Configuration
    # Supported providers: "anthropic", "openai", "google", "deepseek", "openrouter"
    # If not specified, will auto-detect from model name
    main_model_provider: Optional[str] = None
    critic_model_provider: Optional[str] = None

    # Failure Log Management
    max_failure_log_size: int = 50
    recent_failures_full_detail: int = 10
    compressed_failures_range: tuple = (11, 30)
    distilled_failures_range: tuple = (31, 50)

    # Optimization Controls
    max_optimization_attempts: int = 3
    retry_cooldown_seconds: int = 300
    enable_auto_optimization: bool = True

    # Circuit Breaker
    circuit_breaker_threshold: int = 3
    circuit_breaker_window: int = 10
    circuit_breaker_cooldown: int = 3600  # 1 hour

    # Consolidation
    auto_consolidate_at_lines: int = 100
    auto_consolidate_every_n_cycles: int = 50
    require_user_approval_for_consolidation: bool = True

    # Token Management
    critic_max_context_tokens: int = 8000
    base_prompt_tokens: int = 2000
    semantic_similarity_threshold: float = 0.7
    use_semantic_filtering: bool = True

    # Semantic De-duplication (Phase 1)
    enable_semantic_deduplication: bool = True
    rule_similarity_threshold: float = 0.8  # Higher threshold for rules than failures

    # Version Control
    max_versions_to_keep: int = 100
    create_version_on_every_change: bool = True

    # Validation
    enable_auto_validation: bool = True
    validation_timeout_seconds: int = 30

    # Implicit Feedback / Correction Detection
    enable_correction_detection: bool = True
    correction_detection_confidence_threshold: float = 0.7

    # Consensus Critic / Judge Pattern (Phase 2)
    enable_judge_model: bool = True
    judge_approval_required: bool = (
        True  # Require judge approval before applying changes
    )

    # Confidence-Based Throttling (Phase 4)
    enable_confidence_throttling: bool = True
    confidence_threshold: float = 0.7  # Minimum confidence to auto-apply changes

    # Automated Regression Testing / Golden Suite (Phase 3)
    enable_regression_testing: bool = True
    golden_dataset_file: str = "golden_dataset.json"
    golden_dataset_max_size: int = 100
    regression_test_sample_size: int = 10  # Number of tests to run on each update
    regression_pass_threshold: float = 0.9  # Minimum pass rate to apply changes

    # Multi-Modal Optimization (Phase 5)
    enable_multimodal: bool = False
    supported_modalities: List[str] = field(
        default_factory=lambda: ["text", "vision", "audio"]
    )
    vision_model: Optional[str] = None  # Specific model for vision tasks
    audio_model: Optional[str] = None  # Specific model for audio tasks
    multimodal_validation_timeout: int = 60  # Longer timeout for multi-modal

    # Knowledge Graph for Rules (Phase 6)
    enable_knowledge_graph: bool = False
    rule_graph_file: str = "rule_graph.json"
    enable_rule_inheritance: bool = True
    enable_rule_supersession: bool = True
    max_rule_depth: int = 5  # Maximum depth for rule hierarchy

    # Multi-Tenant Isolation (Phase 7)
    enable_multi_tenant: bool = False
    default_tenant_id: str = "default"
    tenant_isolation_strict: bool = True  # Strict isolation vs. shared base rules

    # Distributed System Settings (Production)
    enable_distributed_state: bool = False
    redis_state_url: str = "redis://localhost:6379/2"
    distributed_lock_timeout: int = 30

    # Caching & Performance Layer (Production)
    enable_caching: bool = True
    cache_redis_url: str = "redis://localhost:6379"
    cache_redis_db: int = 0
    cache_redis_password: Optional[str] = None
    cache_default_ttl: int = 3600  # 1 hour default TTL in seconds
    cache_strategy: str = "ttl"  # ttl, lru, lfu, manual
    cache_llm_responses: bool = True
    cache_embeddings: bool = True
    cache_include_context_in_key: bool = False  # Include conversation context in cache key
    cache_max_memory_mb: int = 512


@dataclass
class OptimizationAttempt:
    """Tracks a single optimization attempt"""

    attempt_number: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    critic_response: Optional[Any] = None  # Will be defined in critic_response.py


@dataclass
class FailureEntry:
    """Represents a single failure in the log"""

    trigger_type: Literal["auto_validation", "human_feedback", "implicit_feedback"]
    failure_description: str
    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    severity: Literal["minor", "moderate", "critical"] = "moderate"

    # Failure Details
    user_feedback: Optional[str] = None
    last_model_output: Optional[str] = None
    validation_errors: Optional[Dict[str, Any]] = None

    # Context
    user_query: Optional[str] = None
    conversation_context: Optional[str] = None

    # Multi-Modal Support (Phase 5)
    modality: str = "text"  # text, vision, audio, multi-modal
    vision_input_refs: List[str] = field(default_factory=list)  # File paths or URLs
    audio_input_refs: List[str] = field(default_factory=list)  # File paths or URLs
    vision_validation_errors: Optional[Dict[str, Any]] = None
    audio_validation_errors: Optional[Dict[str, Any]] = None

    # Multi-Tenant Support (Phase 7)
    tenant_id: str = "default"

    # Resolution Tracking
    optimization_attempted: bool = False
    optimization_successful: bool = False
    resolution_notes: Optional[str] = None
    affected_appendix_rules: List[str] = field(default_factory=list)

    # For Circuit Breaker
    failure_signature: str = field(init=False)

    def __post_init__(self):
        """Generate unique signature for pattern detection"""
        signature_data = {
            "trigger_type": self.trigger_type,
            "description": self.failure_description[:100],  # First 100 chars
            "validation_errors": str(self.validation_errors),
        }
        signature_str = json.dumps(signature_data, sort_keys=True)
        self.failure_signature = hashlib.md5(signature_str.encode()).hexdigest()[:12]

    def to_markdown(
        self, detail_level: Literal["full", "compressed", "distilled"] = "full"
    ) -> str:
        """Convert to markdown format for storage"""
        if detail_level == "distilled":
            return f"- [{self.severity.upper()}] {self.timestamp}: {self.failure_description[:80]}..."

        md = f"### Failure #{self.id} [{self.trigger_type.upper()}] - {self.timestamp} - Severity: {self.severity.upper()}\n"
        md += f"**Signature**: `{self.failure_signature}`\n"

        if self.trigger_type == "human_feedback" and self.user_feedback:
            md += f"**User Feedback**: {self.user_feedback}\n"

        md += f"**Description**: {self.failure_description}\n"

        if detail_level == "full":
            if self.validation_errors:
                md += f"**Validation Errors**: {json.dumps(self.validation_errors, indent=2)}\n"
            if self.last_model_output:
                # Handle case where last_model_output might be None or empty
                truncated = self.last_model_output[:500] + (
                    "..." if len(self.last_model_output) > 500 else ""
                )
                md += f"**Last Output**: \n```\n{truncated}\n```\n"
            if self.user_query:
                md += f"**User Query**: {self.user_query}\n"

        if self.resolution_notes:
            md += f"**Resolution**: {self.resolution_notes}\n"

        md += "\n---\n\n"
        return md

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureEntry":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class FailureLog:
    """Manages the collection of failures"""

    entries: List[FailureEntry] = field(default_factory=list)
    max_size: int = 50

    def add(self, failure: FailureEntry):
        """Add a failure, maintaining max size"""
        self.entries.append(failure)

        # Archive if exceeded
        if len(self.entries) > self.max_size:
            self._archive_oldest()

    def _archive_oldest(self):
        """Move oldest entries to archive file"""
        # This will be implemented in InstructionManager
        pass

    def get_recent(self, n: int = 10) -> List[FailureEntry]:
        """Get N most recent failures"""
        return self.entries[-n:] if len(self.entries) >= n else self.entries

    def count_similar(self, failure: FailureEntry, window: int = 10) -> int:
        """Count failures with same signature in recent window"""
        recent = self.get_recent(window)
        return sum(
            1 for f in recent if f.failure_signature == failure.failure_signature
        )

    def to_markdown(self, config: SystemConfig) -> str:
        """Convert entire log to markdown with tiered compression"""
        md = "## Failure Log\n\n"

        total = len(self.entries)

        # Recent failures - full detail
        recent_count = min(config.recent_failures_full_detail, total)
        recent = self.entries[-recent_count:]
        if recent:
            md += "### Recent Failures (Full Detail)\n\n"
            for f in recent:
                md += f.to_markdown(detail_level="full")

        # Compressed range
        compressed_start = max(0, total - config.compressed_failures_range[1])
        compressed_end = max(0, total - config.compressed_failures_range[0])
        compressed = self.entries[compressed_start:compressed_end]
        if compressed:
            md += "### Historical Failures (Compressed)\n\n"
            for f in compressed:
                md += f.to_markdown(detail_level="compressed")

        # Distilled range
        distilled_start = max(0, total - config.distilled_failures_range[1])
        distilled_end = max(0, total - config.distilled_failures_range[0])
        distilled = self.entries[distilled_start:distilled_end]
        if distilled:
            md += "### Older Failures (Distilled)\n\n"
            for f in distilled:
                md += f.to_markdown(detail_level="distilled")

        return md
