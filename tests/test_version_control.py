"""
Unit tests for VersionController.

Tests version creation, loading, trimming, metadata persistence,
and edge cases for the instruction versioning system.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.storage.version_control import VersionController
from src.models.version import InstructionVersion, VersionMetadata
from src.models.config import SystemConfig


@pytest.fixture
def tmp_versions_dir(tmp_path):
    """Create a temporary directory for version storage."""
    versions_dir = tmp_path / ".versions"
    versions_dir.mkdir()
    return versions_dir


@pytest.fixture
def config():
    """Create a SystemConfig with test-friendly defaults."""
    return SystemConfig(max_versions_to_keep=5)


@pytest.fixture
def controller(tmp_versions_dir, config):
    """Create a VersionController with temp storage."""
    return VersionController(versions_dir=tmp_versions_dir, config=config)


def _make_version(base="Base instructions", appendix="Dynamic rules", **kwargs):
    """Helper to create an InstructionVersion with a unique ID."""
    import uuid

    metadata = VersionMetadata(
        trigger_type=kwargs.get("trigger_type", "auto_validation"),
        critic_justification=kwargs.get("justification", "Test justification"),
        diff_summary=kwargs.get("diff_summary", "Test diff"),
        failure_signature=kwargs.get("failure_signature", None),
        version_id=kwargs.get("version_id", f"v_test_{uuid.uuid4().hex[:12]}"),
    )
    return InstructionVersion(
        metadata=metadata,
        base_instructions=base,
        dynamic_appendix=appendix,
    )


class TestVersionControllerCreation:
    """Tests for creating versions."""

    def test_create_version_succeeds(self, controller):
        version = _make_version()
        result = controller.create_version(version)
        assert result is True

    def test_create_version_writes_file(self, controller, tmp_versions_dir):
        version = _make_version()
        controller.create_version(version)
        version_file = tmp_versions_dir / f"{version.metadata.version_id}.md"
        assert version_file.exists()

    def test_create_version_updates_metadata(self, controller):
        version = _make_version()
        controller.create_version(version)
        assert len(controller.metadata) == 1
        assert controller.metadata[0]["version_id"] == version.metadata.version_id

    def test_create_version_saves_metadata_file(self, controller, tmp_versions_dir):
        version = _make_version()
        controller.create_version(version)
        metadata_file = tmp_versions_dir / "commits.json"
        assert metadata_file.exists()
        with open(metadata_file) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_create_multiple_versions(self, controller):
        for i in range(3):
            version = _make_version(base=f"Base v{i}")
            controller.create_version(version)
        assert len(controller.metadata) == 3


class TestVersionControllerLoading:
    """Tests for loading versions."""

    def test_load_existing_version(self, controller):
        version = _make_version(base="Test base", appendix="Test appendix")
        controller.create_version(version)
        loaded = controller.load_version(version.metadata.version_id)
        assert loaded is not None
        assert loaded.base_instructions == "Test base"
        assert loaded.dynamic_appendix == "Test appendix"

    def test_load_nonexistent_version(self, controller):
        loaded = controller.load_version("nonexistent-id")
        assert loaded is None

    def test_get_latest_version_id(self, controller):
        v1 = _make_version(base="v1")
        v2 = _make_version(base="v2")
        controller.create_version(v1)
        controller.create_version(v2)
        assert controller.get_latest_version_id() == v2.metadata.version_id

    def test_get_latest_version_id_empty(self, controller):
        assert controller.get_latest_version_id() is None

    def test_get_version_n_steps_back(self, controller):
        versions = []
        for i in range(3):
            v = _make_version(base=f"v{i}")
            controller.create_version(v)
            versions.append(v)
        loaded = controller.get_version_n_steps_back(steps=1)
        assert loaded is not None
        assert loaded.metadata.version_id == versions[1].metadata.version_id

    def test_get_version_n_steps_back_too_far(self, controller):
        v = _make_version()
        controller.create_version(v)
        assert controller.get_version_n_steps_back(steps=5) is None


class TestVersionControllerTrimming:
    """Tests for trimming old versions."""

    def test_trim_old_versions(self, controller, tmp_versions_dir, config):
        versions = []
        for i in range(config.max_versions_to_keep + 3):
            v = _make_version(base=f"v{i}")
            controller.create_version(v)
            versions.append(v)

        assert len(controller.metadata) == config.max_versions_to_keep
        # Oldest versions should be trimmed
        oldest_file = tmp_versions_dir / f"{versions[0].metadata.version_id}.md"
        assert not oldest_file.exists()
        # Latest versions should remain
        latest_file = tmp_versions_dir / f"{versions[-1].metadata.version_id}.md"
        assert latest_file.exists()

    def test_version_history_returns_copy(self, controller):
        v = _make_version()
        controller.create_version(v)
        history = controller.get_version_history()
        history.clear()
        assert len(controller.get_version_history()) == 1


class TestVersionControllerEdgeCases:
    """Edge case tests."""

    def test_metadata_persistence_across_instances(self, tmp_versions_dir, config):
        ctrl1 = VersionController(versions_dir=tmp_versions_dir, config=config)
        v = _make_version()
        ctrl1.create_version(v)

        ctrl2 = VersionController(versions_dir=tmp_versions_dir, config=config)
        assert len(ctrl2.metadata) == 1
        assert ctrl2.get_latest_version_id() == v.metadata.version_id

    def test_empty_metadata_file(self, tmp_versions_dir, config):
        metadata_file = tmp_versions_dir / "commits.json"
        metadata_file.write_text("")
        ctrl = VersionController(versions_dir=tmp_versions_dir, config=config)
        assert ctrl.metadata == []

    def test_corrupt_metadata_file(self, tmp_versions_dir, config):
        metadata_file = tmp_versions_dir / "commits.json"
        metadata_file.write_text("not valid json{{{")
        ctrl = VersionController(versions_dir=tmp_versions_dir, config=config)
        assert ctrl.metadata == []

    def test_versions_dir_auto_created(self, tmp_path, config):
        versions_dir = tmp_path / "new_versions_dir"
        ctrl = VersionController(versions_dir=versions_dir, config=config)
        assert versions_dir.exists()
        assert ctrl.metadata == []
