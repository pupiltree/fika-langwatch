"""
Tests for ProviderFactory class.
"""

import pytest
from unittest.mock import patch, MagicMock

from langwatch import APIKey
from langwatch.providers import ProviderFactory


class TestProviderFactory:
    """Tests for ProviderFactory class."""

    def test_base_urls(self):
        """Test that base URLs are defined."""
        assert "openrouter" in ProviderFactory.BASE_URLS
        assert ProviderFactory.BASE_URLS["openrouter"] == "https://openrouter.ai/api/v1"

    def test_unsupported_provider(self):
        """Test that unsupported provider raises ValueError."""
        key = APIKey(
            name="test",
            key="sk-test",
            provider="unsupported_provider",
            model="some-model",
        )

        with pytest.raises(ValueError) as exc_info:
            ProviderFactory.create_model(key)

        assert "Unsupported provider" in str(exc_info.value)
        assert "unsupported_provider" in str(exc_info.value)

    @patch("langwatch.providers.ProviderFactory._create_google_model")
    def test_create_google_model_called(self, mock_create):
        """Test that google provider calls correct method."""
        mock_create.return_value = MagicMock()

        key = APIKey(
            name="gemini",
            key="AIza-test",
            provider="google",
            model="gemini-2.5-flash",
        )

        ProviderFactory.create_model(key)
        mock_create.assert_called_once()

    @patch("langwatch.providers.ProviderFactory._create_openai_model")
    def test_create_openai_model_called(self, mock_create):
        """Test that openai provider calls correct method."""
        mock_create.return_value = MagicMock()

        key = APIKey(
            name="openai",
            key="sk-test",
            provider="openai",
            model="gpt-4",
        )

        ProviderFactory.create_model(key)
        mock_create.assert_called_once()

    @patch("langwatch.providers.ProviderFactory._create_anthropic_model")
    def test_create_anthropic_model_called(self, mock_create):
        """Test that anthropic provider calls correct method."""
        mock_create.return_value = MagicMock()

        key = APIKey(
            name="claude",
            key="sk-ant-test",
            provider="anthropic",
            model="claude-3-sonnet",
        )

        ProviderFactory.create_model(key)
        mock_create.assert_called_once()

    @patch("langwatch.providers.ProviderFactory._create_openrouter_model")
    def test_create_openrouter_model_called(self, mock_create):
        """Test that openrouter provider calls correct method."""
        mock_create.return_value = MagicMock()

        key = APIKey(
            name="openrouter",
            key="sk-or-test",
            provider="openrouter",
            model="grok-4.1",
        )

        ProviderFactory.create_model(key)
        mock_create.assert_called_once()

    def test_provider_case_insensitive(self):
        """Test that provider matching is case insensitive."""
        key = APIKey(
            name="test",
            key="sk-test",
            provider="OPENAI",  # uppercase
            model="gpt-4",
        )

        with patch("langwatch.providers.ProviderFactory._create_openai_model") as mock:
            mock.return_value = MagicMock()
            ProviderFactory.create_model(key)
            mock.assert_called_once()


class TestGoogleModelCreation:
    """Tests for Google model creation."""

    def test_missing_google_package(self):
        """Test error when langchain-google-genai is not installed."""
        key = APIKey(
            name="gemini",
            key="AIza-test",
            provider="google",
            model="gemini-2.5-flash",
        )

        with patch.dict("sys.modules", {"langchain_google_genai": None}):
            with pytest.raises(ImportError) as exc_info:
                ProviderFactory._create_google_model(key, {})

            assert "langchain-google-genai" in str(exc_info.value)
            assert "pip install langwatch[google]" in str(exc_info.value)

    def test_google_model_params(self):
        """Test Google model is created with correct parameters."""
        pytest.importorskip("langchain_google_genai")

        with patch("langwatch.providers.ChatGoogleGenerativeAI") as mock_class:
            mock_class.return_value = MagicMock()

            key = APIKey(
                name="gemini",
                key="AIza-test-key",
                provider="google",
                model="gemini-2.5-flash",
            )

            # Need to patch the import inside the method
            with patch.dict("sys.modules", {"langchain_google_genai": MagicMock(ChatGoogleGenerativeAI=mock_class)}):
                ProviderFactory._create_google_model(key, {})

            mock_class.assert_called_once_with(
                model="gemini-2.5-flash",
                google_api_key="AIza-test-key",
                temperature=0.3,  # Default for Google
                max_retries=0,  # Fail fast
            )

    def test_google_model_with_extra_config(self):
        """Test Google model with extra configuration."""
        pytest.importorskip("langchain_google_genai")

        with patch("langwatch.providers.ChatGoogleGenerativeAI") as mock_class:
            mock_class.return_value = MagicMock()

            key = APIKey(
                name="gemini",
                key="AIza-test",
                provider="google",
                model="gemini-2.5-flash",
                extra_config={"temperature": 0.8, "max_retries": 3},
            )

            with patch.dict("sys.modules", {"langchain_google_genai": MagicMock(ChatGoogleGenerativeAI=mock_class)}):
                ProviderFactory._create_google_model(key, key.extra_config)

            mock_class.assert_called_once_with(
                model="gemini-2.5-flash",
                google_api_key="AIza-test",
                temperature=0.8,
                max_retries=3,
            )


class TestOpenAIModelCreation:
    """Tests for OpenAI model creation."""

    def test_missing_openai_package(self):
        """Test error when langchain-openai is not installed."""
        key = APIKey(
            name="openai",
            key="sk-test",
            provider="openai",
            model="gpt-4",
        )

        with patch.dict("sys.modules", {"langchain_openai": None}):
            with pytest.raises(ImportError) as exc_info:
                ProviderFactory._create_openai_model(key, {})

            assert "langchain-openai" in str(exc_info.value)
            assert "pip install langwatch[openai]" in str(exc_info.value)

    def test_openai_model_params(self):
        """Test OpenAI model is created with correct parameters."""
        pytest.importorskip("langchain_openai")

        mock_class = MagicMock()
        mock_class.return_value = MagicMock()

        key = APIKey(
            name="openai",
            key="sk-test-key",
            provider="openai",
            model="gpt-4",
        )

        with patch.dict("sys.modules", {"langchain_openai": MagicMock(ChatOpenAI=mock_class)}):
            ProviderFactory._create_openai_model(key, {})

        mock_class.assert_called_once_with(
            model="gpt-4",
            api_key="sk-test-key",
            temperature=0.7,  # Default for OpenAI
            max_retries=0,
        )


class TestAnthropicModelCreation:
    """Tests for Anthropic model creation."""

    def test_missing_anthropic_package(self):
        """Test error when langchain-anthropic is not installed."""
        key = APIKey(
            name="claude",
            key="sk-ant-test",
            provider="anthropic",
            model="claude-3-sonnet",
        )

        with patch.dict("sys.modules", {"langchain_anthropic": None}):
            with pytest.raises(ImportError) as exc_info:
                ProviderFactory._create_anthropic_model(key, {})

            assert "langchain-anthropic" in str(exc_info.value)
            assert "pip install langwatch[anthropic]" in str(exc_info.value)

    def test_anthropic_model_params(self):
        """Test Anthropic model is created with correct parameters."""
        pytest.importorskip("langchain_anthropic")

        mock_class = MagicMock()
        mock_class.return_value = MagicMock()

        key = APIKey(
            name="claude",
            key="sk-ant-test-key",
            provider="anthropic",
            model="claude-3-sonnet",
        )

        with patch.dict("sys.modules", {"langchain_anthropic": MagicMock(ChatAnthropic=mock_class)}):
            ProviderFactory._create_anthropic_model(key, {})

        mock_class.assert_called_once_with(
            model="claude-3-sonnet",
            api_key="sk-ant-test-key",
            temperature=0.7,
            max_retries=0,
        )


class TestOpenRouterModelCreation:
    """Tests for OpenRouter model creation."""

    def test_openrouter_model_params(self):
        """Test OpenRouter model is created with correct parameters."""
        pytest.importorskip("langchain_openai")

        mock_class = MagicMock()
        mock_class.return_value = MagicMock()

        key = APIKey(
            name="openrouter",
            key="sk-or-test-key",
            provider="openrouter",
            model="grok-4.1",
        )

        with patch.dict("sys.modules", {"langchain_openai": MagicMock(ChatOpenAI=mock_class)}):
            ProviderFactory._create_openrouter_model(key, {})

        mock_class.assert_called_once_with(
            model="grok-4.1",
            api_key="sk-or-test-key",
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_retries=3,  # More retries for fallback
        )

    def test_openrouter_custom_base_url(self):
        """Test OpenRouter with custom base URL."""
        pytest.importorskip("langchain_openai")

        mock_class = MagicMock()
        mock_class.return_value = MagicMock()

        key = APIKey(
            name="openrouter",
            key="sk-or-test",
            provider="openrouter",
            model="grok-4.1",
            extra_config={"base_url": "https://custom.openrouter.ai/v1"},
        )

        with patch.dict("sys.modules", {"langchain_openai": MagicMock(ChatOpenAI=mock_class)}):
            ProviderFactory._create_openrouter_model(key, key.extra_config)

        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["base_url"] == "https://custom.openrouter.ai/v1"
