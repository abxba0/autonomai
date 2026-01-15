# Implicit Negative Feedback and Context-Based Rule Extraction

This document describes the implicit feedback detection and context-based rule extraction features in the Self-Optimizing Instruction Library.

## Table of Contents

- [Overview](#overview)
- [Implicit Negative Feedback (Correction Detector)](#implicit-negative-feedback-correction-detector)
- [Context-Based Rule Extraction (/feedback-context)](#context-based-rule-extraction-feedback-context)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)

## Overview

These features enable the system to learn from user interactions in two powerful ways:

1. **Implicit Negative Feedback**: Automatically detects when users correct or express dissatisfaction with AI responses, even without explicit feedback commands.

2. **Context-Based Rule Extraction**: Analyzes conversation history to extract patterns, preferences, and recurring feedback, proposing new rules automatically.

Both features integrate seamlessly with the existing optimization pipeline, logging failures and triggering instruction updates when appropriate.

## Implicit Negative Feedback (Correction Detector)

### What It Does

The Correction Detector monitors user messages for implicit signs of correction or dissatisfaction, such as:

- Direct negations: "No, that's not correct", "That's wrong"
- Explicit error statements: "You're mistaken", "That's incorrect"
- Dissatisfaction expressions: "That doesn't make sense", "This is not what I wanted"
- Correction requests: "Can you fix that?", "Please correct this"
- Repeated queries (potential dissatisfaction)

When detected, the system:
1. Logs the correction as an `implicit_feedback` failure entry
2. Triggers the optimization pipeline (if auto-optimization is enabled)
3. Updates instructions to prevent similar issues

### How It Works

The detector uses heuristic pattern matching with confidence scoring:

```python
from src.core.correction_detector import CorrectionDetector

detector = CorrectionDetector(confidence_threshold=0.7)

# Detect correction in a message
is_correction, confidence, correction_type = detector.detect_correction(
    user_message="No, that's not right",
    previous_response="The answer is 42",
    conversation_history=conversation_history
)

if is_correction:
    print(f"Correction detected! Type: {correction_type}, Confidence: {confidence:.2f}")
```

### Detection Patterns

The detector recognizes several types of corrections:

| Type | Examples | Base Confidence |
|------|----------|----------------|
| Direct Negation | "No, that's not correct" | 0.90 |
| Explicit Error | "You're wrong", "That's incorrect" | 0.90-0.95 |
| Dissatisfaction | "That doesn't help", "Not what I wanted" | 0.75-0.80 |
| Correction Request | "Can you fix this?", "Please correct" | 0.75 |
| Repeated Query | Same question asked twice | 0.60 |

### Configuration

Enable/disable correction detection in SystemConfig:

```python
from src import SystemConfig

config = SystemConfig(
    enable_correction_detection=True,  # Enable implicit correction detection
    correction_detection_confidence_threshold=0.7,  # Minimum confidence to trigger
)
```

### Integration

Correction detection is automatically integrated into the MainModel execution flow:

```python
from src import SelfOptimizingSystem

system = SelfOptimizingSystem(config)
result = system.execute("No, that's not what I asked for")

if result.get("correction_detected"):
    print(f"Correction detected with confidence: {result['correction_confidence']:.2f}")
    if result.get("optimization_attempted"):
        print("System is learning from your correction!")
```

## Context-Based Rule Extraction (/feedback-context)

### What It Does

The Context Analyzer examines conversation history to extract:

1. **Positive Rules (DO)**: User preferences and desired behaviors
   - "I prefer concise answers" → Rule: "provide concise responses"
   - "Always include examples" → Rule: "include examples in explanations"

2. **Negative Rules (DON'T)**: Behaviors to avoid
   - "Don't use technical jargon" → Rule: "DON'T use technical jargon"
   - "Avoid lengthy responses" → Rule: "DON'T provide overly long responses"

3. **Patterns**: Recurring issues or behaviors
   - Repeated corrections about response length
   - Consistent preference for specific formats

### How It Works

The analyzer can operate in two modes:

1. **Heuristic Mode**: Uses regex patterns to extract rules (fast, works offline)
2. **LLM-Enhanced Mode**: Uses the critic model for deeper semantic analysis (optional)

```python
from src import SelfOptimizingSystem

system = SelfOptimizingSystem()

# Analyze conversation and extract rules
result = system.analyze_feedback_context(
    conversation_history=conversation_history,
    focus_recent=10,  # Analyze last 10 messages
    min_confidence=0.6,  # Minimum confidence threshold
    auto_apply=False  # Don't auto-apply, let user review first
)

if result["success"]:
    print(result["formatted_display"])  # Show extracted rules
    print(f"Found {result['rules_count']} positive rules")
    print(f"Found {result['dont_rules_count']} negative rules")
```

### Usage in Terminal Chatbot

Use the `/feedback-context` command:

```
You: /feedback-context

🔍 Analyzing conversation context...

============================================================
📊 CONVERSATION CONTEXT ANALYSIS
============================================================

Analyzed 8 user messages
Timestamp: 2025-01-14T12:34:56

============================================================
✅ POSITIVE RULES (DO)
============================================================

1. concise answers
   Type: positive_preference
   Confidence: 0.80
   Source: I prefer concise answers...

2. always include examples
   Type: positive_request
   Confidence: 0.80
   Source: Please always include examples...

============================================================
⛔ NEGATIVE RULES (DON'T)
============================================================

1. use technical jargon
   Type: negative_rule
   Confidence: 0.80
   Source: Don't use technical jargon...

============================================================

💡 Apply these rules to system instructions? (y/n): y
```

### Usage in Web API

POST to `/feedback-context` endpoint:

```bash
curl -X POST http://localhost:8000/feedback-context \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_history": [
      {"role": "user", "content": "I prefer concise answers"},
      {"role": "assistant", "content": "Understood."},
      {"role": "user", "content": "Don'\''t use jargon"}
    ],
    "focus_recent": 10,
    "min_confidence": 0.6,
    "auto_apply": false
  }'
```

Response:

```json
{
  "success": true,
  "message": "Extracted 1 positive rules and 1 negative rules",
  "rules_count": 1,
  "dont_rules_count": 1,
  "patterns_count": 0,
  "formatted_display": "...",
  "instruction_updates": "## Context-Based Instruction Updates\n...",
  "auto_apply_result": null
}
```

## Configuration

### System Configuration

```python
from src import SystemConfig

config = SystemConfig(
    # Correction Detection
    enable_correction_detection=True,
    correction_detection_confidence_threshold=0.7,
    
    # Auto-Optimization (affects both features)
    enable_auto_optimization=True,
    max_optimization_attempts=3,
)
```

### Context Analyzer Configuration

```python
# When creating the system
system = SelfOptimizingSystem(config)

# Analyze with custom settings
result = system.analyze_feedback_context(
    conversation_history=history,
    focus_recent=10,  # Number of recent messages to focus on
    min_confidence=0.6,  # Minimum confidence for rule extraction
    auto_apply=False  # Whether to automatically apply rules
)
```

## Usage Examples

### Example 1: Detecting Implicit Corrections

```python
from src import SelfOptimizingSystem, SystemConfig

config = SystemConfig(
    enable_correction_detection=True,
    enable_auto_optimization=True
)
system = SelfOptimizingSystem(config)

# First interaction
result1 = system.execute("What is 2+2?")
print(result1["output"])  # "The answer is 5"

# User corrects implicitly
result2 = system.execute("No, that's wrong. 2+2 is 4.")

if result2.get("correction_detected"):
    print("Correction detected! System is learning...")
    # The system will log this as implicit feedback
    # and attempt to optimize instructions
```

### Example 2: Extracting Rules from Conversation

```python
# After a conversation, analyze it
conversation = [
    {"role": "user", "content": "Please be more concise"},
    {"role": "assistant", "content": "OK"},
    {"role": "user", "content": "Don't use complex words"},
    {"role": "assistant", "content": "Got it"},
]

result = system.analyze_feedback_context(
    conversation,
    auto_apply=True  # Automatically apply extracted rules
)

print(f"Extracted {result['rules_count']} rules")
if result.get("auto_apply_result", {}).get("success"):
    print("Rules applied successfully!")
```

### Example 3: Using Both Features Together

```python
# Start a conversation
conversation_history = []

# User query
conversation_history.append({"role": "user", "content": "Explain quantum physics"})
result = system.execute("Explain quantum physics", conversation_history)
conversation_history.append({"role": "assistant", "content": result["output"]})

# User implicitly corrects (detected automatically)
conversation_history.append({"role": "user", "content": "That's too technical, simplify it"})
result = system.execute(
    "That's too technical, simplify it",
    conversation_history
)
# Correction detected! confidence: 0.75

# Later, extract patterns
analysis = system.analyze_feedback_context(conversation_history)
# Finds pattern: User prefers simplified explanations
# Proposes rule: "DON'T use overly technical language"
```

## API Reference

### CorrectionDetector

```python
class CorrectionDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize detector with confidence threshold"""
        
    def detect_correction(
        self,
        user_message: str,
        previous_response: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Detect implicit correction in user message
        
        Returns:
            (is_correction, confidence, correction_type)
        """
```

### ContextAnalyzer

```python
class ContextAnalyzer:
    def __init__(self, use_llm: bool = False, llm_model=None):
        """Initialize analyzer with optional LLM support"""
        
    def analyze_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        focus_recent: int = 10,
        min_confidence: float = 0.6
    ) -> Dict[str, Any]:
        """
        Analyze conversation to extract rules
        
        Returns dict with:
            - success: bool
            - rules: List[Dict] - Positive rules
            - dont_rules: List[Dict] - Negative rules
            - patterns: List[Dict] - Detected patterns
        """
```

### SelfOptimizingSystem Methods

```python
class SelfOptimizingSystem:
    def analyze_feedback_context(
        self,
        conversation_history: List[Dict[str, str]],
        focus_recent: int = 10,
        min_confidence: float = 0.6,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze conversation context and extract rules
        
        Implements /feedback-context functionality
        """
```

## Best Practices

1. **Correction Detection**:
   - Start with default threshold (0.7) and adjust based on false positive/negative rates
   - Monitor failure logs to see what corrections are being detected
   - Use conversation context when available for better accuracy

2. **Context Analysis**:
   - Analyze after 5-10 messages for meaningful patterns
   - Review extracted rules before auto-applying
   - Use higher confidence thresholds (0.7-0.8) for auto-apply
   - Lower confidence (0.5-0.6) when reviewing manually

3. **Integration**:
   - Enable both features together for comprehensive learning
   - Regularly review failure logs and version history
   - Use rollback if incorrectly learned rules cause issues

## Troubleshooting

**Q: Correction detection triggering too often (false positives)?**
- Increase `correction_detection_confidence_threshold` to 0.8 or 0.9
- Check failure logs to identify problematic patterns
- Consider disabling if not needed

**Q: Context analyzer extracting too few rules?**
- Lower `min_confidence` to 0.5 or 0.6
- Ensure conversation has explicit preferences ("I prefer...", "Don't...")
- Try using longer conversation history (`focus_recent=20`)

**Q: Extracted rules are not being applied?**
- Ensure `enable_auto_optimization=True` in config
- Check if rules are being added to pending review
- Review critic model logs for optimization failures

**Q: How to disable these features?**
```python
config = SystemConfig(
    enable_correction_detection=False,  # Disable implicit feedback
    enable_auto_optimization=False,     # Disable automatic rule application
)
```

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [Usage Guide](usage-guide.md) - General usage information
- [API Reference](api-reference.md) - Complete API documentation
- [Contributing](contributing.md) - How to contribute
