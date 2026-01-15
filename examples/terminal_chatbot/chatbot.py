#!/usr/bin/env python3
"""
Terminal Chatbot Example using DeepSeek API
A simple terminal-based chatbot demonstrating autonomai features
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src import SelfOptimizingSystem, SystemConfig, LengthValidator
from dotenv import load_dotenv


class TerminalChatbot:
    """A simple terminal-based chatbot using autonomai"""

    def __init__(self):
        """Initialize the chatbot"""
        # Load environment variables
        load_dotenv()

        # Configure system to use DeepSeek
        self.config = SystemConfig(
            main_model="deepseek-chat",
            critic_model="deepseek-chat",
            main_model_provider="deepseek",
            critic_model_provider="deepseek",
            temperature_main=0.7,
            temperature_critic=0.3,
            enable_auto_optimization=True,
        )

        # Initialize the self-optimizing system
        print("🤖 Initializing chatbot with DeepSeek API...")
        self.system = SelfOptimizingSystem(self.config)

        # Add validators to demonstrate validation features
        self.system.add_validator(LengthValidator(min_length=5, max_length=2000))

        # Conversation history
        self.conversation_history = []
        self.running = False

        print("✅ Chatbot initialized successfully!\n")

    def show_banner(self):
        """Display welcome banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🤖 AUTONOMAI TERMINAL CHATBOT 🤖                   ║
║                                                              ║
║          Powered by DeepSeek API                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def show_help(self):
        """Display help information"""
        help_text = """
📚 Available Commands:
  /help             - Show this help message
  /status           - Show system status and configuration
  /history          - Show conversation history
  /versions         - Show instruction version history
  /feedback         - Submit feedback for instruction optimization
  /feedback-context - Analyze conversation and extract rules automatically
  /clear            - Clear conversation history
  /quit             - Exit the chatbot

✨ Features Demonstrated:
  • Interactive conversation with DeepSeek API
  • Automatic output validation
  • Self-optimizing instructions based on failures
  • Implicit correction detection
  • Context-based rule extraction
  • Version control for instruction changes
  • Manual feedback processing
  • Conversation context management

💡 Tips:
  • Just type your question and press Enter
  • Use /feedback to help the system learn from your input
  • Use /feedback-context to analyze conversation patterns
  • Check /status to see the current system configuration
  • View /versions to track instruction improvements
"""
        print(help_text)

    def show_status(self):
        """Display system status"""
        status = self.system.get_status()

        print("\n📊 System Status:")
        print(f"  Status: {status['status']}")
        print(f"  Main Model: {status['config']['main_model']} (DeepSeek)")
        print(f"  Critic Model: {status['config']['critic_model']} (DeepSeek)")
        print(f"  Auto-Optimization: {status['config']['enable_auto_optimization']}")
        print(f"  Total Versions: {status['versions']['total']}")
        print(f"  Latest Version: {status['versions']['latest']}")
        print(f"  Active Validators: {status['validation']['validators_count']}")
        print(f"  Conversation Length: {len(self.conversation_history)} messages\n")

    def show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            print("\n📝 No conversation history yet.\n")
            return

        print(
            f"\n📝 Conversation History ({len(self.conversation_history)} messages):\n"
        )
        for i, msg in enumerate(self.conversation_history[-10:], 1):  # Show last 10
            role = "You" if msg["role"] == "user" else "Bot"
            content = (
                msg["content"][:100] + "..."
                if len(msg["content"]) > 100
                else msg["content"]
            )
            print(f"  {i}. {role}: {content}")
        print()

    def show_versions(self):
        """Display version history"""
        versions = self.system.get_version_history()

        if not versions:
            print("\n📦 No version history yet.\n")
            return

        print(f"\n📦 Instruction Version History ({len(versions)} versions):\n")
        for version in versions[-5:]:  # Show last 5
            print(f"  • {version['version_id']}")
            print(f"    Trigger: {version['trigger_type']}")
            print(f"    Summary: {version['diff_summary']}")
            print()

    def submit_feedback(self):
        """Submit manual feedback for optimization"""
        print("\n💭 Manual Feedback Submission")
        print("Enter your feedback (type 'END' on a new line to finish):")

        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)

        feedback = "\n".join(lines).strip()

        if not feedback:
            print("❌ No feedback provided.\n")
            return

        print("\nProcessing feedback...")
        result = self.system.request_instruction_update(feedback, severity="moderate")

        if result.get("success"):
            print("✅ Feedback processed and instructions updated!")
            if result.get("new_version"):
                print(f"   New version: {result['new_version']}")
        else:
            print(
                f"⚠️  Feedback processed but optimization failed: {result.get('message', 'Unknown error')}"
            )
        print()

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("\n🗑️  Conversation history cleared.\n")

    def analyze_feedback_context(self):
        """Analyze conversation context and extract rules"""
        if not self.conversation_history:
            print("\n❌ No conversation history available for analysis.\n")
            return

        print("\n🔍 Analyzing conversation context...")
        print("This may take a moment...\n")

        # Perform context analysis
        result = self.system.analyze_feedback_context(
            self.conversation_history,
            focus_recent=10,
            min_confidence=0.6,
            auto_apply=False,  # Don't auto-apply, let user review first
        )

        if not result.get("success"):
            print(f"❌ Analysis failed: {result.get('message', 'Unknown error')}\n")
            return

        # Display the formatted analysis
        print(result["formatted_display"])
        print()

        # Ask if user wants to apply these rules
        if result.get("rules_count", 0) > 0 or result.get("dont_rules_count", 0) > 0:
            apply = (
                input("\n💡 Apply these rules to system instructions? (y/n): ")
                .lower()
                .strip()
            )

            if apply == "y":
                print("\n📝 Applying rules...")
                apply_result = self.system._apply_context_rules(
                    result["instruction_updates"], result["analysis"]
                )

                if apply_result.get("success"):
                    print("✅ Rules applied successfully!")
                    if apply_result.get("optimization_result", {}).get("success"):
                        print("✨ System instructions updated!")
                    else:
                        print("⚠️  Rules logged for review.")
                else:
                    print(
                        f"❌ Failed to apply rules: {apply_result.get('message', 'Unknown error')}"
                    )
            else:
                print("\n📋 Rules not applied. You can review them above.")
        else:
            print("\n💭 No significant rules extracted from conversation.")

        print()

    def process_command(self, command: str) -> bool:
        """Process special commands. Returns True if should continue, False if should quit"""
        command = command.lower().strip()

        if command == "/quit" or command == "/exit":
            return False
        elif command == "/help":
            self.show_help()
        elif command == "/status":
            self.show_status()
        elif command == "/history":
            self.show_history()
        elif command == "/versions":
            self.show_versions()
        elif command == "/feedback":
            self.submit_feedback()
        elif command == "/feedback-context":
            self.analyze_feedback_context()
        elif command == "/clear":
            self.clear_history()
        else:
            print(f"❓ Unknown command: {command}")
            print("   Type /help to see available commands.\n")

        return True

    def chat(self, user_input: str):
        """Process a chat message"""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Execute with conversation context
        print("🤔 Thinking...")
        result = self.system.execute(
            user_input,
            conversation_context=self.conversation_history[
                -5:
            ],  # Last 5 messages for context
        )

        # Display the response
        output = result["output"]
        print(f"\n🤖 Bot: {output}\n")

        # Add bot response to history
        self.conversation_history.append({"role": "assistant", "content": output})

        # Show correction detection info if relevant
        if result.get("correction_detected"):
            confidence = result.get("correction_confidence", 0)
            print(
                f"🔍 Note: Implicit correction detected (confidence: {confidence:.2f})"
            )
            print("    The system is learning from your feedback!")
            if result.get("optimization_attempted"):
                opt_result = result.get("optimization_result", {})
                if opt_result.get("success"):
                    print("    ✨ Instructions updated based on your correction!")
            print()

        # Show validation and optimization info if relevant
        if not result["validation_passed"]:
            print("⚠️  Note: Response failed validation")
            if result.get("optimization_attempted"):
                opt_result = result.get("optimization_result", {})
                if opt_result.get("success"):
                    print(
                        "✨ System learned from this failure and updated instructions!"
                    )
                else:
                    print(
                        f"❌ Optimization failed: {opt_result.get('message', 'Unknown error')}"
                    )
            print()

    def run(self):
        """Main chatbot loop"""
        self.running = True
        self.show_banner()
        self.show_help()

        print("💬 Start chatting! (Type /help for commands, /quit to exit)\n")

        try:
            while self.running:
                try:
                    # Get user input
                    user_input = input("You: ").strip()

                    if not user_input:
                        continue

                    # Check if it's a command
                    if user_input.startswith("/"):
                        if not self.process_command(user_input):
                            break
                    else:
                        # Regular chat message
                        self.chat(user_input)

                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted by user.")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    print("Please try again or type /quit to exit.\n")

        finally:
            print("\n👋 Goodbye! Thanks for chatting!\n")


def main():
    """Main entry point"""
    # Check if DeepSeek API key is set
    load_dotenv()
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  Warning: DEEPSEEK_API_KEY not found in environment")
        print("   The chatbot will use a mock model for demonstration.")
        print("   To use the real DeepSeek API:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: DEEPSEEK_API_KEY=your_api_key_here")
        print("   3. Optionally add: DEEPSEEK_BASE_URL=https://api.deepseek.com/v1\n")

        response = input("Continue with mock model? (y/n): ").lower().strip()
        if response != "y":
            print("Exiting...")
            return
        print()

    # Create and run chatbot
    chatbot = TerminalChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
