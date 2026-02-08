from typing import Optional, List
from datetime import datetime
import logging

from ..models.config import SystemConfig, FailureLog, FailureEntry
from ..models.version import VersionMetadata, InstructionVersion
from ..storage.version_control import VersionController
from ..storage.distributed_state import DistributedStateManager, DistributedStateConfig
from .golden_dataset import GoldenDataset
from .instruction_file_handler import InstructionFileHandler

logger = logging.getLogger(__name__)


class InstructionManager:
    """Manages instructions.md file and version control with distributed locking"""

    def __init__(
        self, 
        config: SystemConfig,
        state_manager: Optional[DistributedStateManager] = None
    ):
        self.config = config
        self.instructions_path = config.instructions_dir / config.instructions_file
        self.versions_dir = config.instructions_dir / config.versions_dir
        self.pending_review_path = config.instructions_dir / config.pending_review_file
        self.archived_path = config.instructions_dir / config.archived_failures_file

        # Components
        self.file_handler = InstructionFileHandler(config)
        self.version_controller = VersionController(self.versions_dir, config)

        # Distributed state manager for multi-instance coordination
        self.state_manager = state_manager
        if self.state_manager is None and hasattr(config, 'enable_distributed_state') and config.enable_distributed_state:
            # Create state manager if enabled in config
            state_config = DistributedStateConfig()
            self.state_manager = DistributedStateManager(state_config)

        # Phase 3: Golden Dataset for regression testing
        self.golden_dataset = None
        if self.config.enable_regression_testing:
            golden_path = self.config.instructions_dir / self.config.golden_dataset_file
            self.golden_dataset = GoldenDataset(
                golden_path, max_size=self.config.golden_dataset_max_size
            )

        # State
        self.base_instructions: str = ""
        self.dynamic_appendix: str = ""
        self.failure_log: FailureLog = FailureLog(max_size=config.max_failure_log_size)
        self.current_version: Optional[str] = None
        self.optimization_cycle_count: int = 0

        # Initialize
        self._initialize()

    def _initialize(self):
        """Load or create instructions file"""
        if self.file_handler.file_exists():
            self._load_from_file()
        else:
            self._create_default()

    def _create_default(self):
        """Create default instructions.md"""
        self.base_instructions = """# Base Instructions (Immutable)

These are the core, permanent rules that guide the model's behavior.

1. Be professional and respectful in all interactions
2. Provide accurate, well-researched information
3. Admit uncertainty when you don't know something
4. Follow ethical guidelines and refuse harmful requests
5. Structure responses clearly and logically
"""

        self.dynamic_appendix = """# Dynamic Appendix (Self-Optimizing)

This section evolves based on performance feedback.

*No custom rules yet. The system will learn from failures.*
"""

        self.failure_log = FailureLog(max_size=self.config.max_failure_log_size)

        self._save_to_file()
        self._create_version("initial", "System initialization")

    def _load_from_file(self):
        """Load instructions from file"""
        base, appendix = self.file_handler.load_from_file()

        if base is None:
            self._create_default()
            return

        self.base_instructions = base
        self.dynamic_appendix = appendix

        # Get current version
        self.current_version = self.version_controller.get_latest_version_id()

    def _save_to_file(self):
        """Save current state to instructions.md"""
        self.file_handler.save_to_file(
            self.base_instructions,
            self.dynamic_appendix,
            self.failure_log,
            self.current_version,
        )

    def get_full_instructions(self) -> str:
        """Get combined instructions for Main Model"""
        return f"{self.base_instructions}\n\n{self.dynamic_appendix}"

    def add_failure(self, failure: FailureEntry):
        """Add a failure to the log with distributed locking"""
        if self.state_manager:
            try:
                with self.state_manager.lock("failure_log", timeout=10):
                    self.failure_log.add(failure)
                    self._save_to_file()
            except Exception as e:
                logger.error(f"Error acquiring lock for failure logging: {e}")
                # Fallback to non-locked add
                self.failure_log.add(failure)
                self._save_to_file()
        else:
            self.failure_log.add(failure)
            self._save_to_file()

    def get_failure_history(self, limit: int = 50) -> List[FailureEntry]:
        """Get recent failure history"""
        return self.failure_log.get_recent(limit)

    def update_appendix(
        self,
        new_appendix: str,
        metadata: VersionMetadata,
        rules_to_deprecate: Optional[List[str]] = None,
    ) -> bool:
        """Update the dynamic appendix with version control and distributed locking"""

        # Acquire distributed lock for instruction updates
        if self.state_manager:
            try:
                with self.state_manager.lock("instruction_update", timeout=30):
                    return self._update_appendix_locked(new_appendix, metadata, rules_to_deprecate)
            except Exception as e:
                logger.error(f"Error acquiring lock for instruction update: {e}")
                # Fallback to non-locked update in case of lock failure
                return self._update_appendix_locked(new_appendix, metadata, rules_to_deprecate)
        else:
            return self._update_appendix_locked(new_appendix, metadata, rules_to_deprecate)
    
    def _update_appendix_locked(
        self,
        new_appendix: str,
        metadata: VersionMetadata,
        rules_to_deprecate: Optional[List[str]] = None,
    ) -> bool:
        """Internal method for updating appendix (called within lock)"""

        # Update appendix
        old_appendix = self.dynamic_appendix
        self.dynamic_appendix = new_appendix

        # Create version
        version_created = self._create_version(
            metadata.trigger_type, metadata.critic_justification, metadata
        )

        if not version_created:
            # Rollback on failure
            self.dynamic_appendix = old_appendix
            return False

        # Save
        self._save_to_file()
        self.optimization_cycle_count += 1

        return True

    def _create_version(
        self,
        trigger_type: str,
        justification: str,
        metadata: Optional[VersionMetadata] = None,
    ) -> bool:
        """Create a new version snapshot with distributed locking"""

        # Acquire lock for version creation to prevent race conditions
        if self.state_manager:
            try:
                with self.state_manager.lock("version_create", timeout=30):
                    return self._create_version_locked(trigger_type, justification, metadata)
            except Exception as e:
                logger.error(f"Error acquiring lock for version creation: {e}")
                return self._create_version_locked(trigger_type, justification, metadata)
        else:
            return self._create_version_locked(trigger_type, justification, metadata)
    
    def _create_version_locked(
        self,
        trigger_type: str,
        justification: str,
        metadata: Optional[VersionMetadata] = None,
    ) -> bool:
        """Internal method for creating version (called within lock)"""

        if metadata is None:
            metadata = VersionMetadata(
                trigger_type=trigger_type,
                critic_justification=justification,
                diff_summary="Initial version",
                parent_version=self.current_version,
            )
        else:
            metadata.parent_version = self.current_version

        version = InstructionVersion(
            metadata=metadata,
            base_instructions=self.base_instructions,
            dynamic_appendix=self.dynamic_appendix,
        )

        success = self.version_controller.create_version(version)

        if success:
            self.current_version = version.metadata.version_id

        return success

    def rollback(self, steps: int = 1) -> bool:
        """Rollback N versions"""
        target_version = self.version_controller.get_version_n_steps_back(steps)

        if target_version:
            return self.rollback_to_version(target_version.metadata.version_id)

        return False

    def rollback_to_version(self, version_id: str) -> bool:
        """Rollback to specific version"""
        version = self.version_controller.load_version(version_id)

        if version:
            self.base_instructions = version.base_instructions
            self.dynamic_appendix = version.dynamic_appendix
            self.current_version = version_id
            self._save_to_file()
            return True

        return False

    def add_to_pending_review(self, failure: FailureEntry, reason: str):
        """Add failed optimization to pending review"""
        content = f"""# Pending Manual Review

Added: {datetime.now().isoformat()}
Reason: {reason}

{failure.to_markdown(detail_level="full")}

---

"""

        self.file_handler.save_pending_review(content)
