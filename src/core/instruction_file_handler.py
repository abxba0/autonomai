"""
File I/O and Markdown operations for instruction management.

Handles reading, writing, and formatting instruction files, including
base instructions, dynamic appendix, failure logs, and version history.
"""

from datetime import datetime
from typing import Optional
from pathlib import Path

from ..models.config import SystemConfig, FailureLog
from ..storage.markdown_handler import MarkdownHandler


class InstructionFileHandler:
    """Handles file I/O and Markdown operations for instruction management."""

    def __init__(self, config: SystemConfig, md_handler: Optional[MarkdownHandler] = None):
        """Initialize the file handler.

        Args:
            config: System configuration with instruction paths.
            md_handler: Optional MarkdownHandler for dependency injection (primarily for testing).
        """
        self.config = config
        self.instructions_path = config.instructions_dir / config.instructions_file
        self.pending_review_path = config.instructions_dir / config.pending_review_file
        self.md_handler = md_handler or MarkdownHandler()

    def load_from_file(self):
        """Load instructions from file.

        Returns:
            Tuple of (base_instructions, dynamic_appendix) or (None, None)
            if the file does not exist or is empty.
        """
        content = self.md_handler.read_file(self.instructions_path)

        if not content:
            return None, None

        # Simple parsing - look for sections
        sections = content.split("\n---\n")

        if len(sections) >= 2:
            return sections[0].strip(), sections[1].strip()

        return None, None

    def save_to_file(
        self,
        base_instructions: str,
        dynamic_appendix: str,
        failure_log: FailureLog,
        current_version: Optional[str],
    ):
        """Save current state to instructions.md.

        Args:
            base_instructions: The immutable base instructions.
            dynamic_appendix: The self-optimizing dynamic appendix.
            failure_log: The failure log to serialize.
            current_version: Current version ID.
        """
        content = f"""# System Instructions

Generated: {datetime.now().isoformat()}
Current Version: {current_version or "N/A"}

---

{base_instructions}

---

{dynamic_appendix}

---

{failure_log.to_markdown(self.config)}

---

## Version History

See `.versions/` directory for full history.
Latest version: {current_version or "initial"}

"""

        self.md_handler.write_file(self.instructions_path, content)

    def file_exists(self) -> bool:
        """Check if the instructions file exists."""
        return self.instructions_path.exists()

    def save_pending_review(self, content: str):
        """Save content to pending review file.

        Args:
            content: The formatted review content to prepend to file.
        """
        existing = ""
        if self.pending_review_path.exists():
            existing = self.md_handler.read_file(self.pending_review_path)

        self.md_handler.write_file(self.pending_review_path, content + existing)
