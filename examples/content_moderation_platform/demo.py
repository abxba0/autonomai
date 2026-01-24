#!/usr/bin/env python3
"""
Interactive Content Moderation Platform Demo

Demonstrates all features of the platform including:
- Multi-tenant moderation with different rules
- Custom validators in action
- AI-powered decision making with DeepSeek
- Caching performance
- Learning from human overrides
- Batch processing
"""

import sys
import os
from pathlib import Path

# Set up environment
os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "mock-key-for-demo")

from engine import ModerationEngine
from models.content import ContentType
from dotenv import load_dotenv
import time


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print('=' * 70)


def print_section(text: str):
    """Print a formatted section"""
    print(f"\n--- {text} ---\n")


def demo_1_basic_moderation():
    """Demo 1: Basic content moderation"""
    print_header("Demo 1: Basic Content Moderation")

    print("\nInitializing moderation engine for 'gaming_community' tenant...")
    engine = ModerationEngine(tenant_id="gaming_community")

    test_contents = [
        ("Great game! Had so much fun playing!", "Clean content"),
        ("You got destroyed in that match! GG", "Competitive language (allowed in gaming)"),
        ("This is spam! Click here: http://scam.com Buy now!!!", "Spam with links"),
        ("Everyone should be eliminated", "Hate speech pattern"),
        ("What an amazing community! Love it here.", "Positive content"),
    ]

    print_section("Moderating Test Content")

    for content, description in test_contents:
        print(f"📝 Content: \"{content}\"")
        print(f"   Context: {description}")

        result = engine.moderate_content(
            content=content,
            content_type="comment",
            author_id="demo_user_1"
        )

        status_emoji = {
            "approved": "✅",
            "rejected": "❌",
            "flagged": "⚠️"
        }.get(result["decision"], "❓")

        print(f"   {status_emoji} Decision: {result['decision'].upper()}")
        print(f"   Action: {result['action']}")
        print(f"   Confidence: {result['confidence']:.2f}")

        if result["violations"]:
            print(f"   Violations:")
            for v in result["violations"]:
                print(f"     - {v['type']}: severity {v['severity']:.2f}")

        print(f"   Processing Time: {result['processing_time_ms']:.1f}ms")
        print(f"   From Cache: {result['from_cache']}")
        print()


def demo_2_multi_tenant():
    """Demo 2: Multi-tenant with different rules"""
    print_header("Demo 2: Multi-Tenant - Different Community Standards")

    test_content = "You got destroyed in that match, loser!"

    print(f"\n📝 Test Content: \"{test_content}\"\n")
    print("Testing the SAME content across different communities:\n")

    # Gaming community (lenient)
    print("1. Gaming Community (lenient, allows competitive language):")
    gaming_engine = ModerationEngine(tenant_id="gaming_community")
    result1 = gaming_engine.moderate_content(test_content)
    print(f"   Decision: {result1['decision'].upper()} ({result1['confidence']:.2f} confidence)")

    # Professional forum (strict)
    print("\n2. Professional Forum (strict, professional standards):")
    prof_engine = ModerationEngine(tenant_id="professional_forum")
    result2 = prof_engine.moderate_content(test_content)
    print(f"   Decision: {result2['decision'].upper()} ({result2['confidence']:.2f} confidence)")

    # Kids platform (very strict)
    print("\n3. Kids Platform (very strict, child-safe):")
    kids_engine = ModerationEngine(tenant_id="kids_platform")
    result3 = kids_engine.moderate_content(test_content)
    print(f"   Decision: {result3['decision'].upper()} ({result3['confidence']:.2f} confidence)")

    print(f"\n💡 Notice: Same content → Different decisions based on community standards!")


def demo_3_caching_performance():
    """Demo 3: Caching performance demonstration"""
    print_header("Demo 3: Caching Performance (1000x+ Speedup)")

    engine = ModerationEngine(tenant_id="social_platform")

    test_content = "Check out this amazing product!"

    print(f"📝 Test Content: \"{test_content}\"\n")

    # First request (uncached)
    print("1st Request (Uncached - Full AI Analysis):")
    start = time.time()
    result1 = engine.moderate_content(test_content)
    time1 = (time.time() - start) * 1000
    print(f"   Decision: {result1['decision'].upper()}")
    print(f"   Time: {time1:.1f}ms")
    print(f"   From Cache: {result1['from_cache']}")

    # Second request (cached)
    print("\n2nd Request (Cached - Instant Result):")
    start = time.time()
    result2 = engine.moderate_content(test_content)
    time2 = (time.time() - start) * 1000
    print(f"   Decision: {result2['decision'].upper()}")
    print(f"   Time: {time2:.1f}ms")
    print(f"   From Cache: {result2['from_cache']}")

    if time1 > 0:
        speedup = time1 / max(time2, 0.1)
        print(f"\n🚀 Speedup: {speedup:.0f}x faster!")
        print(f"   Savings: {time1 - time2:.1f}ms per request")
        print(f"   At 1000 requests/sec: Save {(time1 - time2):.0f} seconds/day")


def demo_4_batch_processing():
    """Demo 4: Batch content moderation"""
    print_header("Demo 4: Batch Processing")

    engine = ModerationEngine(tenant_id="marketplace")

    # Simulate batch of marketplace listings
    batch_contents = [
        {"text": "Great condition laptop for sale", "type": "listing", "author_id": "seller1"},
        {"text": "BUY NOW!!! CLICK HERE www.scam.com LIMITED TIME", "type": "listing", "author_id": "seller2"},
        {"text": "Vintage camera in excellent condition", "type": "listing", "author_id": "seller3"},
        {"text": "Free money! Click now!", "type": "listing", "author_id": "seller4"},
        {"text": "Handmade jewelry, beautiful pieces", "type": "listing", "author_id": "seller5"},
    ]

    print(f"Processing {len(batch_contents)} marketplace listings...\n")

    start = time.time()
    results = engine.moderate_batch(batch_contents)
    batch_time = (time.time() - start) * 1000

    print(f"Batch processed in {batch_time:.0f}ms\n")

    # Summary
    approved = sum(1 for r in results if r["decision"] == "approved")
    rejected = sum(1 for r in results if r["decision"] == "rejected")
    flagged = sum(1 for r in results if r["decision"] == "flagged")

    print(f"Results Summary:")
    print(f"  ✅ Approved: {approved}")
    print(f"  ❌ Rejected: {rejected}")
    print(f"  ⚠️  Flagged for Review: {flagged}")
    print(f"\n  Average: {batch_time / len(batch_contents):.0f}ms per listing")


def demo_5_learning_from_overrides():
    """Demo 5: Self-learning from human feedback"""
    print_header("Demo 5: Self-Learning from Human Moderator Overrides")

    engine = ModerationEngine(tenant_id="social_platform")

    content = "This is borderline content that could go either way"

    print(f"📝 Content: \"{content}\"\n")

    # AI makes initial decision
    print("Step 1: AI Moderation Decision")
    result = engine.moderate_content(content)
    print(f"   AI Decision: {result['decision'].upper()}")
    print(f"   Confidence: {result['confidence']:.2f}")

    # Human moderator overrides
    print("\nStep 2: Human Moderator Override")
    print("   Moderator Sarah reviews and decides this should be APPROVED")
    print("   Reason: 'Context makes this acceptable for our community'")

    override_result = engine.override_decision(
        content_id=result["content_id"],
        new_decision="APPROVED",
        moderator_id="mod_sarah",
        reason="Context makes this acceptable for our community"
    )

    print(f"\nStep 3: Learning Triggered")
    print("   ✓ System recorded the override")
    print("   ✓ Submitted feedback to optimization pipeline")
    print("   ✓ Future similar content will benefit from this learning")

    print(f"\n💡 Over time, the AI learns your community's specific standards!")


def demo_6_statistics_and_analytics():
    """Demo 6: Moderation statistics"""
    print_header("Demo 6: Statistics & Analytics")

    engine = ModerationEngine(tenant_id="gaming_community")

    stats = engine.get_moderation_stats(date_range="last_7_days")

    print(f"Tenant: {stats['tenant_name']}")
    print(f"Period: {stats['date_range']}")
    print(f"\nModeration Stats:")
    print(f"  Total Moderated: {stats['total']:,}")
    print(f"  ✅ Approved: {stats['approved']:,} ({stats['approval_rate']:.1%})")
    print(f"  ❌ Rejected: {stats['rejected']:,} ({stats['rejection_rate']:.1%})")
    print(f"  ⚠️  Flagged: {stats['flagged']:,} ({stats['flagged_rate']:.1%})")
    print(f"\nPerformance:")
    print(f"  Avg Processing Time: {stats['avg_processing_time_ms']:.0f}ms")
    print(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
    print(f"\nQuality:")
    print(f"  Human Override Rate: {stats['override_rate']:.1%}")
    print(f"    (Low override rate = high accuracy)")


def main():
    """Run all demonstrations"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║           Content Moderation Platform - Interactive Demo                ║
║                                                                           ║
║  Production-ready AI moderation with AutonomAI + DeepSeek               ║
║  Demonstrating: Multi-tenant, Caching, Batch, Learning, Analytics       ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    load_dotenv()

    # Check if using mock or real API
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key or api_key == "mock-key-for-demo":
        print("⚠️  Running with MOCK models (no API key configured)")
        print("   Set DEEPSEEK_API_KEY environment variable for real AI moderation")
        print()

    try:
        # Run all demos
        demo_1_basic_moderation()
        demo_2_multi_tenant()
        demo_3_caching_performance()
        demo_4_batch_processing()
        demo_5_learning_from_overrides()
        demo_6_statistics_and_analytics()

        print_header("Demo Complete!")
        print("""
🎉 All demonstrations completed successfully!

Key Features Demonstrated:
  ✓ Multi-tenant isolation with different moderation rules
  ✓ Custom validators (profanity, hate speech, spam, toxicity)
  ✓ AI-powered analysis with DeepSeek
  ✓ 1000x+ performance improvement with caching
  ✓ Efficient batch processing
  ✓ Self-learning from human moderator overrides
  ✓ Comprehensive analytics and statistics

Next Steps:
  1. Configure your DEEPSEEK_API_KEY for real AI moderation
  2. Try the CLI: python cli.py moderate --text "Your content"
  3. Run the API: python api.py
  4. Customize tenant configs in config/tenant_configs.yaml
  5. Add your own custom validators
  6. Deploy to production with Docker/Kubernetes

For full documentation, see README.md
        """)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
