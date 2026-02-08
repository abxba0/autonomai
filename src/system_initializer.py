"""
System initialization for SelfOptimizingSystem.

Handles creation and wiring of core components from SystemConfig.
"""

from typing import Optional

from .core.main_model import MainModel
from .core.critic_model import CriticModel
from .core.instruction_manager import InstructionManager
from .core.context_analyzer import ContextAnalyzer
from .core.validator import ValidationPipeline
from .models.config import SystemConfig


class SystemInitializer:
    """Factory for initializing the core system components.

    Creates and wires together the instruction manager, validation pipeline,
    main model, critic model, and context analyzer based on configuration.
    """

    @staticmethod
    def initialize(config: SystemConfig):
        """Initialize all system components from config.

        Args:
            config: System configuration.

        Returns:
            Dict containing initialized components:
                - state_manager
                - instruction_manager
                - validation_pipeline
                - main_model
                - critic_model
                - context_analyzer
        """
        # Initialize distributed state manager if enabled
        state_manager = None
        if config.enable_distributed_state:
            from .storage.distributed_state import DistributedStateManager, DistributedStateConfig

            state_config = DistributedStateConfig(
                enabled=True,
                redis_url=config.redis_state_url,
                lock_timeout=config.distributed_lock_timeout,
            )
            state_manager = DistributedStateManager(state_config)

        # Initialize components
        instruction_manager = InstructionManager(config, state_manager=state_manager)
        validation_pipeline = ValidationPipeline()
        main_model = MainModel(config, instruction_manager, validation_pipeline)
        critic_model = CriticModel(config, instruction_manager)

        # Initialize context analyzer with optional LLM support
        context_analyzer = ContextAnalyzer(
            use_llm=True,
            llm_model=critic_model.model,
        )

        return {
            "state_manager": state_manager,
            "instruction_manager": instruction_manager,
            "validation_pipeline": validation_pipeline,
            "main_model": main_model,
            "critic_model": critic_model,
            "context_analyzer": context_analyzer,
        }
