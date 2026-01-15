import os
import sys
from pathlib import Path

# Add current directory to path to ensure src is importable
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from src.models.config import SystemConfig
    from src.core.instruction_manager import InstructionManager
    from src.core.main_model import MainModel, MockModel
except ImportError as e:
    print(f"Import Error: {e}")
    # Try adding src to path explicitly
    src_path = str(current_dir / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        from src.models.config import SystemConfig
        from src.core.instruction_manager import InstructionManager
        from src.core.main_model import MainModel, MockModel
    except ImportError as second_e:
        print(f"Second Import Error: {second_e}")
        sys.exit(1)


def test_deepseek_integration():
    print("Checking for DEEPSEEK_API_KEY...")
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not found.")
        print(
            "Please ensure you set it using: $env:DEEPSEEK_API_KEY='sk-ca6724f62fd44302ae869af' (in PowerShell)"
        )
        return

    print(f"DEEPSEEK_API_KEY found: {api_key[:5]}...{api_key[-4:]}")

    # Configure for DeepSeek
    config = SystemConfig(
        main_model="deepseek-chat",
        main_model_provider="deepseek",
        enable_auto_validation=False,
    )

    print(
        f"Initializing MainModel with provider: {config.main_model_provider} and model: {config.main_model}"
    )

    try:
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # In the current implementation, main_model.model might be a ChatOpenAI instance
        # (since deepseek uses OpenAI provider internally in this code)
        model_type = str(type(main_model.model))
        print(f"Model type: {model_type}")

        if "MockModel" in model_type:
            print(
                "WARNING: MainModel initialized with MockModel. This usually means an API key was missing or provider was not recognized during initialization."
            )

        query = "Hello! Please confirm you are DeepSeek and briefly state your primary function."
        print(f"\nSending Query: {query}")

        result = main_model.execute(query)

        print("\n--- Response ---")
        print(result["output"])
        print("----------------\n")

        if "Mock response" in result["output"]:
            print("Status: FAILED (Received mock response)")
        else:
            print("Status: SUCCESS (Connected to API)")

    except Exception as e:
        print(f"Error during execution: {e}")


if __name__ == "__main__":
    test_deepseek_integration()
