"""
Workflow Instruction Manager

Manages separate instruction files for Planner and Actor roles
with independent version control.
"""

from typing import Optional
from pathlib import Path

from ...models.config import SystemConfig
from ...storage.markdown_handler import MarkdownHandler
from ...storage.version_control import VersionController


class WorkflowInstructionManager:
    """
    Manages separate instruction files for Planner and Actor roles
    with independent version control
    """

    def __init__(self, config: SystemConfig, instructions_dir: Path):
        self.config = config
        self.instructions_dir = instructions_dir
        self.md_handler = MarkdownHandler()

        # Paths for role-specific instruction files
        self.planner_path = instructions_dir / "planner.md"
        self.actor_path = instructions_dir / "actor.md"

        # Version controllers for each role
        planner_versions_dir = instructions_dir / ".versions_planner"
        actor_versions_dir = instructions_dir / ".versions_actor"

        self.planner_version_controller = VersionController(
            planner_versions_dir, config
        )
        self.actor_version_controller = VersionController(actor_versions_dir, config)

        # Current versions
        self.current_planner_version: Optional[str] = None
        self.current_actor_version: Optional[str] = None

        # Initialize instruction files
        self._initialize_instructions()

    def _initialize_instructions(self):
        """Initialize instruction files if they don't exist"""
        if not self.planner_path.exists():
            self._create_default_planner()

        if not self.actor_path.exists():
            self._create_default_actor()

        # Create initial versions
        if self.current_planner_version is None:
            self.current_planner_version = self._create_planner_version(
                "initialization",
                "Initial planner instructions"
            )

        if self.current_actor_version is None:
            self.current_actor_version = self._create_actor_version(
                "initialization",
                "Initial actor instructions"
            )

    def _create_default_planner(self):
        """Create default planner instructions if file doesn't exist"""
        # The file should already be created, but provide a fallback
        default_content = """# Planner Instructions

Generate workflow plans as JSON with steps, dependencies, and clear descriptions.
"""
        self.planner_path.parent.mkdir(parents=True, exist_ok=True)
        self.md_handler.write_file(self.planner_path, default_content)

    def _create_default_actor(self):
        """Create default actor instructions if file doesn't exist"""
        # The file should already be created, but provide a fallback
        default_content = """# Actor Instructions

Execute workflow steps precisely according to their descriptions.
"""
        self.actor_path.parent.mkdir(parents=True, exist_ok=True)
        self.md_handler.write_file(self.actor_path, default_content)

    def get_planner_instructions(self) -> str:
        """Get current planner instructions"""
        return self.md_handler.read_file(self.planner_path)

    def get_actor_instructions(self) -> str:
        """Get current actor instructions"""
        return self.md_handler.read_file(self.actor_path)

    def _create_planner_version(self, trigger_type: str, diff_summary: str) -> str:
        """Create a version for planner instructions"""
        from ...models.version import VersionMetadata, InstructionVersion
        
        metadata = VersionMetadata(
            trigger_type=trigger_type,
            critic_justification=diff_summary,
            diff_summary=diff_summary,
            parent_version=self.current_planner_version,
        )
        
        version = InstructionVersion(
            metadata=metadata,
            base_instructions=self.get_planner_instructions(),
            dynamic_appendix="",
        )
        
        success = self.planner_version_controller.create_version(version)
        if success:
            return version.metadata.version_id
        return None

    def _create_actor_version(self, trigger_type: str, diff_summary: str) -> str:
        """Create a version for actor instructions"""
        from ...models.version import VersionMetadata, InstructionVersion
        
        metadata = VersionMetadata(
            trigger_type=trigger_type,
            critic_justification=diff_summary,
            diff_summary=diff_summary,
            parent_version=self.current_actor_version,
        )
        
        version = InstructionVersion(
            metadata=metadata,
            base_instructions=self.get_actor_instructions(),
            dynamic_appendix="",
        )
        
        success = self.actor_version_controller.create_version(version)
        if success:
            return version.metadata.version_id
        return None

    def update_planner_instructions(
        self, new_content: str, trigger_type: str, diff_summary: str
    ) -> str:
        """Update planner instructions and create version"""
        self.md_handler.write_file(self.planner_path, new_content)
        self.current_planner_version = self._create_planner_version(
            trigger_type=trigger_type,
            diff_summary=diff_summary,
        )
        return self.current_planner_version

    def update_actor_instructions(
        self, new_content: str, trigger_type: str, diff_summary: str
    ) -> str:
        """Update actor instructions and create version"""
        self.md_handler.write_file(self.actor_path, new_content)
        self.current_actor_version = self._create_actor_version(
            trigger_type=trigger_type,
            diff_summary=diff_summary,
        )
        return self.current_actor_version

    def rollback_planner(self, steps: int = 1) -> bool:
        """Rollback planner instructions"""
        content = self.planner_version_controller.rollback(steps)
        if content:
            self.md_handler.write_file(self.planner_path, content)
            return True
        return False

    def rollback_actor(self, steps: int = 1) -> bool:
        """Rollback actor instructions"""
        content = self.actor_version_controller.rollback(steps)
        if content:
            self.md_handler.write_file(self.actor_path, content)
            return True
        return False


def swap_instructions_temporarily(base_instruction_manager, new_instructions: str, restore_callback):
    """
    Helper function to temporarily swap instructions and restore them after execution
    
    Args:
        base_instruction_manager: The InstructionManager to swap instructions on
        new_instructions: The new instructions to use temporarily
        restore_callback: Function to call after restoration (receives restored instructions)
    """
    # Save original instructions
    original_instructions = base_instruction_manager.get_full_instructions()
    
    # Apply new instructions
    base_instruction_manager.base_instructions = new_instructions
    base_instruction_manager.dynamic_appendix = ""
    
    # Execute callback
    result = restore_callback()
    
    # Restore original instructions
    if "# Dynamic Appendix" in original_instructions:
        parts = original_instructions.split("# Dynamic Appendix")
        base_instruction_manager.base_instructions = parts[0].strip()
        base_instruction_manager.dynamic_appendix = "# Dynamic Appendix" + parts[1]
    else:
        base_instruction_manager.base_instructions = original_instructions
        base_instruction_manager.dynamic_appendix = ""
    
    return result
