import os
import sys
import time
from pathlib import Path

# Add current directory to path to ensure src is importable
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.models.config import SystemConfig
from src.core.instruction_manager import InstructionManager
from src.core.main_model import MainModel
from src.core.critic_model import CriticModel
from src.core.validator import ValidationPipeline, JSONValidator


def run_optimization_test():
    """
    Runs a 3-loop test where we force validation failures and
    observe the Critic optimizing instructions.
    """
    print("=== Starting Continuous Optimization Test (3 Loops) ===\n")

    # 1. Configuration
    config = SystemConfig(
        main_model="deepseek-chat",
        main_model_provider="deepseek",
        critic_model="deepseek-chat",
        critic_model_provider="deepseek",
        enable_auto_validation=True,
        max_optimization_attempts=1,
        retry_cooldown_seconds=1,
    )

    # 2. Setup Validation Pipeline
    # Requirement: Output MUST be JSON and MUST include 'test_id' and 'explanation'
    pipeline = ValidationPipeline()
    pipeline.add_validator(JSONValidator(required_fields=["test_id", "explanation"]))

    # 3. Initialize Components
    instruction_manager = InstructionManager(config)
    main_model = MainModel(config, instruction_manager, validation_pipeline=pipeline)
    critic_model = CriticModel(config, instruction_manager)

    # 4. Test Query
    # We use a query that is unlikely to produce JSON initially
    test_query = "Explain why the sky is blue."

    for i in range(1, 4):
        print(f"--- LOOP {i} ---")
        print(f"Query: {test_query}")

        # Execute Query
        result = main_model.execute(test_query)
        output = result["output"]
        passed = result["validation_passed"]

        print(f"Model Output (first 100 chars): {output[:100].strip()}...")
        print(f"Validation Passed: {passed}")

        if not passed:
            print("Validation FAILED. Triggering Optimizer (Critic)...")
            failure_entry = result["failure_entry"]

            if failure_entry:
                # The Critic will analyze the failure and update instructions.md
                optimization_result = critic_model.optimize(failure_entry)

                if optimization_result["success"]:
                    print("SUCCESS: Optimizer updated instructions.")
                    print(
                        f"Impact Analysis: {optimization_result['critic_response'].impact_analysis}"
                    )
                    print(
                        f"Proposed Update: {optimization_result['critic_response'].proposed_appendix_update}"
                    )
                else:
                    print(
                        f"FAILED: Optimizer could not update instructions. Error: {optimization_result['error_message']}"
                    )
            else:
                print("Error: No failure entry generated despite validation failure.")
        else:
            print("SUCCESS: Validation passed! The model has learned the requirement.")

        print(
            f"\nTotal Instructions Length: {len(instruction_manager.get_full_instructions())} chars"
        )
        print("-" * 30 + "\n")

        # Wait a bit between loops
        if i < 3:
            print("Waiting for next loop...")
            time.sleep(2)

    print("=== Test Complete ===")
    print(f"Check 'instructions/instructions.md' for the updated rules.")


if __name__ == "__main__":
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("Error: DEEPSEEK_API_KEY not found in environment.")
        sys.exit(1)

    run_optimization_test()
