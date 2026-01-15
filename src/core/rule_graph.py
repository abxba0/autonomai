"""
Knowledge Graph for Rules - Phase 6 Implementation

Provides hierarchical rule storage with parent-child relationships,
rule inheritance, and supersession tracking.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class RuleNode:
    """Represents a single rule in the knowledge graph"""

    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S%f"))
    rule_text: str = ""
    category: str = "general"  # e.g., "validation", "formatting", "safety"

    # Hierarchy
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)

    # Relationships
    supersedes_ids: List[str] = field(default_factory=list)  # Rules this replaces
    superseded_by_id: Optional[str] = None  # Rule that replaces this
    related_ids: List[str] = field(default_factory=list)  # Related rules

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    confidence: float = 1.0
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    # Multi-tenant support
    tenant_id: str = "default"

    # Tags and search
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher is more important
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "rule_text": self.rule_text,
            "category": self.category,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "supersedes_ids": self.supersedes_ids,
            "superseded_by_id": self.superseded_by_id,
            "related_ids": self.related_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "tenant_id": self.tenant_id,
            "tags": self.tags,
            "priority": self.priority,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleNode":
        """Create from dictionary"""
        return cls(**data)

    def get_effectiveness_score(self) -> float:
        """Calculate effectiveness score based on usage statistics"""
        total_usage = self.usage_count
        if total_usage == 0:
            return 0.5  # Neutral score for unused rules

        success_rate = self.success_count / total_usage
        # Weight by confidence and priority
        effectiveness = (
            success_rate * 0.6 + self.confidence * 0.3 + (self.priority / 10) * 0.1
        )
        return min(1.0, max(0.0, effectiveness))


class RuleGraph:
    """Knowledge graph for managing hierarchical rules"""

    def __init__(self, config=None, storage_path: Optional[Path] = None):
        """
        Initialize the rule graph

        Args:
            config: SystemConfig instance
            storage_path: Path to store the graph JSON
        """
        self.config = config
        self.storage_path = storage_path or Path("rule_graph.json")
        self.nodes: Dict[str, RuleNode] = {}
        self.root_node_ids: Set[str] = set()

        # Load existing graph if available
        if self.storage_path.exists():
            self.load()

    def add_rule(
        self,
        rule_text: str,
        category: str = "general",
        parent_id: Optional[str] = None,
        supersedes_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        priority: int = 5,
        tenant_id: str = "default",
    ) -> RuleNode:
        """
        Add a new rule to the graph

        Args:
            rule_text: The rule content
            category: Rule category
            parent_id: Parent rule ID for hierarchy
            supersedes_ids: IDs of rules this supersedes
            tags: Tags for searching/categorization
            priority: Priority level (1-10)
            tenant_id: Tenant identifier

        Returns:
            The created RuleNode
        """
        node = RuleNode(
            rule_text=rule_text,
            category=category,
            parent_id=parent_id,
            supersedes_ids=supersedes_ids or [],
            tags=tags or [],
            priority=priority,
            tenant_id=tenant_id,
        )

        self.nodes[node.id] = node

        # Update parent's children list
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].child_ids.append(node.id)
        else:
            # Root node
            self.root_node_ids.add(node.id)

        # Handle supersession
        if supersedes_ids:
            for old_id in supersedes_ids:
                if old_id in self.nodes:
                    self.nodes[old_id].superseded_by_id = node.id
                    self.nodes[old_id].is_active = False

        self.save()
        return node

    def get_rule(self, rule_id: str) -> Optional[RuleNode]:
        """Get a rule by ID"""
        return self.nodes.get(rule_id)

    def get_active_rules(self, tenant_id: Optional[str] = None) -> List[RuleNode]:
        """Get all active rules, optionally filtered by tenant"""
        rules = [node for node in self.nodes.values() if node.is_active]
        if tenant_id:
            rules = [r for r in rules if r.tenant_id == tenant_id]
        return rules

    def get_rules_by_category(
        self, category: str, tenant_id: Optional[str] = None
    ) -> List[RuleNode]:
        """Get all active rules in a category"""
        rules = self.get_active_rules(tenant_id)
        return [r for r in rules if r.category == category]

    def get_children(self, rule_id: str) -> List[RuleNode]:
        """Get all child rules of a given rule"""
        node = self.nodes.get(rule_id)
        if not node:
            return []
        return [
            self.nodes[child_id]
            for child_id in node.child_ids
            if child_id in self.nodes
        ]

    def get_ancestors(self, rule_id: str) -> List[RuleNode]:
        """Get all ancestor rules (parent chain)"""
        ancestors = []
        current_id = rule_id

        while current_id:
            node = self.nodes.get(current_id)
            if not node or not node.parent_id:
                break
            parent = self.nodes.get(node.parent_id)
            if parent:
                ancestors.append(parent)
                current_id = parent.id
            else:
                break

        return ancestors

    def get_inherited_rules(self, rule_id: str) -> List[RuleNode]:
        """Get all rules inherited from ancestors"""
        if not self.config or not self.config.enable_rule_inheritance:
            return []

        ancestors = self.get_ancestors(rule_id)
        # Filter to only active rules
        return [a for a in ancestors if a.is_active]

    def update_rule_stats(
        self, rule_id: str, success: bool = True, increment_usage: bool = True
    ):
        """Update usage statistics for a rule"""
        node = self.nodes.get(rule_id)
        if not node:
            return

        if increment_usage:
            node.usage_count += 1

        if success:
            node.success_count += 1
        else:
            node.failure_count += 1

        node.updated_at = datetime.now().isoformat()
        self.save()

    def supersede_rule(
        self, old_rule_id: str, new_rule_text: str, **kwargs
    ) -> RuleNode:
        """Create a new rule that supersedes an old one"""
        old_node = self.nodes.get(old_rule_id)
        if not old_node:
            raise ValueError(f"Rule {old_rule_id} not found")

        # Prepare defaults from old node, but allow overrides from kwargs
        defaults = {
            "category": old_node.category,
            "parent_id": old_node.parent_id,
            "tags": old_node.tags,
            "priority": old_node.priority,
            "tenant_id": old_node.tenant_id,
        }

        # Override with any provided kwargs
        defaults.update(kwargs)

        # Create new rule with supersession
        new_node = self.add_rule(
            rule_text=new_rule_text, supersedes_ids=[old_rule_id], **defaults
        )

        return new_node

    def find_conflicts(
        self, rule_text: str, tenant_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Find potential conflicts with existing rules

        Args:
            rule_text: New rule text to check
            tenant_id: Tenant context

        Returns:
            List of potential conflicts with details
        """
        conflicts = []
        active_rules = self.get_active_rules(tenant_id)

        # Simple text-based conflict detection
        # In a real implementation, this would use semantic similarity
        rule_lower = rule_text.lower()

        for node in active_rules:
            node_lower = node.rule_text.lower()

            # Check for contradictions (simple keyword-based)
            # e.g., "always use X" vs "never use X"
            if "always" in rule_lower and "never" in node_lower:
                conflicts.append(
                    {
                        "rule_id": node.id,
                        "rule_text": node.rule_text,
                        "conflict_type": "contradiction",
                        "severity": "high",
                    }
                )
            elif "never" in rule_lower and "always" in node_lower:
                conflicts.append(
                    {
                        "rule_id": node.id,
                        "rule_text": node.rule_text,
                        "conflict_type": "contradiction",
                        "severity": "high",
                    }
                )

        return conflicts

    def get_rule_hierarchy(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the complete rule hierarchy as a tree structure"""

        def build_tree(node_id: str) -> Dict[str, Any]:
            node = self.nodes.get(node_id)
            if not node:
                return {}

            return {
                "id": node.id,
                "rule_text": node.rule_text,
                "category": node.category,
                "priority": node.priority,
                "is_active": node.is_active,
                "effectiveness": node.get_effectiveness_score(),
                "children": [build_tree(child_id) for child_id in node.child_ids],
            }

        # Get root nodes
        roots = self.root_node_ids
        if tenant_id:
            roots = {
                rid
                for rid in roots
                if self.nodes.get(rid) and self.nodes[rid].tenant_id == tenant_id
            }

        return {
            "roots": [build_tree(root_id) for root_id in roots],
            "total_nodes": len(self.nodes),
            "active_nodes": len(self.get_active_rules(tenant_id)),
        }

    def save(self):
        """Save the graph to storage"""
        data = {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "root_node_ids": list(self.root_node_ids),
            "saved_at": datetime.now().isoformat(),
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load the graph from storage"""
        if not self.storage_path.exists():
            return

        with open(self.storage_path, "r") as f:
            data = json.load(f)

        self.nodes = {
            node_id: RuleNode.from_dict(node_data)
            for node_id, node_data in data.get("nodes", {}).items()
        }
        self.root_node_ids = set(data.get("root_node_ids", []))

    def migrate_from_markdown(
        self, markdown_content: str, tenant_id: str = "default"
    ) -> int:
        """
        Migrate rules from markdown format to knowledge graph

        Args:
            markdown_content: Markdown content with rules
            tenant_id: Tenant identifier

        Returns:
            Number of rules migrated
        """
        # Simple parser for markdown rules
        # Assumes rules are in list format with categories as headers
        lines = markdown_content.split("\n")
        current_category = "general"
        migrated_count = 0

        for line in lines:
            line = line.strip()

            # Check for category headers (##)
            if line.startswith("##") and not line.startswith("###"):
                current_category = line.replace("#", "").strip().lower()

            # Check for rule items (-)
            elif line.startswith("- ") or line.startswith("* "):
                rule_text = line[2:].strip()
                if rule_text:
                    self.add_rule(
                        rule_text=rule_text,
                        category=current_category,
                        tenant_id=tenant_id,
                    )
                    migrated_count += 1

        return migrated_count


class MockRuleGraph(RuleGraph):
    """Mock rule graph for testing without actual storage"""

    def save(self):
        """Override save to do nothing in tests"""
        pass

    def load(self):
        """Override load to do nothing in tests"""
        pass
