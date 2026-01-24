"""
Main Content Moderation Engine

This is the core of the platform, integrating all components:
- AutonomAI self-optimizing system
- Custom validators
- Multi-tenant configuration
- Caching layer
- Learning from human overrides
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src import SelfOptimizingSystem, SystemConfig
from src.core.validator import ValidationPipeline

from config.settings import get_settings, load_tenant_configs
from models.content import Content, ContentType
from models.moderation import (
    ModerationDecision,
    ModerationResult,
    DecisionStatus,
    ModerationAction,
    ViolationType
)
from validators.profanity_validator import ProfanityValidator
from validators.hate_speech_validator import HateSpeechValidator
from validators.spam_validator import SpamValidator
from validators.toxicity_validator import ToxicityValidator

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import json


class ModerationEngine:
    """
    Main content moderation engine

    Features:
    - Multi-tenant isolation
    - AI-powered analysis with DeepSeek
    - Custom validation pipeline
    - Self-learning from human feedback
    - Caching for performance
    - Batch processing support
    """

    def __init__(self, tenant_id: str = "default"):
        self.settings = get_settings()
        self.tenant_id = tenant_id

        # Load tenant configuration
        tenant_configs = load_tenant_configs()
        if tenant_id not in tenant_configs:
            raise ValueError(f"Unknown tenant: {tenant_id}")
        self.tenant_config = tenant_configs[tenant_id]

        # Initialize AutonomAI system
        system_config = SystemConfig(
            main_model=self.settings.deepseek_model,
            main_model_provider="deepseek",
            critic_model=self.settings.deepseek_model,
            critic_model_provider="deepseek",
            enable_auto_optimization=self.tenant_config.enable_auto_learning,
            enable_caching=self.settings.enable_caching,
            cache_ttl=self.settings.cache_ttl,
            cache_strategy=self.settings.cache_strategy,
            enable_distributed_state=self.settings.enable_distributed_state,
            redis_url=self.settings.redis_url,
            instruction_dir=str(self.settings.instruction_dir / tenant_id)
        )

        self.system = SelfOptimizingSystem(system_config)

        # Initialize validators
        self._setup_validators()

        print(f"✓ ModerationEngine initialized for tenant '{tenant_id}' ({self.tenant_config.name})")
        print(f"  Moderation Level: {self.tenant_config.moderation_level}")
        print(f"  Auto-Learning: {self.tenant_config.enable_auto_learning}")
        print(f"  Validators: {', '.join(self.tenant_config.enabled_validators)}")

    def _setup_validators(self):
        """Set up validation pipeline with tenant-specific validators"""

        # Get tenant-specific settings
        allow_mild = self.tenant_config.custom_rules.get("allow_competitive_language", False)

        # Add validators based on tenant configuration
        if "profanity" in self.tenant_config.enabled_validators:
            profanity_validator = ProfanityValidator(
                severity_threshold=0.5,
                allow_mild_profanity=allow_mild
            )
            self.system.validation_pipeline.validators.append(profanity_validator)

        if "hate_speech" in self.tenant_config.enabled_validators:
            hate_validator = HateSpeechValidator(severity_threshold=0.6)
            self.system.validation_pipeline.validators.append(hate_validator)

        if "spam" in self.tenant_config.enabled_validators:
            spam_validator = SpamValidator(link_threshold=3)
            self.system.validation_pipeline.validators.append(spam_validator)

        if "toxicity" in self.tenant_config.enabled_validators:
            toxicity_validator = ToxicityValidator(toxicity_threshold=0.6)
            self.system.validation_pipeline.validators.append(toxicity_validator)

    def moderate_content(
        self,
        content: str,
        content_type: str = "comment",
        author_id: str = "anonymous",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Moderate a single piece of content

        Args:
            content: The text content to moderate
            content_type: Type of content (comment, post, etc.)
            author_id: ID of the content author
            metadata: Additional metadata

        Returns:
            Moderation result with decision and details
        """
        start_time = time.time()

        # Create Content object
        content_obj = Content(
            text=content,
            content_type=ContentType(content_type),
            tenant_id=self.tenant_id,
            author_id=author_id,
            metadata=metadata or {}
        )

        # Build moderation prompt
        prompt = self._build_moderation_prompt(content_obj)

        # Execute with AutonomAI
        result = self.system.execute(prompt)

        # Run validation pipeline
        validation_results = self.system.validation_pipeline.validate(result["output"])

        # Make moderation decision
        decision = self._make_decision(
            content_obj=content_obj,
            ai_output=result["output"],
            validation_results=validation_results,
            cached=result.get("from_cache", False)
        )

        processing_time = (time.time() - start_time) * 1000
        decision.processing_time_ms = processing_time

        return {
            "content_id": content_obj.content_id,
            "decision": decision.status.value,
            "action": decision.action.value,
            "confidence": decision.confidence,
            "violations": [
                {
                    "type": v.violation_type.value,
                    "severity": v.severity,
                    "confidence": v.confidence
                }
                for v in decision.violations
            ],
            "reasoning": decision.reasoning,
            "processing_time_ms": processing_time,
            "from_cache": decision.from_cache
        }

    def _build_moderation_prompt(self, content: Content) -> str:
        """Build the moderation analysis prompt"""

        prompt = f"""Analyze the following {content.content_type.value} for content moderation.

Content: "{content.text}"

Community Standards:
- Moderation Level: {self.tenant_config.moderation_level}
- Allow Competitive Language: {self.tenant_config.custom_rules.get('allow_competitive_language', False)}
- Block External Links: {self.tenant_config.custom_rules.get('block_external_links', False)}

Evaluate for:
1. Profanity and offensive language
2. Hate speech and discrimination
3. Spam or promotional content
4. Toxicity and harassment
5. Overall appropriateness

Provide a brief analysis (2-3 sentences) explaining whether this content should be approved, flagged for review, or rejected."""

        return prompt

    def _make_decision(
        self,
        content_obj: Content,
        ai_output: str,
        validation_results: List[Any],
        cached: bool
    ) -> ModerationDecision:
        """Make final moderation decision based on AI and validator results"""

        decision = ModerationDecision(
            content_id=content_obj.content_id,
            tenant_id=self.tenant_id,
            status=DecisionStatus.APPROVED,
            action=ModerationAction.ALLOW,
            confidence=0.9,
            reasoning=ai_output,
            ai_explanation=ai_output,
            from_cache=cached
        )

        # Analyze validation results
        max_severity = 0.0
        violations_found = []

        for validation_result in validation_results:
            if not validation_result.passed and hasattr(validation_result, 'metadata'):
                metadata = validation_result.metadata
                violation_type = metadata.get("violation_type", "other")
                severity = metadata.get("severity", 0.5)
                confidence = metadata.get("confidence", 0.7)

                # Add violation to decision
                decision.add_violation(
                    violation_type=ViolationType(violation_type),
                    confidence=confidence,
                    severity=severity,
                    evidence=validation_result.message,
                    validator_name=validation_result.metadata.get("validator", "unknown")
                )

                max_severity = max(max_severity, severity)
                violations_found.append(violation_type)

        # Determine final status and action based on severity
        if max_severity >= self.tenant_config.auto_reject_threshold:
            decision.status = DecisionStatus.REJECTED
            decision.action = ModerationAction.REMOVE
            decision.confidence = min(1.0, max_severity + 0.1)
        elif max_severity >= self.tenant_config.require_review_threshold:
            decision.status = DecisionStatus.FLAGGED
            decision.action = ModerationAction.FLAG_FOR_REVIEW
            decision.confidence = 0.7
        else:
            decision.status = DecisionStatus.APPROVED
            decision.action = ModerationAction.ALLOW
            decision.confidence = max(0.8, 1.0 - max_severity)

        return decision

    def moderate_batch(
        self,
        contents: List[Dict[str, Any]],
        batch_size: int = None
    ) -> List[Dict[str, Any]]:
        """Moderate multiple content items efficiently"""

        batch_size = batch_size or self.settings.batch_size
        results = []

        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]

            for content_item in batch:
                result = self.moderate_content(
                    content=content_item.get("text", ""),
                    content_type=content_item.get("type", "comment"),
                    author_id=content_item.get("author_id", "anonymous"),
                    metadata=content_item.get("metadata", {})
                )
                results.append(result)

        return results

    def override_decision(
        self,
        content_id: str,
        new_decision: str,
        moderator_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Override an AI decision with human judgment

        This triggers the learning system to improve future decisions
        """

        # In production, retrieve the original decision from database
        # For this demo, we'll simulate the override

        print(f"\n🔄 Human Override Detected!")
        print(f"  Content ID: {content_id}")
        print(f"  New Decision: {new_decision}")
        print(f"  Moderator: {moderator_id}")
        print(f"  Reason: {reason}")

        # Submit feedback to the learning system
        feedback_message = f"""Human moderator override:
Original AI decision was changed to: {new_decision}
Reason: {reason}

This indicates the AI should learn to {new_decision.lower()} similar content in the future."""

        self.system.submit_feedback(feedback_message)

        print(f"  ✓ Feedback submitted to learning system")
        print(f"  ✓ System will optimize instructions for similar cases")

        return {
            "content_id": content_id,
            "override_applied": True,
            "new_decision": new_decision,
            "learning_triggered": True
        }

    def get_moderation_stats(self, date_range: str = "last_7_days") -> Dict[str, Any]:
        """Get moderation statistics for this tenant"""

        # In production, query from database
        # For demo, return sample stats

        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_config.name,
            "date_range": date_range,
            "total": 1234,
            "approved": 956,
            "rejected": 189,
            "flagged": 89,
            "override_rate": 0.05,  # 5% of decisions overridden
            "approval_rate": 0.77,
            "rejection_rate": 0.15,
            "flagged_rate": 0.07,
            "avg_processing_time_ms": 250,
            "cache_hit_rate": 0.65
        }

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all moderation data for a user (GDPR compliance)"""

        # In production, query database for all user content
        return {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "tenant_id": self.tenant_id,
            "total_content_moderated": 0,
            "decisions": [],
            "note": "Production implementation would include all user data"
        }
