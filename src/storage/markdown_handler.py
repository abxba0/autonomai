from pathlib import Path
from typing import Dict
import re

from ..models.config import SystemConfig, FailureLog, FailureEntry


class MarkdownHandler:
    """Handles reading and writing markdown files"""

    def read_file(self, filepath: Path) -> str:
        """Read content from a markdown file"""
        if not filepath.exists():
            return ""

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, filepath: Path, content: str):
        """Write content to a markdown file"""
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections"""
        sections = {}

        # Split by major headers
        pattern = r"^#+\s+(.+?)$"
        lines = content.split("\n")

        current_section = None
        current_content = []

        for line in lines:
            header_match = re.match(pattern, line)
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = header_match.group(1).lower().replace(" ", "_")
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def parse_failure_log(
        self, failure_log_md: str, config: SystemConfig
    ) -> FailureLog:
        """Parse failure log markdown into FailureLog object"""
        failure_log = FailureLog(max_size=config.max_failure_log_size)

        if not failure_log_md:
            return failure_log

        # Simple parsing - in a real implementation, this would be more robust
        lines = failure_log_md.split("\n")
        current_failure = None
        failure_data = {}

        for line in lines:
            if line.startswith("### Failure #"):
                # Save previous failure
                if current_failure and failure_data:
                    try:
                        failure_entry = FailureEntry.from_dict(failure_data)
                        failure_log.add(failure_entry)
                    except Exception:
                        pass

                # Start new failure
                current_failure = line
                failure_data = {}
            elif line.startswith("**Signature**:"):
                failure_data["failure_signature"] = (
                    line.replace("**Signature**:", "").strip().strip("`")
                )
            elif line.startswith("**Description**:"):
                failure_data["failure_description"] = line.replace(
                    "**Description**:", ""
                ).strip()

        # Save last failure
        if current_failure and failure_data:
            try:
                failure_entry = FailureEntry.from_dict(failure_data)
                failure_log.add(failure_entry)
            except Exception:
                pass

        return failure_log
