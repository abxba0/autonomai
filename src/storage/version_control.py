from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import shutil

from ..models.version import InstructionVersion, VersionMetadata
from ..models.config import SystemConfig


class VersionController:
    """Manages version control for instructions"""

    def __init__(self, versions_dir: Path, config: SystemConfig):
        self.versions_dir = versions_dir
        self.config = config
        self.metadata_file = versions_dir / "commits.json"

        # Ensure directory exists
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Load metadata
        self.metadata: List[Dict[str, Any]] = self._load_metadata()

    def _load_metadata(self) -> List[Dict[str, Any]]:
        """Load version metadata from file"""
        if not self.metadata_file.exists():
            return []

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_metadata(self):
        """Save version metadata to file"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)

    def create_version(self, version: InstructionVersion) -> bool:
        """Create a new version snapshot"""
        try:
            # Save version file
            version_file = self.versions_dir / f"{version.metadata.version_id}.md"
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(version.to_markdown())

            # Update metadata
            self.metadata.append(version.metadata.to_dict())

            # Trim old versions if needed
            if len(self.metadata) > self.config.max_versions_to_keep:
                self._trim_old_versions()

            # Save metadata
            self._save_metadata()

            return True

        except Exception as e:
            print(f"Error creating version: {e}")
            return False

    def _trim_old_versions(self):
        """Remove oldest versions to stay within limit"""
        # Keep only the most recent versions
        keep_count = self.config.max_versions_to_keep
        if len(self.metadata) <= keep_count:
            return

        # Get versions to remove
        versions_to_remove = self.metadata[:-keep_count]

        # Remove files
        for version_data in versions_to_remove:
            version_id = version_data["version_id"]
            version_file = self.versions_dir / f"{version_id}.md"
            if version_file.exists():
                version_file.unlink()

        # Update metadata
        self.metadata = self.metadata[-keep_count:]

    def load_version(self, version_id: str) -> Optional[InstructionVersion]:
        """Load a specific version"""
        version_file = self.versions_dir / f"{version_id}.md"

        if not version_file.exists():
            return None

        try:
            with open(version_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse version (simplified - in real implementation would parse properly)
            lines = content.split("\n")

            # Extract metadata
            metadata_dict = None
            for data in self.metadata:
                if data["version_id"] == version_id:
                    metadata_dict = data
                    break

            if not metadata_dict:
                return None

            metadata = VersionMetadata.from_dict(metadata_dict)

            # Extract sections (simplified)
            base_start = content.find("## Base Instructions")
            appendix_start = content.find("## Dynamic Appendix")

            if base_start != -1 and appendix_start != -1:
                base_instructions = content[
                    base_start + len("## Base Instructions") : appendix_start
                ].strip()
                dynamic_appendix = content[
                    appendix_start + len("## Dynamic Appendix") :
                ].strip()
            else:
                # Fallback
                base_instructions = "Base instructions not found"
                dynamic_appendix = "Dynamic appendix not found"

            return InstructionVersion(
                metadata=metadata,
                base_instructions=base_instructions,
                dynamic_appendix=dynamic_appendix,
            )

        except Exception as e:
            print(f"Error loading version {version_id}: {e}")
            return None

    def get_latest_version_id(self) -> Optional[str]:
        """Get ID of latest version"""
        if not self.metadata:
            return None

        return self.metadata[-1]["version_id"]

    def get_version_n_steps_back(self, steps: int = 1) -> Optional[InstructionVersion]:
        """Get version N steps back from latest"""
        if not self.metadata or steps >= len(self.metadata):
            return None

        version_id = self.metadata[-(steps + 1)]["version_id"]
        return self.load_version(version_id)

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get complete version history"""
        return self.metadata.copy()
