"""
Context Analyzer Module

Analyzes conversation history to extract patterns, user desires, and recurring feedback
to propose new rules and "DON'T" rules (negative instructions) for the system.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class ContextAnalyzer:
    """Analyzes conversation context to extract rules and patterns"""

    # Configuration constants
    MIN_RULE_TEXT_LENGTH = 5  # Minimum length for extracted rule text

    def __init__(self, use_llm: bool = False, llm_model=None):
        """
        Initialize the context analyzer

        Args:
            use_llm: Whether to use LLM for deeper analysis (optional)
            llm_model: LLM model instance for advanced analysis
        """
        self.use_llm = use_llm
        self.llm_model = llm_model

        # Patterns for extracting preferences and rules
        self.preference_patterns = [
            # Explicit preferences
            (
                r"\bI (?:prefer|like|want|need)\s+(?:you to\s+)?([^.!?]+)",
                "positive_preference",
            ),
            (r"\bplease\s+(?:always\s+)?([^.!?]+)", "positive_request"),
            (r"\bmake sure\s+(?:to\s+)?([^.!?]+)", "positive_instruction"),
            (r"\balways\s+([^.!?]+)", "positive_rule"),
            # Negative preferences (DON'T rules)
            (r"\bdon\'?t\s+([^.!?]+)", "negative_rule"),
            (r"\bavoid\s+([^.!?]+)", "negative_rule"),
            (r"\bnever\s+([^.!?]+)", "negative_rule"),
            (r"\bstop\s+([^.!?]+)", "negative_rule"),
            (
                r"\bI (?:don\'?t|do not)\s+(?:like|want|need)\s+(?:you to\s+)?([^.!?]+)",
                "negative_preference",
            ),
            # Style preferences
            (
                r"\b(?:be more|be less|should be)\s+(concise|detailed|formal|casual|technical|simple)",
                "style_preference",
            ),
            (
                r"\b(?:keep|make) (?:it|responses?)\s+(short|brief|concise|detailed|simple)",
                "style_preference",
            ),
        ]

        # Patterns for detecting recurring issues
        self.issue_patterns = [
            (r"\byou (?:keep|always|often)\s+([^.!?]+)", "recurring_behavior"),
            (r"\bevery time\s+([^.!?]+)", "recurring_issue"),
            (r"\bagain\s*,?\s*([^.!?]+)", "repetition"),
        ]

    def analyze_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        focus_recent: int = 10,
        min_confidence: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Analyze conversation history to extract rules and patterns

        Args:
            conversation_history: List of conversation messages
            focus_recent: Number of recent messages to focus on
            min_confidence: Minimum confidence for rule extraction

        Returns:
            Dict containing extracted rules, patterns, and analysis
        """
        if not conversation_history:
            return {
                "success": False,
                "message": "No conversation history available",
                "rules": [],
                "dont_rules": [],
                "patterns": [],
            }

        # Focus on recent messages
        recent_messages = (
            conversation_history[-focus_recent:]
            if len(conversation_history) > focus_recent
            else conversation_history
        )

        # Extract rules from user messages
        user_messages = [msg for msg in recent_messages if msg.get("role") == "user"]

        positive_rules = []
        negative_rules = []
        patterns = []

        # Extract preferences and rules
        for msg in user_messages:
            content = msg.get("content", "")

            # Check preference patterns
            for pattern, rule_type in self.preference_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    rule_text = match.strip()
                    if (
                        len(rule_text) > self.MIN_RULE_TEXT_LENGTH
                    ):  # Filter out too short matches
                        rule = {
                            "text": rule_text,
                            "type": rule_type,
                            "confidence": 0.8,
                            "source": content[:100],
                        }

                        if "negative" in rule_type or "don't" in rule_type.lower():
                            negative_rules.append(rule)
                        else:
                            positive_rules.append(rule)

            # Check for recurring issues
            for pattern, issue_type in self.issue_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    patterns.append(
                        {
                            "type": issue_type,
                            "description": match.strip(),
                            "confidence": 0.7,
                        }
                    )

        # Deduplicate rules
        positive_rules = self._deduplicate_rules(positive_rules)
        negative_rules = self._deduplicate_rules(negative_rules)

        # Filter by confidence
        positive_rules = [
            r for r in positive_rules if r["confidence"] >= min_confidence
        ]
        negative_rules = [
            r for r in negative_rules if r["confidence"] >= min_confidence
        ]

        # If LLM is available, use it for deeper analysis
        if self.use_llm and self.llm_model:
            enhanced_analysis = self._llm_enhanced_analysis(
                conversation_history, positive_rules, negative_rules, patterns
            )
            if enhanced_analysis:
                return enhanced_analysis

        return {
            "success": True,
            "message": f"Extracted {len(positive_rules)} positive rules and {len(negative_rules)} negative rules",
            "rules": positive_rules,
            "dont_rules": negative_rules,
            "patterns": patterns,
            "timestamp": datetime.now().isoformat(),
            "analyzed_messages": len(user_messages),
        }

    def _deduplicate_rules(self, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar rules"""
        if not rules:
            return []

        unique_rules = []
        seen_texts = set()

        for rule in rules:
            text_lower = rule["text"].lower().strip()
            # Simple deduplication - more sophisticated semantic similarity could be used
            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_rules.append(rule)

        return unique_rules

    def _llm_enhanced_analysis(
        self,
        conversation_history: List[Dict[str, str]],
        positive_rules: List[Dict[str, Any]],
        negative_rules: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to enhance rule extraction with deeper semantic understanding

        This is an optional feature for more sophisticated analysis
        """
        try:
            # Build prompt for LLM
            conversation_text = self._format_conversation_for_llm(
                conversation_history[-20:]
            )

            prompt = f"""Analyze the following conversation history and extract:
1. Clear, actionable rules the AI should follow (DO rules)
2. Clear, actionable rules the AI should avoid (DON'T rules)
3. Recurring patterns or user preferences

Focus on user feedback, corrections, and explicit preferences.

Conversation:
{conversation_text}

Provide your analysis in JSON format:
{{
    "positive_rules": [
        {{"rule": "...", "confidence": 0.9, "justification": "..."}},
        ...
    ],
    "negative_rules": [
        {{"rule": "...", "confidence": 0.9, "justification": "..."}},
        ...
    ],
    "patterns": [
        {{"pattern": "...", "impact": "..."}},
        ...
    ]
}}
"""

            # Call LLM
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                messages = [
                    SystemMessage(
                        content="You are an expert at analyzing conversations to extract actionable rules and patterns."
                    ),
                    HumanMessage(content=prompt),
                ]

                response = self.llm_model.invoke(messages)
                response_text = response.content
            except ImportError:
                # If langchain is not available, use simple format
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing conversations to extract actionable rules and patterns.",
                    },
                    {"role": "user", "content": prompt},
                ]
                response = self.llm_model.invoke(messages)
                response_text = response.content

            # Parse LLM response
            import json

            # Clean potential markdown formatting
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            llm_analysis = json.loads(clean_text.strip())

            # Merge with heuristic-based rules
            all_positive = positive_rules + [
                {
                    "text": r["rule"],
                    "type": "llm_extracted",
                    "confidence": r.get("confidence", 0.8),
                    "source": r.get("justification", "LLM analysis"),
                }
                for r in llm_analysis.get("positive_rules", [])
            ]

            all_negative = negative_rules + [
                {
                    "text": r["rule"],
                    "type": "llm_extracted_negative",
                    "confidence": r.get("confidence", 0.8),
                    "source": r.get("justification", "LLM analysis"),
                }
                for r in llm_analysis.get("negative_rules", [])
            ]

            all_patterns = patterns + llm_analysis.get("patterns", [])

            return {
                "success": True,
                "message": f"LLM-enhanced analysis: {len(all_positive)} positive rules, {len(all_negative)} negative rules",
                "rules": self._deduplicate_rules(all_positive),
                "dont_rules": self._deduplicate_rules(all_negative),
                "patterns": all_patterns,
                "timestamp": datetime.now().isoformat(),
                "analyzed_messages": len(conversation_history),
                "analysis_method": "llm_enhanced",
            }

        except Exception as e:
            print(
                f"LLM-enhanced analysis failed: {e}. Falling back to heuristic-based analysis."
            )
            return None

    def _format_conversation_for_llm(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages for LLM prompt"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")
        return "\n\n".join(formatted)

    def format_rules_for_display(self, analysis_result: Dict[str, Any]) -> str:
        """
        Format extracted rules in a human-readable format

        Args:
            analysis_result: Result from analyze_conversation

        Returns:
            Formatted string for display
        """
        if not analysis_result.get("success"):
            return f"Analysis failed: {analysis_result.get('message', 'Unknown error')}"

        output = []
        output.append("=" * 60)
        output.append("📊 CONVERSATION CONTEXT ANALYSIS")
        output.append("=" * 60)
        output.append(
            f"\nAnalyzed {analysis_result.get('analyzed_messages', 0)} user messages"
        )
        output.append(f"Timestamp: {analysis_result.get('timestamp', 'N/A')}")

        # Positive rules
        rules = analysis_result.get("rules", [])
        if rules:
            output.append("\n" + "=" * 60)
            output.append("✅ POSITIVE RULES (DO)")
            output.append("=" * 60)
            for i, rule in enumerate(rules, 1):
                output.append(f"\n{i}. {rule['text']}")
                output.append(f"   Type: {rule['type']}")
                output.append(f"   Confidence: {rule['confidence']:.2f}")
                if rule.get("source"):
                    output.append(f"   Source: {rule['source'][:80]}...")

        # Negative rules
        dont_rules = analysis_result.get("dont_rules", [])
        if dont_rules:
            output.append("\n" + "=" * 60)
            output.append("⛔ NEGATIVE RULES (DON'T)")
            output.append("=" * 60)
            for i, rule in enumerate(dont_rules, 1):
                output.append(f"\n{i}. {rule['text']}")
                output.append(f"   Type: {rule['type']}")
                output.append(f"   Confidence: {rule['confidence']:.2f}")
                if rule.get("source"):
                    output.append(f"   Source: {rule['source'][:80]}...")

        # Patterns
        patterns = analysis_result.get("patterns", [])
        if patterns:
            output.append("\n" + "=" * 60)
            output.append("🔍 DETECTED PATTERNS")
            output.append("=" * 60)
            for i, pattern in enumerate(patterns, 1):
                output.append(
                    f"\n{i}. {pattern.get('type', 'Unknown')}: {pattern.get('description', 'N/A')}"
                )
                if pattern.get("confidence"):
                    output.append(f"   Confidence: {pattern['confidence']:.2f}")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    def create_instruction_updates(
        self, analysis_result: Dict[str, Any], format: str = "markdown"
    ) -> str:
        """
        Create formatted instruction updates from analysis results

        Args:
            analysis_result: Result from analyze_conversation
            format: Output format ("markdown" or "text")

        Returns:
            Formatted instruction updates ready to be added to system instructions
        """
        if not analysis_result.get("success"):
            return ""

        updates = []

        if format == "markdown":
            updates.append("## Context-Based Instruction Updates")
            updates.append(
                f"\n*Generated from conversation analysis on {analysis_result.get('timestamp', 'N/A')}*\n"
            )

            # Positive rules
            rules = analysis_result.get("rules", [])
            if rules:
                updates.append("### DO Rules")
                for rule in rules:
                    updates.append(
                        f"- **{rule['text']}** (confidence: {rule['confidence']:.2f})"
                    )

            # Negative rules
            dont_rules = analysis_result.get("dont_rules", [])
            if dont_rules:
                updates.append("\n### DON'T Rules")
                for rule in dont_rules:
                    updates.append(
                        f"- **DON'T {rule['text']}** (confidence: {rule['confidence']:.2f})"
                    )
        else:
            # Plain text format
            rules = analysis_result.get("rules", [])
            if rules:
                updates.append("DO Rules:")
                for rule in rules:
                    updates.append(f"- {rule['text']}")

            dont_rules = analysis_result.get("dont_rules", [])
            if dont_rules:
                updates.append("\nDON'T Rules:")
                for rule in dont_rules:
                    updates.append(f"- DON'T {rule['text']}")

        return "\n".join(updates)
