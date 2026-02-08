"""
Tests for the refactored modular components.

Tests cover:
- Provider detection and initialization (src/core/providers/)
- Cache initialization (src/core/cache_initializer.py)
- Instruction file handler (src/core/instruction_file_handler.py)
- SystemInitializer (src/system_initializer.py)
- FeedbackProcessor (src/feedback_processor.py)
- WorkflowManager (src/workflow_manager.py)
- SystemStatus (src/system_status.py)
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.config import SystemConfig, FailureEntry, FailureLog
from src.core.providers.base import detect_provider, initialize_provider
from src.core.cache_initializer import initialize_cache
from src.core.instruction_file_handler import InstructionFileHandler
from src.system_initializer import SystemInitializer
from src.feedback_processor import FeedbackProcessor
from src.workflow_manager import WorkflowManager
from src.system_status import SystemStatus


# ==================== Provider Tests ====================


class TestProviderDetection:
    """Tests for LLM provider detection"""

    def test_detect_anthropic_claude(self):
        assert detect_provider("claude-3-5-sonnet") == "anthropic"

    def test_detect_anthropic_keyword(self):
        assert detect_provider("anthropic-model") == "anthropic"

    def test_detect_openai_gpt(self):
        assert detect_provider("gpt-4") == "openai"

    def test_detect_openai_keyword(self):
        assert detect_provider("openai-model") == "openai"

    def test_detect_google_gemini(self):
        assert detect_provider("gemini-pro") == "google"

    def test_detect_google_keyword(self):
        assert detect_provider("google-model") == "google"

    def test_detect_deepseek(self):
        assert detect_provider("deepseek-chat") == "deepseek"

    def test_detect_openrouter(self):
        assert detect_provider("openrouter-model") == "openrouter"

    def test_detect_unknown(self):
        assert detect_provider("some-unknown-model") == "unknown"


class TestProviderInitialization:
    """Tests for provider initialization error handling"""

    def test_initialize_provider_no_api_key_raises(self):
        """Test that missing API key raises ConfigurationError"""
        from src.models.exceptions import ConfigurationError

        config = SystemConfig(
            main_model="claude-3-5-sonnet-20241022",
            main_model_provider="anthropic",
        )

        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
                initialize_provider(config)

    def test_initialize_provider_unknown_raises(self):
        """Test that unknown provider raises ConfigurationError"""
        from src.models.exceptions import ConfigurationError

        config = SystemConfig(
            main_model="unknown-model",
            main_model_provider="unknown",
        )

        with pytest.raises(ConfigurationError, match="No API key configured"):
            initialize_provider(config)

    def test_initialize_provider_detects_from_model_name(self):
        """Test provider auto-detection from model name"""
        from src.models.exceptions import ConfigurationError

        config = SystemConfig(
            main_model="gpt-4",
            main_model_provider=None,
        )

        # Should detect openai and raise because no API key
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
                initialize_provider(config)


# ==================== Cache Initializer Tests ====================


class TestCacheInitializer:
    """Tests for cache initialization"""

    def test_initialize_cache_when_not_available(self):
        """Test cache initialization when cache module is not available"""
        config = SystemConfig(enable_caching=True, cache_llm_responses=True)

        with patch("src.core.cache_initializer.CACHE_AVAILABLE", False):
            cache_manager, llm_cache = initialize_cache(config)
            assert cache_manager is None
            assert llm_cache is None

    def test_initialize_cache_returns_tuple(self):
        """Test that initialize_cache returns a tuple of two values"""
        config = SystemConfig(enable_caching=True, cache_llm_responses=True)

        with patch("src.core.cache_initializer.CACHE_AVAILABLE", False):
            result = initialize_cache(config)
            assert isinstance(result, tuple)
            assert len(result) == 2


# ==================== Instruction File Handler Tests ====================


class TestInstructionFileHandler:
    """Tests for InstructionFileHandler"""

    def test_file_exists_false(self):
        """Test file_exists returns False for non-existent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            handler = InstructionFileHandler(config)
            assert not handler.file_exists()

    def test_load_from_file_empty(self):
        """Test loading from non-existent file returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            handler = InstructionFileHandler(config)
            base, appendix = handler.load_from_file()
            assert base is None
            assert appendix is None

    def test_save_and_load(self):
        """Test saving and loading instructions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            handler = InstructionFileHandler(config)

            base = "# Base Instructions\nBe helpful."
            appendix = "# Dynamic Appendix\nNo custom rules yet."
            failure_log = FailureLog(max_size=50)

            handler.save_to_file(base, appendix, failure_log, "v1")
            assert handler.file_exists()

            loaded_base, loaded_appendix = handler.load_from_file()
            assert loaded_base is not None
            assert loaded_appendix is not None
            # File has multiple sections separated by ---
            # Section 0: header, Section 1: base instructions, etc.
            assert "System Instructions" in loaded_base
            assert "Base Instructions" in loaded_appendix

    def test_save_pending_review(self):
        """Test saving pending review content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            handler = InstructionFileHandler(config)

            handler.save_pending_review("# Review needed\nTest content\n")
            assert handler.pending_review_path.exists()


# ==================== SystemInitializer Tests ====================


class TestSystemInitializer:
    """Tests for SystemInitializer"""

    @patch("src.system_initializer.MainModel")
    @patch("src.system_initializer.CriticModel")
    @patch("src.system_initializer.ContextAnalyzer")
    def test_initialize_returns_all_components(
        self, mock_context_analyzer, mock_critic, mock_main
    ):
        """Test that initialize returns all expected components"""
        mock_main.return_value = MagicMock()
        mock_critic.return_value = MagicMock()
        mock_context_analyzer.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            components = SystemInitializer.initialize(config)

            assert "state_manager" in components
            assert "instruction_manager" in components
            assert "validation_pipeline" in components
            assert "main_model" in components
            assert "critic_model" in components
            assert "context_analyzer" in components

    @patch("src.system_initializer.MainModel")
    @patch("src.system_initializer.CriticModel")
    @patch("src.system_initializer.ContextAnalyzer")
    def test_initialize_no_distributed_state(
        self, mock_context_analyzer, mock_critic, mock_main
    ):
        """Test initialization without distributed state"""
        mock_main.return_value = MagicMock()
        mock_critic.return_value = MagicMock()
        mock_context_analyzer.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(
                instructions_dir=Path(tmpdir),
                enable_distributed_state=False,
            )
            components = SystemInitializer.initialize(config)
            assert components["state_manager"] is None


# ==================== FeedbackProcessor Tests ====================


class TestFeedbackProcessor:
    """Tests for FeedbackProcessor"""

    def _create_processor(self, enable_auto_optimization=False):
        """Helper to create a FeedbackProcessor with mocked dependencies"""
        instruction_manager = MagicMock()
        critic_model = MagicMock()
        context_analyzer = MagicMock()
        config = MagicMock()
        config.enable_auto_optimization = enable_auto_optimization

        return FeedbackProcessor(
            instruction_manager, critic_model, context_analyzer, config
        )

    def test_process_feedback_calls_process_failure(self):
        """Test that process_feedback delegates to process_failure"""
        processor = self._create_processor()
        result = processor.process_feedback(
            user_query="test query",
            model_output="test output",
            feedback_type="negative",
            feedback_details="wrong answer",
        )
        assert result["success"] is True

    def test_process_failure_without_optimization(self):
        """Test failure processing without auto-optimization"""
        processor = self._create_processor(enable_auto_optimization=False)
        result = processor.process_failure(
            trigger_type="auto_validation",
            failure_description="Validation failed",
            user_query="test",
            last_model_output="output",
        )
        assert result["success"] is True
        assert result["optimization_attempted"] is False
        assert "failure_id" in result

    def test_process_failure_with_optimization(self):
        """Test failure processing with auto-optimization"""
        processor = self._create_processor(enable_auto_optimization=True)
        processor.critic_model.optimize.return_value = {"success": True}

        result = processor.process_failure(
            trigger_type="auto_validation",
            failure_description="Validation failed",
        )
        assert result["success"] is True
        assert result["optimization_attempted"] is True
        assert result["optimization_result"] == {"success": True}

    def test_analyze_feedback_context_not_successful(self):
        """Test analyze_feedback_context when analysis fails"""
        processor = self._create_processor()
        processor.context_analyzer.analyze_conversation.return_value = {
            "success": False,
            "error": "Not enough data",
        }

        result = processor.analyze_feedback_context(
            conversation_history=[{"role": "user", "content": "hello"}]
        )
        assert result.get("success") is False

    def test_analyze_feedback_context_successful(self):
        """Test analyze_feedback_context with successful analysis"""
        processor = self._create_processor()
        processor.context_analyzer.analyze_conversation.return_value = {
            "success": True,
            "rules": [{"rule": "test"}],
            "dont_rules": [],
            "patterns": [],
        }
        processor.context_analyzer.format_rules_for_display.return_value = "Display"
        processor.context_analyzer.create_instruction_updates.return_value = "Updates"

        result = processor.analyze_feedback_context(
            conversation_history=[{"role": "user", "content": "hello"}]
        )
        assert result["success"] is True
        assert result["rules_count"] == 1
        assert result["dont_rules_count"] == 0

    def test_apply_context_rules_error_handling(self):
        """Test _apply_context_rules handles exceptions gracefully"""
        processor = self._create_processor(enable_auto_optimization=True)
        processor.instruction_manager.add_failure.side_effect = RuntimeError("DB error")

        result = processor._apply_context_rules("updates", {"rules_count": 1, "dont_rules_count": 0})
        assert result["success"] is False
        assert "error" in result


# ==================== WorkflowManager Tests ====================


class TestWorkflowManager:
    """Tests for WorkflowManager"""

    def test_lazy_initialization(self):
        """Test that WorkflowOrchestrator is lazily initialized"""
        config = MagicMock()
        instruction_manager = MagicMock()
        manager = WorkflowManager(config, instruction_manager)
        assert manager._workflow_orchestrator is None

    def test_execute_workflow_delegates(self):
        """Test that execute_workflow delegates to orchestrator"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.execute_workflow.return_value = {"status": "completed"}

        config = MagicMock()
        instruction_manager = MagicMock()
        manager = WorkflowManager(config, instruction_manager)

        # Manually inject a mock orchestrator
        manager._workflow_orchestrator = mock_orchestrator

        result = manager.execute_workflow("Build a chatbot")
        assert result["status"] == "completed"
        mock_orchestrator.execute_workflow.assert_called_once()


# ==================== SystemStatus Tests ====================


class TestSystemStatus:
    """Tests for SystemStatus"""

    def test_get_status_structure(self):
        """Test that get_status returns expected structure"""
        config = MagicMock()
        config.main_model = "claude-3-5-sonnet"
        config.critic_model = "claude-3-haiku"
        config.enable_auto_optimization = True
        config.enable_correction_detection = True

        instruction_manager = MagicMock()
        instruction_manager.version_controller.get_version_history.return_value = [
            {"version_id": "v1"}
        ]

        validation_pipeline = MagicMock()
        validation_pipeline.validators = []

        status = SystemStatus(config, instruction_manager, validation_pipeline)
        result = status.get_status()

        assert result["system"] == "Self-Optimizing Instruction Library"
        assert result["status"] == "operational"
        assert result["config"]["main_model"] == "claude-3-5-sonnet"
        assert result["versions"]["total"] == 1
        assert result["versions"]["latest"] == "v1"
        assert result["validation"]["validators_count"] == 0

    def test_get_version_history(self):
        """Test get_version_history delegates correctly"""
        instruction_manager = MagicMock()
        instruction_manager.version_controller.get_version_history.return_value = []

        status = SystemStatus(MagicMock(), instruction_manager, MagicMock())
        assert status.get_version_history() == []

    def test_get_current_instructions(self):
        """Test get_current_instructions delegates correctly"""
        instruction_manager = MagicMock()
        instruction_manager.get_full_instructions.return_value = "Be helpful."

        status = SystemStatus(MagicMock(), instruction_manager, MagicMock())
        assert status.get_current_instructions() == "Be helpful."

    def test_get_failure_history(self):
        """Test get_failure_history returns empty list"""
        status = SystemStatus(MagicMock(), MagicMock(), MagicMock())
        assert status.get_failure_history() == []

    def test_rollback(self):
        """Test rollback delegates correctly"""
        instruction_manager = MagicMock()
        instruction_manager.rollback.return_value = True

        status = SystemStatus(MagicMock(), instruction_manager, MagicMock())
        assert status.rollback(steps=2) is True
        instruction_manager.rollback.assert_called_once_with(2)

    def test_rollback_to_version(self):
        """Test rollback_to_version delegates correctly"""
        instruction_manager = MagicMock()
        instruction_manager.rollback_to_version.return_value = True

        status = SystemStatus(MagicMock(), instruction_manager, MagicMock())
        assert status.rollback_to_version("v1") is True
        instruction_manager.rollback_to_version.assert_called_once_with("v1")


# ==================== MainModel Refactoring Tests ====================


class TestMainModelRefactoring:
    """Tests that MainModel correctly uses the extracted modules"""

    def test_main_model_uses_detect_provider(self):
        """Test that MainModel._detect_provider delegates to providers module"""
        from src.core.main_model import MainModel

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            # Create a mock to avoid actual model initialization
            with patch("src.core.main_model.initialize_provider") as mock_init:
                mock_init.return_value = MagicMock()
                model = MainModel(config, MagicMock())

                assert model._detect_provider("claude-3") == "anthropic"
                assert model._detect_provider("gpt-4") == "openai"
                assert model._detect_provider("gemini-pro") == "google"

    def test_main_model_uses_cache_initializer(self):
        """Test that MainModel._initialize_cache delegates to cache_initializer"""
        from src.core.main_model import MainModel

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(
                instructions_dir=Path(tmpdir),
                enable_caching=True,
                cache_llm_responses=True,
            )
            with patch("src.core.main_model.initialize_provider") as mock_init:
                mock_init.return_value = MagicMock()
                with patch("src.core.main_model.initialize_cache") as mock_cache:
                    mock_cache.return_value = (None, None)
                    model = MainModel(config, MagicMock())
                    mock_cache.assert_called_once_with(config)


# ==================== InstructionManager Refactoring Tests ====================


class TestInstructionManagerRefactoring:
    """Tests that InstructionManager correctly uses the extracted file handler"""

    def test_instruction_manager_has_file_handler(self):
        """Test that InstructionManager uses InstructionFileHandler"""
        from src.core.instruction_manager import InstructionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            manager = InstructionManager(config)
            assert hasattr(manager, "file_handler")
            assert isinstance(manager.file_handler, InstructionFileHandler)

    def test_instruction_manager_save_load_cycle(self):
        """Test that InstructionManager save/load cycle works"""
        from src.core.instruction_manager import InstructionManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SystemConfig(instructions_dir=Path(tmpdir))
            manager = InstructionManager(config)

            # Should have default instructions after initialization
            assert manager.base_instructions != ""
            assert manager.dynamic_appendix != ""

            # Get full instructions
            full = manager.get_full_instructions()
            assert "Base Instructions" in full
