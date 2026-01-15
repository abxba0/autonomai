#!/usr/bin/env python3
"""
Demo script showing the new implicit feedback and context analysis features
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig


def demo_correction_detection():
    """Demonstrate implicit correction detection"""
    print("\n" + "=" * 60)
    print("DEMO 1: Implicit Correction Detection")
    print("=" * 60 + "\n")

    config = SystemConfig(
        enable_correction_detection=True,
        enable_auto_optimization=False,  # Disable auto-opt for faster demo
        main_model="mock",  # Use mock for demo
        critic_model="mock",
    )
    system = SelfOptimizingSystem(config)

    # Simulate a conversation
    print("User: What is the capital of France?")
    result1 = system.execute("What is the capital of France?")
    print(f"Bot: {result1['output'][:100]}...\n")

    # User corrects implicitly
    print("User: No, that's not correct. Paris is the capital.")
    result2 = system.execute("No, that's not correct. Paris is the capital.")

    if result2.get("correction_detected"):
        print(
            f"✅ Correction detected! (confidence: {result2['correction_confidence']:.2f})"
        )
        print("   The system recognized implicit negative feedback!")
        print("   (Auto-optimization disabled for demo)")
    else:
        print("❌ Correction not detected")

    print(f"\nBot: {result2['output'][:100]}...")


def demo_context_analysis():
    """Demonstrate context-based rule extraction"""
    print("\n" + "=" * 60)
    print("DEMO 2: Context-Based Rule Extraction")
    print("=" * 60 + "\n")

    config = SystemConfig(main_model="mock", critic_model="mock")
    system = SelfOptimizingSystem(config)

    # Simulate a conversation with clear preferences
    conversation = [
        {"role": "user", "content": "I prefer concise answers"},
        {"role": "assistant", "content": "Understood. I'll keep responses brief."},
        {
            "role": "user",
            "content": "Please always include examples when explaining concepts",
        },
        {"role": "assistant", "content": "Will do. I'll provide examples."},
        {"role": "user", "content": "Don't use technical jargon"},
        {"role": "assistant", "content": "Got it. I'll use simple language."},
        {"role": "user", "content": "Avoid lengthy explanations"},
        {"role": "assistant", "content": "Noted. I'll be concise."},
    ]

    print("Conversation:")
    for msg in conversation:
        role = "User" if msg["role"] == "user" else "Bot"
        print(f"  {role}: {msg['content']}")

    print("\n🔍 Analyzing conversation context...\n")

    result = system.analyze_feedback_context(
        conversation, focus_recent=10, min_confidence=0.6, auto_apply=False
    )

    if result["success"]:
        print("✅ Analysis successful!")
        print(f"   Found {result['rules_count']} positive rules (DO)")
        print(f"   Found {result['dont_rules_count']} negative rules (DON'T)")

        print("\n📋 Extracted Rules:")

        # Show positive rules
        if result["analysis"]["rules"]:
            print("\n  Positive Rules (DO):")
            for i, rule in enumerate(result["analysis"]["rules"], 1):
                print(f"    {i}. {rule['text']} (confidence: {rule['confidence']:.2f})")

        # Show negative rules
        if result["analysis"]["dont_rules"]:
            print("\n  Negative Rules (DON'T):")
            for i, rule in enumerate(result["analysis"]["dont_rules"], 1):
                print(f"    {i}. {rule['text']} (confidence: {rule['confidence']:.2f})")

        print("\n💡 These rules can be applied to improve future responses!")
    else:
        print(f"❌ Analysis failed: {result.get('message')}")


def demo_combined():
    """Demonstrate both features working together"""
    print("\n" + "=" * 60)
    print("DEMO 3: Combined Features - Natural Conversation Flow")
    print("=" * 60 + "\n")

    config = SystemConfig(
        enable_correction_detection=True,
        enable_auto_optimization=False,  # Disable for faster demo
        main_model="mock",
        critic_model="mock",
    )
    system = SelfOptimizingSystem(config)

    conversation_history = []

    # Interaction 1
    print("User: Explain machine learning")
    conversation_history.append({"role": "user", "content": "Explain machine learning"})
    result = system.execute("Explain machine learning", conversation_history)
    print(f"Bot: {result['output'][:80]}...\n")
    conversation_history.append({"role": "assistant", "content": result["output"]})

    # Interaction 2 - User prefers simpler
    print("User: That's too technical. Explain it more simply.")
    conversation_history.append(
        {"role": "user", "content": "That's too technical. Explain it more simply."}
    )
    result = system.execute(
        "That's too technical. Explain it more simply.", conversation_history
    )

    if result.get("correction_detected"):
        print(
            f"🔍 Implicit correction detected! (confidence: {result['correction_confidence']:.2f})"
        )

    print(f"Bot: {result['output'][:80]}...\n")
    conversation_history.append({"role": "assistant", "content": result["output"]})

    # Interaction 3 - Another preference
    print("User: Please always include real-world examples")
    conversation_history.append(
        {"role": "user", "content": "Please always include real-world examples"}
    )
    result = system.execute(
        "Please always include real-world examples", conversation_history
    )
    print(f"Bot: {result['output'][:80]}...\n")
    conversation_history.append({"role": "assistant", "content": result["output"]})

    # Now analyze the conversation
    print("--- Analyzing conversation for patterns ---\n")
    analysis = system.analyze_feedback_context(conversation_history, auto_apply=False)

    if analysis["success"]:
        print(
            f"✅ Found {analysis['rules_count']} positive and {analysis['dont_rules_count']} negative rules"
        )
        print(
            "   These preferences have been extracted and can be applied to future responses!"
        )


def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print(" AUTONOMAI - NEW FEATURES DEMONSTRATION")
    print(" Implicit Negative Feedback & Context-Based Rule Extraction")
    print("=" * 70)

    try:
        demo_correction_detection()
        demo_context_analysis()
        demo_combined()

        print("\n" + "=" * 70)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(
            "\nThese features help the system learn more naturally from user interactions,"
        )
        print(
            "capturing both explicit preferences and implicit corrections automatically."
        )
        print("\nTry them out in the terminal chatbot with /feedback-context command!")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
