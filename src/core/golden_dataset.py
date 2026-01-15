"""
Golden Dataset - Regression Testing Suite

Maintains a collection of successful interactions that serve as regression tests
for instruction updates.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class GoldenInteraction:
    """A successful interaction to use as a regression test"""
    
    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S%f"))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Input/Output
    user_query: str = ""
    expected_output: str = ""
    
    # Validation criteria
    validation_rules: List[str] = field(default_factory=list)
    must_contain: List[str] = field(default_factory=list)
    must_not_contain: List[str] = field(default_factory=list)
    
    # Context
    instructions_version: Optional[str] = None
    model_used: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Multi-Modal Support (Phase 5)
    modality: str = "text"  # text, vision, audio, multi-modal
    vision_input_refs: List[str] = field(default_factory=list)
    audio_input_refs: List[str] = field(default_factory=list)
    vision_validation_rules: Dict[str, Any] = field(default_factory=dict)
    audio_validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Multi-Tenant Support (Phase 7)
    tenant_id: str = "default"
    
    # Metadata
    success_count: int = 1
    last_validated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "user_query": self.user_query,
            "expected_output": self.expected_output,
            "validation_rules": self.validation_rules,
            "must_contain": self.must_contain,
            "must_not_contain": self.must_not_contain,
            "instructions_version": self.instructions_version,
            "model_used": self.model_used,
            "tags": self.tags,
            "modality": self.modality,
            "vision_input_refs": self.vision_input_refs,
            "audio_input_refs": self.audio_input_refs,
            "vision_validation_rules": self.vision_validation_rules,
            "audio_validation_rules": self.audio_validation_rules,
            "tenant_id": self.tenant_id,
            "success_count": self.success_count,
            "last_validated": self.last_validated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoldenInteraction":
        """Create from dictionary"""
        # Handle backward compatibility - older data may not have new fields
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class RegressionTestResult:
    """Result of running a regression test"""
    
    interaction_id: str
    passed: bool
    error_message: Optional[str] = None
    actual_output: Optional[str] = None
    validation_details: Dict[str, Any] = field(default_factory=dict)


class GoldenDataset:
    """
    Manages a collection of successful interactions for regression testing
    
    The Golden Dataset serves as a safety net to ensure that instruction updates
    don't break previously working functionality.
    """
    
    def __init__(self, storage_path: Path, max_size: int = 100):
        self.storage_path = storage_path
        self.max_size = max_size
        self.interactions: List[GoldenInteraction] = []
        
        # Create storage directory if it doesn't exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing dataset
        self._load()
    
    def add_interaction(
        self,
        user_query: str,
        output: str,
        instructions_version: str,
        model_used: str,
        validation_rules: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> GoldenInteraction:
        """
        Add a successful interaction to the golden dataset
        
        Args:
            user_query: The user's query
            output: The successful model output
            instructions_version: Version ID of instructions used
            model_used: Model name that produced this output
            validation_rules: List of validation rules that passed
            tags: Optional tags for categorization
            
        Returns:
            The created GoldenInteraction
        """
        interaction = GoldenInteraction(
            user_query=user_query,
            expected_output=output,
            validation_rules=validation_rules or [],
            instructions_version=instructions_version,
            model_used=model_used,
            tags=tags or []
        )
        
        # Check if similar interaction already exists
        if not self._is_duplicate(interaction):
            self.interactions.append(interaction)
            
            # Maintain max size (remove oldest if needed)
            if len(self.interactions) > self.max_size:
                self.interactions = self.interactions[-self.max_size:]
            
            self._save()
            print(f"✓ Added interaction to golden dataset (total: {len(self.interactions)})")
        else:
            print(f"  Interaction already in golden dataset")
        
        return interaction
    
    def run_regression_tests(
        self,
        test_function: Any,  # Callable that takes query and returns output
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run regression tests against the golden dataset
        
        Args:
            test_function: Function that takes a query and returns model output
            sample_size: Optional limit on number of tests to run
            
        Returns:
            Dictionary with test results
        """
        if not self.interactions:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 1.0,
                "results": []
            }
        
        # Select interactions to test
        interactions_to_test = self.interactions
        if sample_size and sample_size < len(self.interactions):
            # Test most recent interactions
            interactions_to_test = self.interactions[-sample_size:]
        
        results = []
        passed_count = 0
        failed_count = 0
        
        print(f"\n🧪 Running regression tests on {len(interactions_to_test)} golden interactions...")
        
        for interaction in interactions_to_test:
            try:
                # Run the test
                result = test_function(interaction.user_query)
                
                # Validate the result
                test_result = self._validate_output(interaction, result)
                results.append(test_result)
                
                if test_result.passed:
                    passed_count += 1
                    # Update last validated timestamp
                    interaction.last_validated = datetime.now().isoformat()
                    interaction.success_count += 1
                else:
                    failed_count += 1
                    print(f"  ✗ Test failed: {interaction.id}")
                    print(f"    Error: {test_result.error_message}")
                
            except Exception as e:
                failed_count += 1
                results.append(RegressionTestResult(
                    interaction_id=interaction.id,
                    passed=False,
                    error_message=f"Exception during test: {str(e)}"
                ))
                print(f"  ✗ Test exception: {interaction.id} - {str(e)}")
        
        pass_rate = passed_count / len(interactions_to_test) if interactions_to_test else 1.0
        
        print(f"\n📊 Regression test results: {passed_count}/{len(interactions_to_test)} passed ({pass_rate*100:.1f}%)")
        
        # Save updated dataset
        self._save()
        
        return {
            "total": len(interactions_to_test),
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": pass_rate,
            "results": results
        }
    
    def _validate_output(
        self,
        interaction: GoldenInteraction,
        actual_output: str
    ) -> RegressionTestResult:
        """Validate actual output against expected criteria"""
        
        validation_details = {}
        errors = []
        
        # Check must_contain rules
        for phrase in interaction.must_contain:
            if phrase not in actual_output:
                errors.append(f"Missing required phrase: '{phrase}'")
                validation_details[f"must_contain_{phrase}"] = False
            else:
                validation_details[f"must_contain_{phrase}"] = True
        
        # Check must_not_contain rules
        for phrase in interaction.must_not_contain:
            if phrase in actual_output:
                errors.append(f"Contains forbidden phrase: '{phrase}'")
                validation_details[f"must_not_contain_{phrase}"] = False
            else:
                validation_details[f"must_not_contain_{phrase}"] = True
        
        # For now, we don't require exact output match
        # Instead, we focus on validation rules
        
        passed = len(errors) == 0
        error_message = "; ".join(errors) if errors else None
        
        return RegressionTestResult(
            interaction_id=interaction.id,
            passed=passed,
            error_message=error_message,
            actual_output=actual_output,
            validation_details=validation_details
        )
    
    def _is_duplicate(self, new_interaction: GoldenInteraction) -> bool:
        """Check if similar interaction already exists"""
        for existing in self.interactions:
            if existing.user_query.strip().lower() == new_interaction.user_query.strip().lower():
                return True
        return False
    
    def get_interactions_by_tag(self, tag: str) -> List[GoldenInteraction]:
        """Get all interactions with a specific tag"""
        return [i for i in self.interactions if tag in i.tags]
    
    def get_recent_interactions(self, n: int = 10) -> List[GoldenInteraction]:
        """Get n most recent interactions"""
        return self.interactions[-n:] if len(self.interactions) >= n else self.interactions
    
    def clear(self):
        """Clear all interactions (use with caution)"""
        self.interactions = []
        self._save()
    
    def _load(self):
        """Load dataset from storage"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.interactions = [
                    GoldenInteraction.from_dict(item) for item in data.get("interactions", [])
                ]
            print(f"✓ Loaded {len(self.interactions)} golden interactions from {self.storage_path}")
        except Exception as e:
            print(f"Warning: Could not load golden dataset: {e}")
            self.interactions = []
    
    def _save(self):
        """Save dataset to storage"""
        try:
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "count": len(self.interactions),
                "interactions": [i.to_dict() for i in self.interactions]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving golden dataset: {e}")
    
    def export_to_markdown(self, output_truncate_length: int = 200) -> str:
        """
        Export dataset to markdown format for review
        
        Args:
            output_truncate_length: Maximum length for output display (default: 200)
        """
        md = f"# Golden Dataset\n\n"
        md += f"Total interactions: {len(self.interactions)}\n\n"
        md += f"Last updated: {datetime.now().isoformat()}\n\n"
        md += "---\n\n"
        
        for i, interaction in enumerate(self.interactions, 1):
            md += f"## Interaction {i}: {interaction.id}\n\n"
            md += f"**Timestamp**: {interaction.timestamp}\n\n"
            md += f"**Query**: {interaction.user_query}\n\n"
            
            # Truncate output for display
            output = interaction.expected_output
            if len(output) > output_truncate_length:
                output = output[:output_truncate_length] + "..."
            md += f"**Expected Output**:\n```\n{output}\n```\n\n"
            
            md += f"**Version**: {interaction.instructions_version}\n\n"
            md += f"**Success Count**: {interaction.success_count}\n\n"
            if interaction.tags:
                md += f"**Tags**: {', '.join(interaction.tags)}\n\n"
            md += "---\n\n"
        
        return md
