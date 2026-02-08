"""
System status reporting for SelfOptimizingSystem.

Provides status information, version history, and system health checks.
"""

from typing import Dict, Any, List, Optional

from .models.config import FailureEntry


class SystemStatus:
    """Provides system status and version information.

    Aggregates status from instruction manager, validation pipeline,
    and configuration.
    """

    def __init__(self, config, instruction_manager, validation_pipeline):
        self.config = config
        self.instruction_manager = instruction_manager
        self.validation_pipeline = validation_pipeline

    def get_status(self) -> Dict[str, Any]:
        """Get system status information."""
        versions = self.get_version_history()
        return {
            "system": "Self-Optimizing Instruction Library",
            "status": "operational",
            "config": {
                "main_model": self.config.main_model,
                "critic_model": self.config.critic_model,
                "enable_auto_optimization": self.config.enable_auto_optimization,
                "enable_correction_detection": self.config.enable_correction_detection,
            },
            "versions": {
                "total": len(versions),
                "latest": versions[-1]["version_id"] if versions else None,
            },
            "validation": {
                "validators_count": len(self.validation_pipeline.validators),
            },
        }

    def get_version_history(self):
        """Get version history."""
        return self.instruction_manager.version_controller.get_version_history()

    def get_current_instructions(self) -> str:
        """Get current instructions."""
        return self.instruction_manager.get_full_instructions()

    def get_failure_history(self, limit: int = 50) -> List[FailureEntry]:
        """Get recent failure history."""
        return []

    def rollback(self, steps: int = 1) -> bool:
        """Rollback N versions."""
        return self.instruction_manager.rollback(steps)

    def rollback_to_version(self, version_id: str) -> bool:
        """Rollback to specific version."""
        return self.instruction_manager.rollback_to_version(version_id)
