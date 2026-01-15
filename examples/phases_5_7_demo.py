"""
Example: Using Epic Phases 5-7 Together

This example demonstrates how to use Multi-Modal, Knowledge Graph, and Multi-Tenant
features together in a real-world scenario.

Scenario: A company has two product teams:
- Vision Team: Working on image recognition product (needs vision support)
- Audio Team: Working on voice assistant product (needs audio support)

Each team wants isolated rules and data, but both benefit from the knowledge graph.
"""

from pathlib import Path
import tempfile
from src.models.config import SystemConfig, FailureEntry
from src.core.tenant_manager import TenantManager, TenantConfig
from src.core.rule_graph import RuleGraph
from src.core.multimodal_validator import MultiModalValidator
from src.core.golden_dataset import GoldenDataset, GoldenInteraction


def main():
    print("\n" + "="*70)
    print("Epic Phases 5-7 Integration Demo")
    print("="*70 + "\n")
    
    # ========================================================================
    # Step 1: Configure System with All Features
    # ========================================================================
    print("Step 1: Configuring system with all Phase 5-7 features...")
    
    config = SystemConfig(
        # Phase 1-4 (already implemented)
        enable_semantic_deduplication=True,
        enable_judge_model=True,
        enable_regression_testing=True,
        enable_confidence_throttling=True,
        
        # Phase 5: Multi-Modal
        enable_multimodal=True,
        supported_modalities=["text", "vision", "audio"],
        vision_model="gpt-4-vision-preview",
        audio_model="whisper-1",
        
        # Phase 6: Knowledge Graph
        enable_knowledge_graph=True,
        enable_rule_inheritance=True,
        enable_rule_supersession=True,
        max_rule_depth=5,
        
        # Phase 7: Multi-Tenant
        enable_multi_tenant=True,
        tenant_isolation_strict=True,
    )
    
    print("✓ System configured with multi-modal, knowledge graph, and multi-tenant support\n")
    
    # ========================================================================
    # Step 2: Set Up Multi-Tenant Environment
    # ========================================================================
    print("Step 2: Setting up multi-tenant environment...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create tenant manager
        tenant_manager = TenantManager(base_path=base_path, config=config)
        
        # Create Vision Team tenant
        vision_team = tenant_manager.create_tenant(
            tenant_id="vision_team",
            tenant_name="Vision Product Team",
            max_rules=500,
            max_golden_interactions=200,
            enable_multimodal=True,
            enable_knowledge_graph=True,
            tags=["product-a", "vision", "ml"]
        )
        
        # Create Audio Team tenant
        audio_team = tenant_manager.create_tenant(
            tenant_id="audio_team",
            tenant_name="Audio Product Team",
            max_rules=500,
            max_golden_interactions=200,
            enable_multimodal=True,
            enable_knowledge_graph=True,
            tags=["product-b", "audio", "voice"]
        )
        
        print(f"✓ Created tenant: {vision_team.tenant_name}")
        print(f"✓ Created tenant: {audio_team.tenant_name}\n")
        
        # ====================================================================
        # Step 3: Set Up Knowledge Graphs for Each Tenant
        # ====================================================================
        print("Step 3: Creating knowledge graphs for each tenant...")
        
        # Vision Team Rules
        vision_context = tenant_manager.get_context("vision_team")
        vision_context.ensure_directory()
        vision_graph = RuleGraph(
            config=config,
            storage_path=vision_context.get_rule_graph_path()
        )
        
        # Add hierarchical rules for vision team
        vision_root = vision_graph.add_rule(
            rule_text="All images must be validated before processing",
            category="validation",
            priority=10,
            tenant_id="vision_team",
            tags=["core", "vision"]
        )
        
        vision_quality = vision_graph.add_rule(
            rule_text="Image quality score must be above 0.7",
            category="validation",
            parent_id=vision_root.id,
            priority=8,
            tenant_id="vision_team",
            tags=["quality"]
        )
        
        vision_format = vision_graph.add_rule(
            rule_text="Support JPEG, PNG, and WebP formats only",
            category="validation",
            parent_id=vision_root.id,
            priority=7,
            tenant_id="vision_team",
            tags=["format"]
        )
        
        print(f"✓ Created {len(vision_graph.nodes)} rules for Vision Team")
        
        # Audio Team Rules
        audio_context = tenant_manager.get_context("audio_team")
        audio_context.ensure_directory()
        audio_graph = RuleGraph(
            config=config,
            storage_path=audio_context.get_rule_graph_path()
        )
        
        # Add hierarchical rules for audio team
        audio_root = audio_graph.add_rule(
            rule_text="All audio must be validated before transcription",
            category="validation",
            priority=10,
            tenant_id="audio_team",
            tags=["core", "audio"]
        )
        
        audio_quality = audio_graph.add_rule(
            rule_text="Audio quality must be sufficient for transcription",
            category="validation",
            parent_id=audio_root.id,
            priority=8,
            tenant_id="audio_team",
            tags=["quality"]
        )
        
        audio_duration = audio_graph.add_rule(
            rule_text="Audio clips must be between 0.5 and 120 seconds",
            category="validation",
            parent_id=audio_root.id,
            priority=7,
            tenant_id="audio_team",
            tags=["duration"]
        )
        
        print(f"✓ Created {len(audio_graph.nodes)} rules for Audio Team\n")
        
        # ====================================================================
        # Step 4: Create Multi-Modal Validators
        # ====================================================================
        print("Step 4: Setting up multi-modal validators...")
        
        validator = MultiModalValidator(config)
        
        print("✓ Multi-modal validator ready (vision + audio)\n")
        
        # ====================================================================
        # Step 5: Simulate Vision Team Workflow
        # ====================================================================
        print("Step 5: Simulating Vision Team workflow...")
        
        # Create a test image file
        test_image = vision_context.ensure_directory() / "test_image.png"
        test_image.write_text("mock image data")
        
        # Validate vision input
        vision_result = validator.validate_vision(
            image_refs=[str(test_image)],
            min_quality=0.7
        )
        
        print(f"  Vision validation: {'✓ Passed' if vision_result.is_valid else '✗ Failed'}")
        print(f"  Confidence: {vision_result.confidence:.2f}")
        
        # Update rule statistics
        vision_graph.update_rule_stats(
            vision_quality.id,
            success=vision_result.is_valid
        )
        
        # Create a failure entry if validation failed
        if not vision_result.is_valid:
            failure = FailureEntry(
                trigger_type="auto_validation",
                failure_description="Image quality validation failed",
                modality="vision",
                vision_input_refs=[str(test_image)],
                vision_validation_errors=vision_result.to_dict(),
                tenant_id="vision_team"
            )
            print(f"  Created failure entry: {failure.id}")
        else:
            # Add to golden dataset
            vision_dataset = GoldenDataset(
                storage_path=vision_context.get_golden_dataset_path(),
                max_size=200
            )
            
            interaction = GoldenInteraction(
                user_query="Validate this image",
                expected_output="Image validation passed",
                modality="vision",
                vision_input_refs=[str(test_image)],
                vision_validation_rules={"min_quality": 0.7},
                tenant_id="vision_team",
                instructions_version="v1.0.0",
                model_used=config.vision_model or "default"
            )
            vision_dataset.interactions.append(interaction)
            vision_dataset._save()
            
            print(f"  Added to golden dataset: {len(vision_dataset.interactions)} interactions")
        
        print()
        
        # ====================================================================
        # Step 6: Simulate Audio Team Workflow
        # ====================================================================
        print("Step 6: Simulating Audio Team workflow...")
        
        # Create a test audio file
        test_audio = audio_context.ensure_directory() / "test_audio.mp3"
        test_audio.write_text("mock audio data")
        
        # Validate audio input
        audio_result = validator.validate_audio(
            audio_refs=[str(test_audio)],
            min_duration=0.5,
            max_duration=120.0
        )
        
        print(f"  Audio validation: {'✓ Passed' if audio_result.is_valid else '✗ Failed'}")
        print(f"  Confidence: {audio_result.confidence:.2f}")
        
        # Update rule statistics
        audio_graph.update_rule_stats(
            audio_duration.id,
            success=audio_result.is_valid
        )
        
        # Add to golden dataset
        if audio_result.is_valid:
            audio_dataset = GoldenDataset(
                storage_path=audio_context.get_golden_dataset_path(),
                max_size=200
            )
            
            interaction = GoldenInteraction(
                user_query="Transcribe this audio",
                expected_output="Audio transcription completed",
                modality="audio",
                audio_input_refs=[str(test_audio)],
                audio_validation_rules={"min_duration": 0.5, "max_duration": 120.0},
                tenant_id="audio_team",
                instructions_version="v1.0.0",
                model_used=config.audio_model or "default"
            )
            audio_dataset.interactions.append(interaction)
            audio_dataset._save()
            
            print(f"  Added to golden dataset: {len(audio_dataset.interactions)} interactions")
        
        print()
        
        # ====================================================================
        # Step 7: Demonstrate Tenant Isolation
        # ====================================================================
        print("Step 7: Verifying tenant isolation...")
        
        # Get rules for each tenant
        vision_rules = vision_graph.get_active_rules(tenant_id="vision_team")
        audio_rules = audio_graph.get_active_rules(tenant_id="audio_team")
        
        print(f"  Vision Team rules: {len(vision_rules)}")
        print(f"  Audio Team rules: {len(audio_rules)}")
        
        # Verify isolation
        vision_rule_ids = {r.id for r in vision_rules}
        audio_rule_ids = {r.id for r in audio_rules}
        
        if vision_rule_ids.isdisjoint(audio_rule_ids):
            print("  ✓ Rules are properly isolated between tenants")
        else:
            print("  ✗ Warning: Rule overlap detected")
        
        # Check file isolation
        vision_paths = [
            vision_context.get_instructions_path(),
            vision_context.get_golden_dataset_path(),
            vision_context.get_rule_graph_path()
        ]
        
        audio_paths = [
            audio_context.get_instructions_path(),
            audio_context.get_golden_dataset_path(),
            audio_context.get_rule_graph_path()
        ]
        
        # Verify paths are different
        for v_path, a_path in zip(vision_paths, audio_paths):
            if "vision_team" in str(v_path) and "audio_team" in str(a_path):
                continue
            else:
                print(f"  ✗ Warning: Paths not properly isolated")
                break
        else:
            print("  ✓ File paths are properly isolated between tenants")
        
        print()
        
        # ====================================================================
        # Step 8: Show Rule Hierarchy and Statistics
        # ====================================================================
        print("Step 8: Displaying rule hierarchies and statistics...")
        
        print("\n  Vision Team Rule Hierarchy:")
        vision_hierarchy = vision_graph.get_rule_hierarchy(tenant_id="vision_team")
        for root in vision_hierarchy["roots"]:
            print(f"    └─ {root['rule_text'][:50]}...")
            print(f"       Priority: {root['priority']}, Active: {root['is_active']}")
            for child in root["children"]:
                print(f"       └─ {child['rule_text'][:50]}...")
                print(f"          Priority: {child['priority']}")
        
        print("\n  Audio Team Rule Hierarchy:")
        audio_hierarchy = audio_graph.get_rule_hierarchy(tenant_id="audio_team")
        for root in audio_hierarchy["roots"]:
            print(f"    └─ {root['rule_text'][:50]}...")
            print(f"       Priority: {root['priority']}, Active: {root['is_active']}")
            for child in root["children"]:
                print(f"       └─ {child['rule_text'][:50]}...")
                print(f"          Priority: {child['priority']}")
        
        print()
        
        # ====================================================================
        # Step 9: Demonstrate Rule Supersession
        # ====================================================================
        print("Step 9: Demonstrating rule supersession...")
        
        # Vision team realizes they need to update quality threshold
        print("  Updating Vision Team's quality rule...")
        
        new_quality_rule = vision_graph.supersede_rule(
            old_rule_id=vision_quality.id,
            new_rule_text="Image quality score must be above 0.8 (updated threshold)",
            priority=9
        )
        
        old_rule = vision_graph.get_rule(vision_quality.id)
        print(f"  Old rule active: {old_rule.is_active}")
        print(f"  New rule active: {new_quality_rule.is_active}")
        print(f"  New rule supersedes: {new_quality_rule.supersedes_ids}")
        print("  ✓ Rule supersession completed")
        
        print()
        
        # ====================================================================
        # Step 10: Show Tenant Statistics
        # ====================================================================
        print("Step 10: Displaying tenant statistics...")
        
        vision_stats = tenant_manager.get_tenant_stats("vision_team")
        audio_stats = tenant_manager.get_tenant_stats("audio_team")
        
        print(f"\n  Vision Team Statistics:")
        print(f"    Active: {vision_stats['is_active']}")
        print(f"    Files exist:")
        print(f"      - Golden dataset: {vision_stats['files_exist']['golden_dataset']}")
        print(f"      - Rule graph: {vision_stats['files_exist']['rule_graph']}")
        
        print(f"\n  Audio Team Statistics:")
        print(f"    Active: {audio_stats['is_active']}")
        print(f"    Files exist:")
        print(f"      - Golden dataset: {audio_stats['files_exist']['golden_dataset']}")
        print(f"      - Rule graph: {audio_stats['files_exist']['rule_graph']}")
        
        print()
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("="*70)
    print("Demo Summary")
    print("="*70)
    print("""
This demo demonstrated:

✓ Phase 5 (Multi-Modal): 
  - Vision and audio validation
  - Modality-specific failure entries
  - Multi-modal golden interactions

✓ Phase 6 (Knowledge Graph):
  - Hierarchical rule organization
  - Parent-child relationships
  - Rule supersession tracking
  - Per-rule statistics

✓ Phase 7 (Multi-Tenant):
  - Complete tenant isolation
  - Separate data storage per tenant
  - Tenant-specific configurations
  - Independent rule graphs

All features work together seamlessly while maintaining:
- Complete backward compatibility
- Clear separation of concerns
- Scalable architecture
- Production-ready implementation
""")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
