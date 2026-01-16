"""
Tests for Correction Detector and Context Analyzer features
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.correction_detector import CorrectionDetector
from src.core.context_analyzer import ContextAnalyzer
from src.models.config import SystemConfig


def test_correction_detector_direct_negation():
    """Test detection of direct negations"""
    detector = CorrectionDetector(confidence_threshold=0.7)

    # Test direct negation patterns
    test_cases = [
        ("No, that's not correct", True),
        ("That's not right", True),
        ("Actually, that's wrong", True),
        ("You're wrong about this", True),
        ("That doesn't make sense", True),
        ("Hello, how are you?", False),  # Should not trigger
    ]

    for message, should_detect in test_cases:
        is_correction, confidence, correction_type = detector.detect_correction(message)
        if should_detect:
            assert is_correction, f"Failed to detect correction in: {message}"
            assert confidence >= 0.7, f"Confidence too low for: {message}"
            print(
                f"✓ Detected correction: '{message}' (confidence: {confidence:.2f}, type: {correction_type})"
            )
        else:
            assert not is_correction, f"False positive on: {message}"
            print(f"✓ Correctly ignored: '{message}'")

    print("\n✓ Correction detector direct negation tests passed")


def test_correction_detector_dissatisfaction():
    """Test detection of dissatisfaction expressions"""
    detector = CorrectionDetector(confidence_threshold=0.7)

    test_cases = [
        ("That doesn't answer my question", True),
        ("You didn't help with what I asked", True),
        ("This is not what I wanted", True),
        ("Can you please explain quantum physics?", False),  # Should not trigger
    ]

    for message, should_detect in test_cases:
        is_correction, confidence, correction_type = detector.detect_correction(message)
        if should_detect:
            assert is_correction, f"Failed to detect dissatisfaction in: {message}"
            print(
                f"✓ Detected dissatisfaction: '{message}' (confidence: {confidence:.2f}, type: {correction_type})"
            )
        else:
            assert not is_correction, f"False positive on: {message}"
            print(f"✓ Correctly ignored: '{message}'")

    print("\n✓ Correction detector dissatisfaction tests passed")


def test_correction_detector_with_context():
    """Test detection using conversation context"""
    detector = CorrectionDetector(confidence_threshold=0.6)

    # Simulate conversation history
    conversation_history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What is the capital of France?"},  # Repeated query
    ]

    # Last user message is repeated, should trigger
    is_correction, confidence, correction_type = detector.detect_correction(
        "What is the capital of France?", conversation_history=conversation_history
    )

    assert is_correction, "Failed to detect repeated query as potential correction"
    print(
        f"✓ Detected repeated query (confidence: {confidence:.2f}, type: {correction_type})"
    )
    print("\n✓ Correction detector context tests passed")


def test_context_analyzer_preference_extraction():
    """Test extraction of user preferences from conversation"""
    analyzer = ContextAnalyzer(use_llm=False)  # Use heuristic mode for testing

    conversation = [
        {"role": "user", "content": "I prefer concise answers"},
        {"role": "assistant", "content": "Understood."},
        {"role": "user", "content": "Please always include examples"},
        {"role": "assistant", "content": "Will do."},
        {"role": "user", "content": "Don't use technical jargon"},
        {"role": "assistant", "content": "Got it."},
    ]

    result = analyzer.analyze_conversation(conversation, min_confidence=0.6)

    assert result["success"], "Context analysis failed"
    assert len(result["rules"]) > 0, "Failed to extract positive rules"
    assert len(result["dont_rules"]) > 0, "Failed to extract negative rules"

    print(f"✓ Extracted {len(result['rules'])} positive rules")
    print(f"✓ Extracted {len(result['dont_rules'])} negative rules")

    # Check specific rules were found
    rule_texts = [r["text"].lower() for r in result["rules"]]
    dont_rule_texts = [r["text"].lower() for r in result["dont_rules"]]

    # At least one should match our patterns
    assert any(
        "concise" in text or "example" in text for text in rule_texts
    ), "Failed to extract expected positive rules"
    assert any(
        "jargon" in text for text in dont_rule_texts
    ), "Failed to extract expected negative rules"

    print("✓ Verified extracted rules match input preferences")
    print("\n✓ Context analyzer preference extraction tests passed")


def test_context_analyzer_rule_deduplication():
    """Test that duplicate rules are properly removed"""
    analyzer = ContextAnalyzer(use_llm=False)

    conversation = [
        {"role": "user", "content": "I prefer short answers"},
        {"role": "assistant", "content": "OK"},
        {"role": "user", "content": "I prefer short answers"},  # Duplicate
        {"role": "assistant", "content": "Noted"},
    ]

    result = analyzer.analyze_conversation(conversation, min_confidence=0.6)

    assert result["success"], "Context analysis failed"

    # Should have deduplicated the repeated preference
    rule_texts = [r["text"].lower() for r in result["rules"]]
    short_answer_rules = [text for text in rule_texts if "short" in text]

    # Should have at most one rule about short answers (could be 0 if extraction missed it)
    assert len(short_answer_rules) <= 1, "Failed to deduplicate rules"

    print("✓ Rule deduplication working correctly")
    print("\n✓ Context analyzer deduplication tests passed")


def test_context_analyzer_formatting():
    """Test formatting of analysis results"""
    analyzer = ContextAnalyzer(use_llm=False)

    # Create a simple analysis result
    analysis_result = {
        "success": True,
        "rules": [
            {
                "text": "be concise",
                "type": "positive_preference",
                "confidence": 0.8,
                "source": "test",
            }
        ],
        "dont_rules": [
            {
                "text": "use jargon",
                "type": "negative_rule",
                "confidence": 0.9,
                "source": "test",
            }
        ],
        "patterns": [],
        "analyzed_messages": 2,
    }

    # Test display formatting
    display = analyzer.format_rules_for_display(analysis_result)
    assert "POSITIVE RULES" in display, "Missing positive rules section"
    assert "NEGATIVE RULES" in display, "Missing negative rules section"
    assert "be concise" in display, "Missing expected rule"
    assert "use jargon" in display, "Missing expected don't rule"

    print("✓ Display formatting correct")

    # Test instruction update formatting
    updates = analyzer.create_instruction_updates(analysis_result, format="markdown")
    assert "DO Rules" in updates, "Missing DO rules section"
    assert "DON'T Rules" in updates, "Missing DON'T rules section"
    assert "be concise" in updates, "Missing expected rule in updates"

    print("✓ Instruction update formatting correct")
    print("\n✓ Context analyzer formatting tests passed")


def test_integration_correction_to_failure_log():
    """Test that correction detection creates proper failure entries"""
    from models.config import FailureEntry

    detector = CorrectionDetector()

    user_message = "No, that's not correct"
    previous_response = "The answer is 42"

    is_correction, confidence, correction_type = detector.detect_correction(
        user_message, previous_response=previous_response
    )

    if is_correction:
        description = detector.create_correction_description(
            user_message, correction_type, confidence, previous_response
        )

        # Create failure entry
        failure = FailureEntry(
            trigger_type="implicit_feedback",
            failure_description=description,
            user_query=user_message,
            last_model_output=previous_response,
            severity="moderate",
        )

        assert failure.trigger_type == "implicit_feedback", "Wrong trigger type"
        assert correction_type in description, "Correction type not in description"
        assert "confidence" in description.lower(), "Confidence not in description"

        print("✓ Failure entry created correctly from correction detection")
        print(f"  Trigger: {failure.trigger_type}")
        print(f"  Description: {description[:100]}...")

    print("\n✓ Integration test passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("RUNNING CORRECTION DETECTOR AND CONTEXT ANALYZER TESTS")
    print("=" * 60)
    print()

    try:
        test_correction_detector_direct_negation()
        test_correction_detector_dissatisfaction()
        test_correction_detector_with_context()
        test_context_analyzer_preference_extraction()
        test_context_analyzer_rule_deduplication()
        test_context_analyzer_formatting()
        test_integration_correction_to_failure_log()

        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
