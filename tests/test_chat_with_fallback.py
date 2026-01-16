"""
Tests for ChatWithFallback class.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from langwatch.langchain.chat_with_fallback import ChatWithFallback
from langwatch import KeyManager, InMemoryRateLimiter


class TestChatWithFallbackInit:
    """Tests for ChatWithFallback initialization."""

    def test_basic_init(self, mock_chat_model):
        """Test basic initialization with models."""
        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["test-model"],
        )

        assert len(chat.models) == 1
        assert chat.model_names == ["test-model"]
        assert chat.alerts == []
        assert chat.key_manager is None

    def test_init_with_all_params(self, mock_chat_model, mock_alert_channel):
        """Test initialization with all parameters."""
        key_manager = KeyManager([
            {"name": "test", "key": "sk-test", "provider": "openai", "model": "gpt-4"}
        ])

        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["test-model"],
            alerts=[mock_alert_channel],
            key_manager=key_manager,
            cooldown_seconds=600,
            app_name="TestApp",
            skip_unhealthy=False,
            unhealthy_timeout=120,
        )

        assert chat.alerts == [mock_alert_channel]
        assert chat.key_manager is key_manager
        assert chat.cooldown_seconds == 600
        assert chat.app_name == "TestApp"
        assert chat.skip_unhealthy is False
        assert chat.unhealthy_timeout == 120

    def test_init_auto_generates_model_names(self, mock_chat_model):
        """Test that model names are auto-generated if not provided."""
        chat = ChatWithFallback(
            models=[mock_chat_model, mock_chat_model],
        )

        assert chat.model_names == ["model-0", "model-1"]

    def test_init_mismatched_lengths_raises(self, mock_chat_model):
        """Test that mismatched model/name lengths raise error."""
        with pytest.raises(ValueError) as exc_info:
            ChatWithFallback(
                models=[mock_chat_model, mock_chat_model],
                model_names=["only-one"],
            )

        assert "must match" in str(exc_info.value)

    def test_llm_type_property(self, mock_chat_model):
        """Test _llm_type property."""
        chat = ChatWithFallback(models=[mock_chat_model])
        assert chat._llm_type == "chat_with_fallback"

    def test_identifying_params(self, mock_chat_model):
        """Test _identifying_params property."""
        chat = ChatWithFallback(
            models=[mock_chat_model, mock_chat_model],
            model_names=["model-a", "model-b"],
        )

        params = chat._identifying_params
        assert params["model_names"] == ["model-a", "model-b"]
        assert params["num_models"] == 2


class TestChatWithFallbackFromConfig:
    """Tests for ChatWithFallback.from_config class method."""

    @patch("langwatch.providers.ProviderFactory.create_model")
    def test_from_config_creates_models(self, mock_create):
        """Test that from_config creates models via factory."""
        mock_model = MagicMock()
        mock_create.return_value = mock_model

        chat = ChatWithFallback.from_config(
            models=[
                {"name": "model-1", "provider": "openai", "model": "gpt-4", "api_key": "sk-1"},
                {"name": "model-2", "provider": "openai", "model": "gpt-4", "api_key": "sk-2"},
            ]
        )

        assert mock_create.call_count == 2
        assert len(chat.models) == 2
        assert chat.model_names == ["model-1", "model-2"]

    @patch("langwatch.providers.ProviderFactory.create_model")
    def test_from_config_creates_key_manager(self, mock_create):
        """Test that from_config creates KeyManager."""
        mock_create.return_value = MagicMock()

        chat = ChatWithFallback.from_config(
            models=[
                {"name": "primary", "provider": "openai", "model": "gpt-4", "api_key": "sk-1"},
                {"name": "fallback", "provider": "openai", "model": "gpt-4", "api_key": "sk-2", "is_fallback": True},
            ]
        )

        assert chat.key_manager is not None
        assert len(chat.key_manager.keys) == 2
        assert chat.key_manager.keys[0].is_fallback is False
        assert chat.key_manager.keys[1].is_fallback is True

    @patch("langwatch.providers.ProviderFactory.create_model")
    def test_from_config_with_app_name(self, mock_create):
        """Test that from_config passes app_name."""
        mock_create.return_value = MagicMock()

        chat = ChatWithFallback.from_config(
            models=[{"name": "test", "provider": "openai", "model": "gpt-4", "api_key": "sk-1"}],
            app_name="MyApp",
        )

        assert chat.app_name == "MyApp"


class TestChatWithFallbackGenerate:
    """Tests for synchronous _generate method."""

    def test_generate_success_first_model(self, mock_chat_model):
        """Test successful generation with first model."""
        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["primary"],
        )

        messages = [HumanMessage(content="Hello")]
        result = chat._generate(messages)

        assert isinstance(result, ChatResult)
        mock_chat_model._generate.assert_called_once()

    def test_generate_fallback_on_failure(self, mock_models_with_fallback):
        """Test that fallback is used when primary fails."""
        chat = ChatWithFallback(
            models=mock_models_with_fallback,
            model_names=["primary", "fallback"],
        )

        messages = [HumanMessage(content="Hello")]
        result = chat._generate(messages)

        assert isinstance(result, ChatResult)
        # Primary should have been tried and failed
        mock_models_with_fallback[0]._generate.assert_called_once()
        # Fallback should have succeeded
        mock_models_with_fallback[1]._generate.assert_called_once()

    def test_generate_marks_healthy_on_success(self, mock_chat_model):
        """Test that successful model is marked healthy."""
        key_configs = [
            {"name": "gemini-1", "key": "AIza-test", "provider": "google", "model": "gemini-2.5-flash"},
        ]
        key_manager = KeyManager(key_configs)
        key_manager.mark_failed("gemini-1", "Previous error")

        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["gemini-1"],
            key_manager=key_manager,
            skip_unhealthy=False,  # Disable skipping so the model is tried
        )

        messages = [HumanMessage(content="Hello")]
        chat._generate(messages)

        assert key_manager.get_key_by_name("gemini-1").is_healthy is True

    def test_generate_all_fail_raises(self, mock_failing_model):
        """Test that RuntimeError is raised when all models fail."""
        chat = ChatWithFallback(
            models=[mock_failing_model, mock_failing_model],
            model_names=["model-1", "model-2"],
        )

        messages = [HumanMessage(content="Hello")]

        with pytest.raises(RuntimeError) as exc_info:
            chat._generate(messages)

        assert "All 2 models failed" in str(exc_info.value)

    def test_generate_skips_unhealthy(self, mock_chat_model, sample_key_configs):
        """Test that unhealthy models are skipped."""
        key_manager = KeyManager(sample_key_configs)
        key_manager.mark_failed("gemini-1", "Error")

        failing_model = MagicMock()
        failing_model._generate = MagicMock(side_effect=Exception("Should not be called"))

        chat = ChatWithFallback(
            models=[failing_model, mock_chat_model],
            model_names=["gemini-1", "gemini-2"],
            key_manager=key_manager,
            skip_unhealthy=True,
        )

        messages = [HumanMessage(content="Hello")]
        result = chat._generate(messages)

        # First model should be skipped (unhealthy)
        failing_model._generate.assert_not_called()
        # Second model should be used
        mock_chat_model._generate.assert_called_once()


class TestChatWithFallbackAGenerate:
    """Tests for asynchronous _agenerate method."""

    @pytest.mark.asyncio
    async def test_agenerate_success(self, mock_chat_model):
        """Test successful async generation."""
        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["primary"],
        )

        messages = [HumanMessage(content="Hello")]
        result = await chat._agenerate(messages)

        assert isinstance(result, ChatResult)
        mock_chat_model._agenerate.assert_called_once()

    @pytest.mark.asyncio
    async def test_agenerate_fallback(self, mock_models_with_fallback):
        """Test async fallback on failure."""
        chat = ChatWithFallback(
            models=mock_models_with_fallback,
            model_names=["primary", "fallback"],
        )

        messages = [HumanMessage(content="Hello")]
        result = await chat._agenerate(messages)

        assert isinstance(result, ChatResult)
        mock_models_with_fallback[0]._agenerate.assert_called_once()
        mock_models_with_fallback[1]._agenerate.assert_called_once()


class TestChatWithFallbackBindTools:
    """Tests for bind_tools method."""

    def test_bind_tools_returns_new_instance(self, mock_chat_model):
        """Test that bind_tools returns a new ChatWithFallback instance."""
        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["primary"],
        )

        tools = [MagicMock()]
        new_chat = chat.bind_tools(tools)

        assert new_chat is not chat
        assert isinstance(new_chat, ChatWithFallback)

    def test_bind_tools_calls_underlying_models(self, mock_chat_model):
        """Test that bind_tools is called on underlying models."""
        chat = ChatWithFallback(
            models=[mock_chat_model, mock_chat_model],
            model_names=["model-1", "model-2"],
        )

        tools = [MagicMock()]
        chat.bind_tools(tools)

        # bind_tools should be called on each model
        assert mock_chat_model.bind_tools.call_count == 2

    def test_bind_tools_preserves_config(self, mock_chat_model, mock_alert_channel):
        """Test that bind_tools preserves configuration."""
        chat = ChatWithFallback(
            models=[mock_chat_model],
            model_names=["primary"],
            alerts=[mock_alert_channel],
            app_name="TestApp",
            cooldown_seconds=600,
        )

        tools = [MagicMock()]
        new_chat = chat.bind_tools(tools)

        assert new_chat.alerts == [mock_alert_channel]
        assert new_chat.app_name == "TestApp"
        assert new_chat.cooldown_seconds == 600


class TestChatWithFallbackAlerts:
    """Tests for alert functionality."""

    def test_failure_triggers_alert(self, mock_failing_model, mock_alert_channel):
        """Test that model failure triggers alert."""
        # Need a successful fallback to complete
        success_model = MagicMock()
        success_result = ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="OK"))]
        )
        success_model._generate = MagicMock(return_value=success_result)

        chat = ChatWithFallback(
            models=[mock_failing_model, success_model],
            model_names=["primary", "fallback"],
            alerts=[mock_alert_channel],
        )

        messages = [HumanMessage(content="Hello")]
        chat._generate(messages)

        # Alert should have been sent
        assert len(mock_alert_channel.sent_payloads) == 1
        payload = mock_alert_channel.sent_payloads[0]
        assert payload.failed_key_name == "primary"

    def test_alert_respects_cooldown(self, mock_failing_model, mock_alert_channel):
        """Test that alerts respect cooldown."""
        success_model = MagicMock()
        success_result = ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="OK"))]
        )
        success_model._generate = MagicMock(return_value=success_result)

        chat = ChatWithFallback(
            models=[mock_failing_model, success_model],
            model_names=["primary", "fallback"],
            alerts=[mock_alert_channel],
            cooldown_seconds=3600,  # 1 hour cooldown
        )

        messages = [HumanMessage(content="Hello")]

        # First call - alert sent
        chat._generate(messages)
        assert len(mock_alert_channel.sent_payloads) == 1

        # Second call - alert should be in cooldown
        chat._generate(messages)
        assert len(mock_alert_channel.sent_payloads) == 1  # Still 1

    def test_alert_payload_includes_app_name(self, mock_failing_model, mock_alert_channel):
        """Test that alert payload includes app_name."""
        success_model = MagicMock()
        success_result = ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="OK"))]
        )
        success_model._generate = MagicMock(return_value=success_result)

        chat = ChatWithFallback(
            models=[mock_failing_model, success_model],
            model_names=["primary", "fallback"],
            alerts=[mock_alert_channel],
            app_name="MyApp",
        )

        messages = [HumanMessage(content="Hello")]
        chat._generate(messages)

        payload = mock_alert_channel.sent_payloads[0]
        assert "MyApp" in payload.title
        assert payload.details["app_name"] == "MyApp"


class TestChatWithFallbackCallbacks:
    """Tests for callback functionality."""

    def test_on_key_failure_callback(self, mock_failing_model):
        """Test on_key_failure callback is called."""
        success_model = MagicMock()
        success_result = ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="OK"))]
        )
        success_model._generate = MagicMock(return_value=success_result)

        callback_calls = []

        def on_failure(key_name, error):
            callback_calls.append((key_name, error))

        chat = ChatWithFallback(
            models=[mock_failing_model, success_model],
            model_names=["primary", "fallback"],
            on_key_failure=on_failure,
        )

        messages = [HumanMessage(content="Hello")]
        chat._generate(messages)

        assert len(callback_calls) == 1
        assert callback_calls[0][0] == "primary"
        assert "quota exceeded" in callback_calls[0][1]

    def test_on_fallback_activated_callback(self, mock_failing_model, sample_key_configs):
        """Test on_fallback_activated callback is called."""
        key_manager = KeyManager(sample_key_configs)

        # Create mock models
        failing1 = MagicMock()
        failing1._generate = MagicMock(side_effect=Exception("Error 1"))

        failing2 = MagicMock()
        failing2._generate = MagicMock(side_effect=Exception("Error 2"))

        success = MagicMock()
        success_result = ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="OK"))]
        )
        success._generate = MagicMock(return_value=success_result)

        callback_calls = []

        def on_fallback(key_name):
            callback_calls.append(key_name)

        chat = ChatWithFallback(
            models=[failing1, failing2, success],
            model_names=["gemini-1", "gemini-2", "fallback"],
            key_manager=key_manager,
            on_fallback_activated=on_fallback,
        )

        messages = [HumanMessage(content="Hello")]
        chat._generate(messages)

        # Callback should be triggered when entering fallback
        assert "fallback" in callback_calls


class TestChatWithFallbackGetStatus:
    """Tests for get_status method."""

    def test_get_status_with_key_manager(self, mock_chat_model, sample_key_configs):
        """Test get_status with KeyManager."""
        key_manager = KeyManager(sample_key_configs)
        key_manager.mark_failed("gemini-1", "Error")

        chat = ChatWithFallback(
            models=[mock_chat_model, mock_chat_model, mock_chat_model],
            model_names=["gemini-1", "gemini-2", "fallback"],
            key_manager=key_manager,
        )

        status = chat.get_status()

        assert status["total_keys"] == 3
        assert status["failed_keys"] == 1
        assert status["healthy_keys"] == 2

    def test_get_status_without_key_manager(self, mock_chat_model):
        """Test get_status without KeyManager."""
        chat = ChatWithFallback(
            models=[mock_chat_model, mock_chat_model],
            model_names=["model-1", "model-2"],
        )

        status = chat.get_status()

        assert status["model_names"] == ["model-1", "model-2"]
        assert status["num_models"] == 2
