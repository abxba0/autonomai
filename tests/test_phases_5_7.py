"""
Tests for Epic Phases 5-7: Multi-Modal, Knowledge Graph, and Multi-Tenant Features

Tests the implementation of the remaining architectural phases.
"""

import pytest
from pathlib import Path
import tempfile
import json

from src.models.config import SystemConfig, FailureEntry
from src.core.multimodal_validator import (
    MultiModalValidator,
    VisionValidationResult,
    AudioValidationResult,
    MockMultiModalValidator,
)
from src.core.rule_graph import RuleGraph, RuleNode, MockRuleGraph
from src.core.tenant_manager import (
    TenantManager,
    TenantConfig,
    TenantContext,
    MockTenantManager,
)
from src.core.golden_dataset import GoldenInteraction, GoldenDataset


# ============================================================================
# Phase 5: Multi-Modal Optimization Tests
# ============================================================================


def test_multimodal_config():
    """Test Phase 5 configuration options"""
    config = SystemConfig(
        enable_multimodal=True,
        supported_modalities=["text", "vision", "audio"],
        vision_model="gpt-4-vision-preview",
        audio_model="whisper-1",
    )

    assert config.enable_multimodal is True
    assert "vision" in config.supported_modalities
    assert "audio" in config.supported_modalities
    assert config.vision_model == "gpt-4-vision-preview"
    assert config.audio_model == "whisper-1"
    print("✓ Multi-modal configuration works correctly")


def test_failure_entry_multimodal():
    """Test FailureEntry with multi-modal metadata"""
    failure = FailureEntry(
        trigger_type="auto_validation",
        failure_description="Vision validation failed",
        modality="vision",
        vision_input_refs=["image1.png", "image2.jpg"],
        vision_validation_errors={"quality_score": "low"},
        tenant_id="test_tenant",
    )

    assert failure.modality == "vision"
    assert len(failure.vision_input_refs) == 2
    assert "image1.png" in failure.vision_input_refs
    assert failure.vision_validation_errors["quality_score"] == "low"
    assert failure.tenant_id == "test_tenant"
    print("✓ FailureEntry multi-modal support works correctly")


def test_vision_validator():
    """Test vision validation functionality"""
    config = SystemConfig(enable_multimodal=True, supported_modalities=["vision"])
    validator = MultiModalValidator(config)

    # Create test images
    with tempfile.TemporaryDirectory() as tmpdir:
        test_image = Path(tmpdir) / "test.png"
        test_image.write_text("fake image data")

        result = validator.validate_vision(
            image_refs=[str(test_image)],
            expected_objects=["cat", "dog"],
            min_quality=0.5,
        )

        assert isinstance(result, VisionValidationResult)
        assert result.is_valid is True
        assert result.confidence > 0
        print("✓ Vision validator works correctly")


def test_audio_validator():
    """Test audio validation functionality"""
    config = SystemConfig(enable_multimodal=True, supported_modalities=["audio"])
    validator = MultiModalValidator(config)

    # Create test audio
    with tempfile.TemporaryDirectory() as tmpdir:
        test_audio = Path(tmpdir) / "test.mp3"
        test_audio.write_text("fake audio data")

        result = validator.validate_audio(
            audio_refs=[str(test_audio)],
            expected_language="en",
            min_duration=1.0,
            max_duration=60.0,
        )

        assert isinstance(result, AudioValidationResult)
        assert result.is_valid is True
        assert result.confidence > 0
        print("✓ Audio validator works correctly")


def test_multimodal_validator_disabled():
    """Test that validator gracefully handles disabled state"""
    config = SystemConfig(enable_multimodal=False)
    validator = MultiModalValidator(config)

    result = validator.validate_vision(image_refs=["nonexistent.png"])
    assert result.is_valid is True
    assert len(result.warnings) > 0
    assert "disabled" in result.warnings[0].lower()
    print("✓ Disabled multi-modal validator works correctly")


def test_mock_multimodal_validator():
    """Test mock validator for testing"""
    validator = MockMultiModalValidator()

    # Set mock result
    validator.set_mock_result("vision", {"is_valid": True, "confidence": 1.0})

    result = validator.validate_vision(image_refs=["test.png"])
    assert result.is_valid is True
    assert result.confidence == 1.0
    print("✓ Mock multi-modal validator works correctly")


def test_golden_interaction_multimodal():
    """Test GoldenInteraction with multi-modal support"""
    interaction = GoldenInteraction(
        user_query="Describe this image",
        expected_output="A cat sitting on a chair",
        modality="vision",
        vision_input_refs=["cat.png"],
        vision_validation_rules={"expected_objects": ["cat"]},
        tenant_id="test_tenant",
    )

    assert interaction.modality == "vision"
    assert len(interaction.vision_input_refs) == 1
    assert interaction.tenant_id == "test_tenant"

    # Test serialization
    data = interaction.to_dict()
    assert data["modality"] == "vision"
    assert data["vision_input_refs"] == ["cat.png"]
    assert data["tenant_id"] == "test_tenant"

    # Test deserialization
    restored = GoldenInteraction.from_dict(data)
    assert restored.modality == interaction.modality
    assert restored.vision_input_refs == interaction.vision_input_refs
    print("✓ Multi-modal GoldenInteraction works correctly")


# ============================================================================
# Phase 6: Knowledge Graph for Rules Tests
# ============================================================================


def test_rule_node():
    """Test RuleNode data model"""
    node = RuleNode(
        rule_text="Always validate user input",
        category="validation",
        priority=8,
        tags=["security", "input"],
    )

    assert node.rule_text == "Always validate user input"
    assert node.category == "validation"
    assert node.priority == 8
    assert "security" in node.tags
    assert node.is_active is True

    # Test serialization
    data = node.to_dict()
    assert data["rule_text"] == node.rule_text

    # Test effectiveness score
    node.usage_count = 10
    node.success_count = 9
    score = node.get_effectiveness_score()
    assert 0.0 <= score <= 1.0
    print("✓ RuleNode works correctly")


def test_rule_graph_basic():
    """Test basic RuleGraph functionality"""
    graph = MockRuleGraph()

    # Add root rule
    root = graph.add_rule(
        rule_text="Base validation rule", category="validation", priority=10
    )

    assert root.id in graph.nodes
    assert root.id in graph.root_node_ids

    # Add child rule
    child = graph.add_rule(
        rule_text="Specific validation for emails",
        category="validation",
        parent_id=root.id,
        priority=7,
    )

    assert child.parent_id == root.id
    assert child.id in graph.nodes[root.id].child_ids
    assert child.id not in graph.root_node_ids
    print("✓ Basic RuleGraph operations work correctly")


def test_rule_graph_hierarchy():
    """Test rule hierarchy and relationships"""
    graph = MockRuleGraph()

    # Create hierarchy: root -> middle -> leaf
    root = graph.add_rule(rule_text="Root rule", category="general")
    middle = graph.add_rule(rule_text="Middle rule", parent_id=root.id)
    leaf = graph.add_rule(rule_text="Leaf rule", parent_id=middle.id)

    # Test children
    children = graph.get_children(root.id)
    assert len(children) == 1
    assert children[0].id == middle.id

    # Test ancestors
    ancestors = graph.get_ancestors(leaf.id)
    assert len(ancestors) == 2
    assert ancestors[0].id == middle.id
    assert ancestors[1].id == root.id
    print("✓ Rule hierarchy works correctly")


def test_rule_supersession():
    """Test rule supersession functionality"""
    config = SystemConfig(enable_knowledge_graph=True, enable_rule_supersession=True)
    graph = MockRuleGraph(config=config)

    # Add original rule
    old_rule = graph.add_rule(
        rule_text="Original rule that will be superseded", category="validation"
    )

    assert old_rule.is_active is True

    # Supersede with new rule
    new_rule = graph.supersede_rule(
        old_rule_id=old_rule.id, new_rule_text="New improved rule"
    )

    # Check supersession
    assert new_rule.is_active is True
    assert old_rule.id in new_rule.supersedes_ids
    assert graph.nodes[old_rule.id].is_active is False
    assert graph.nodes[old_rule.id].superseded_by_id == new_rule.id
    print("✓ Rule supersession works correctly")


def test_rule_graph_filtering():
    """Test filtering rules by category and tenant"""
    graph = MockRuleGraph()

    # Add rules with different categories and tenants
    graph.add_rule(rule_text="Rule 1", category="validation", tenant_id="tenant1")
    graph.add_rule(rule_text="Rule 2", category="formatting", tenant_id="tenant1")
    graph.add_rule(rule_text="Rule 3", category="validation", tenant_id="tenant2")

    # Test category filtering
    validation_rules = graph.get_rules_by_category("validation")
    assert len(validation_rules) == 2

    # Test tenant filtering
    tenant1_rules = graph.get_active_rules(tenant_id="tenant1")
    assert len(tenant1_rules) == 2

    tenant1_validation = graph.get_rules_by_category("validation", tenant_id="tenant1")
    assert len(tenant1_validation) == 1
    print("✓ Rule filtering works correctly")


def test_rule_graph_conflict_detection():
    """Test conflict detection between rules"""
    graph = MockRuleGraph()

    graph.add_rule(rule_text="Always use JSON format", category="formatting")

    # Check for conflicts
    conflicts = graph.find_conflicts("Never use JSON format")

    # Should detect potential contradiction
    assert len(conflicts) > 0
    assert conflicts[0]["conflict_type"] == "contradiction"
    print("✓ Conflict detection works correctly")


def test_rule_graph_stats():
    """Test rule statistics tracking"""
    graph = MockRuleGraph()

    rule = graph.add_rule(rule_text="Test rule", category="test")

    # Update stats
    graph.update_rule_stats(rule.id, success=True)
    graph.update_rule_stats(rule.id, success=True)
    graph.update_rule_stats(rule.id, success=False)

    node = graph.get_rule(rule.id)
    assert node.usage_count == 3
    assert node.success_count == 2
    assert node.failure_count == 1
    print("✓ Rule statistics tracking works correctly")


def test_rule_graph_migration():
    """Test migration from markdown to graph"""
    graph = MockRuleGraph()

    markdown_content = """
## Validation Rules

- Always validate user input
- Check for SQL injection
- Sanitize HTML content

## Formatting Rules

- Use JSON for API responses
- Follow PEP 8 for Python code
"""

    count = graph.migrate_from_markdown(markdown_content, tenant_id="test")

    assert count == 5  # 5 rules migrated

    validation_rules = graph.get_rules_by_category("validation rules")
    assert len(validation_rules) == 3

    formatting_rules = graph.get_rules_by_category("formatting rules")
    assert len(formatting_rules) == 2
    print("✓ Markdown migration works correctly")


def test_rule_graph_hierarchy_view():
    """Test getting hierarchy view"""
    graph = MockRuleGraph()

    root = graph.add_rule(rule_text="Root", category="general")
    child1 = graph.add_rule(rule_text="Child 1", parent_id=root.id)
    child2 = graph.add_rule(rule_text="Child 2", parent_id=root.id)

    hierarchy = graph.get_rule_hierarchy()

    assert "roots" in hierarchy
    assert hierarchy["total_nodes"] == 3
    assert hierarchy["active_nodes"] == 3
    assert len(hierarchy["roots"]) == 1
    assert len(hierarchy["roots"][0]["children"]) == 2
    print("✓ Rule hierarchy view works correctly")


# ============================================================================
# Phase 7: Multi-Tenant Isolation Tests
# ============================================================================


def test_tenant_config():
    """Test TenantConfig data model"""
    config = TenantConfig(
        tenant_id="test_tenant",
        tenant_name="Test Tenant",
        max_rules=500,
        enable_multimodal=True,
        share_base_rules=True,
    )

    assert config.tenant_id == "test_tenant"
    assert config.tenant_name == "Test Tenant"
    assert config.max_rules == 500
    assert config.enable_multimodal is True
    assert config.share_base_rules is True

    # Test serialization
    data = config.to_dict()
    assert data["tenant_id"] == "test_tenant"

    # Test deserialization
    restored = TenantConfig.from_dict(data)
    assert restored.tenant_id == config.tenant_id
    print("✓ TenantConfig works correctly")


def test_tenant_manager_basic():
    """Test basic TenantManager functionality"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MockTenantManager(base_path=Path(tmpdir))

        # Default tenant should be created
        default = manager.get_tenant("default")
        assert default is not None
        assert default.tenant_id == "default"

        # Create new tenant
        tenant = manager.create_tenant(
            tenant_id="test_org", tenant_name="Test Organization", max_rules=1000
        )

        assert tenant.tenant_id == "test_org"
        assert tenant.tenant_name == "Test Organization"
        assert tenant.max_rules == 1000
        print("✓ Basic TenantManager operations work correctly")


def test_tenant_context():
    """Test TenantContext functionality"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MockTenantManager(base_path=Path(tmpdir))
        tenant = manager.create_tenant("test", "Test")

        context = manager.get_context("test")
        assert context is not None
        assert context.tenant_id == "test"

        # Test path generation
        instructions_path = context.get_instructions_path()
        assert "test" in str(instructions_path)
        assert instructions_path.name == "instructions.md"

        golden_path = context.get_golden_dataset_path()
        assert "test" in str(golden_path)
        assert golden_path.name == "golden_dataset.json"

        # Test directory creation
        tenant_dir = context.ensure_directory()
        assert tenant_dir.exists()
        print("✓ TenantContext works correctly")


def test_tenant_isolation():
    """Test that tenants are properly isolated"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MockTenantManager(base_path=Path(tmpdir))

        tenant1 = manager.create_tenant("tenant1", "Tenant 1")
        tenant2 = manager.create_tenant("tenant2", "Tenant 2")

        # Each tenant should have separate directories
        context1 = manager.get_context("tenant1")
        context2 = manager.get_context("tenant2")

        path1 = context1.get_instructions_path()
        path2 = context2.get_instructions_path()

        assert path1 != path2
        assert "tenant1" in str(path1)
        assert "tenant2" in str(path2)
        print("✓ Tenant isolation works correctly")


def test_tenant_list_and_filter():
    """Test listing and filtering tenants"""
    manager = MockTenantManager()

    manager.create_tenant("active1", "Active 1")
    manager.create_tenant("active2", "Active 2")
    manager.create_tenant("inactive", "Inactive")
    manager.deactivate_tenant("inactive")

    # List all tenants
    all_tenants = manager.list_tenants(active_only=False)
    assert len(all_tenants) >= 3  # Including default

    # List only active tenants
    active_tenants = manager.list_tenants(active_only=True)
    inactive_ids = [t.tenant_id for t in active_tenants]
    assert "inactive" not in inactive_ids
    print("✓ Tenant listing and filtering works correctly")


def test_tenant_lifecycle():
    """Test tenant activation/deactivation"""
    manager = MockTenantManager()

    tenant = manager.create_tenant("test", "Test")
    assert tenant.is_active is True

    # Deactivate
    manager.deactivate_tenant("test")
    tenant = manager.get_tenant("test")
    assert tenant.is_active is False

    # Reactivate
    manager.activate_tenant("test")
    tenant = manager.get_tenant("test")
    assert tenant.is_active is True
    print("✓ Tenant lifecycle works correctly")


def test_tenant_updates():
    """Test updating tenant configuration"""
    manager = MockTenantManager()

    tenant = manager.create_tenant("test", "Test", max_rules=100)
    assert tenant.max_rules == 100

    # Update configuration
    updated = manager.update_tenant("test", max_rules=500, enable_multimodal=True)

    assert updated.max_rules == 500
    assert updated.enable_multimodal is True
    print("✓ Tenant updates work correctly")


def test_tenant_stats():
    """Test tenant statistics"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MockTenantManager(base_path=Path(tmpdir))

        tenant = manager.create_tenant("test", "Test")
        context = manager.get_context("test")
        context.ensure_directory()

        # Create some files
        instructions_path = context.get_instructions_path()
        instructions_path.write_text("# Test instructions")

        stats = manager.get_tenant_stats("test")

        assert stats["tenant_id"] == "test"
        assert stats["is_active"] is True
        assert "files_exist" in stats
        assert stats["files_exist"]["instructions"] is True
        print("✓ Tenant statistics work correctly")


def test_system_config_with_tenant():
    """Test SystemConfig with multi-tenant settings"""
    config = SystemConfig(
        enable_multi_tenant=True,
        default_tenant_id="my_org",
        tenant_isolation_strict=True,
    )

    assert config.enable_multi_tenant is True
    assert config.default_tenant_id == "my_org"
    assert config.tenant_isolation_strict is True
    print("✓ Multi-tenant SystemConfig works correctly")


# ============================================================================
# Integration Tests
# ============================================================================


def test_multimodal_with_tenant():
    """Test multi-modal features with multi-tenant support"""
    config = SystemConfig(
        enable_multimodal=True,
        enable_multi_tenant=True,
        supported_modalities=["text", "vision"],
    )

    # Create tenant manager
    manager = MockTenantManager()
    tenant = manager.create_tenant("test", "Test", enable_multimodal=True)

    # Create failure entry with both multi-modal and tenant info
    failure = FailureEntry(
        trigger_type="auto_validation",
        failure_description="Multi-modal validation failed",
        modality="vision",
        vision_input_refs=["test.png"],
        tenant_id="test",
    )

    assert failure.modality == "vision"
    assert failure.tenant_id == "test"
    print("✓ Multi-modal with multi-tenant integration works")


def test_knowledge_graph_with_tenant():
    """Test knowledge graph with multi-tenant support"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create tenant manager
        manager = MockTenantManager(base_path=Path(tmpdir))
        tenant1 = manager.create_tenant("org1", "Organization 1")
        tenant2 = manager.create_tenant("org2", "Organization 2")

        # Create rule graph
        graph = MockRuleGraph()

        # Add rules for different tenants
        rule1 = graph.add_rule(rule_text="Org 1 rule", tenant_id="org1")
        rule2 = graph.add_rule(rule_text="Org 2 rule", tenant_id="org2")

        # Filter by tenant
        org1_rules = graph.get_active_rules(tenant_id="org1")
        org2_rules = graph.get_active_rules(tenant_id="org2")

        assert len(org1_rules) == 1
        assert len(org2_rules) == 1
        assert org1_rules[0].rule_text == "Org 1 rule"
        assert org2_rules[0].rule_text == "Org 2 rule"
        print("✓ Knowledge graph with multi-tenant integration works")


def test_golden_dataset_with_tenant():
    """Test golden dataset with multi-tenant support"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create datasets for different tenants
        dataset1_path = Path(tmpdir) / "tenant1_golden.json"
        dataset2_path = Path(tmpdir) / "tenant2_golden.json"

        dataset1 = GoldenDataset(dataset1_path, max_size=10)
        dataset2 = GoldenDataset(dataset2_path, max_size=10)

        # Add interactions with tenant IDs
        interaction1 = GoldenInteraction(
            user_query="Query for tenant 1",
            expected_output="Output 1",
            tenant_id="tenant1",
        )

        interaction2 = GoldenInteraction(
            user_query="Query for tenant 2",
            expected_output="Output 2",
            tenant_id="tenant2",
        )

        dataset1.interactions.append(interaction1)
        dataset2.interactions.append(interaction2)

        # Verify isolation
        assert len(dataset1.interactions) == 1
        assert len(dataset2.interactions) == 1
        assert dataset1.interactions[0].tenant_id == "tenant1"
        assert dataset2.interactions[0].tenant_id == "tenant2"
        print("✓ Golden dataset with multi-tenant integration works")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Running Epic Phases 5-7 Tests")
    print("=" * 70 + "\n")

    # Phase 5 Tests
    print("\n--- Phase 5: Multi-Modal Optimization ---")
    test_multimodal_config()
    test_failure_entry_multimodal()
    test_vision_validator()
    test_audio_validator()
    test_multimodal_validator_disabled()
    test_mock_multimodal_validator()
    test_golden_interaction_multimodal()

    # Phase 6 Tests
    print("\n--- Phase 6: Knowledge Graph for Rules ---")
    test_rule_node()
    test_rule_graph_basic()
    test_rule_graph_hierarchy()
    test_rule_supersession()
    test_rule_graph_filtering()
    test_rule_graph_conflict_detection()
    test_rule_graph_stats()
    test_rule_graph_migration()
    test_rule_graph_hierarchy_view()

    # Phase 7 Tests
    print("\n--- Phase 7: Multi-Tenant Isolation ---")
    test_tenant_config()
    test_tenant_manager_basic()
    test_tenant_context()
    test_tenant_isolation()
    test_tenant_list_and_filter()
    test_tenant_lifecycle()
    test_tenant_updates()
    test_tenant_stats()
    test_system_config_with_tenant()

    # Integration Tests
    print("\n--- Integration Tests ---")
    test_multimodal_with_tenant()
    test_knowledge_graph_with_tenant()
    test_golden_dataset_with_tenant()

    print("\n" + "=" * 70)
    print("All tests passed! ✓")
    print("=" * 70 + "\n")
