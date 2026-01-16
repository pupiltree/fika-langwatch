"""
Provider factory for creating LangChain models from configuration.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

from .key_manager import APIKey

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating LangChain chat models from configuration.

    Supported providers:
        - google: ChatGoogleGenerativeAI (Gemini)
        - openai: ChatOpenAI
        - anthropic: ChatAnthropic
        - openrouter: ChatOpenAI with OpenRouter base_url
    """

    # Default base URLs for providers
    BASE_URLS = {
        "openrouter": "https://openrouter.ai/api/v1",
    }

    @classmethod
    def create_model(cls, key: APIKey) -> "BaseChatModel":
        """
        Create a LangChain chat model from an APIKey.

        Args:
            key: APIKey instance with provider, model, and key info

        Returns:
            LangChain BaseChatModel instance

        Raises:
            ValueError: If provider is not supported
            ImportError: If provider package is not installed
        """
        provider = key.provider.lower()
        extra = key.extra_config or {}

        if provider == "google":
            return cls._create_google_model(key, extra)
        elif provider == "openai":
            return cls._create_openai_model(key, extra)
        elif provider == "anthropic":
            return cls._create_anthropic_model(key, extra)
        elif provider == "openrouter":
            return cls._create_openrouter_model(key, extra)
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported: google, openai, anthropic, openrouter. "
                f"For other providers, create the model manually and pass it directly."
            )

    @classmethod
    def _create_google_model(cls, key: APIKey, extra: Dict[str, Any]) -> "BaseChatModel":
        """Create Google Gemini model."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langwatch[google]"
            )

        return ChatGoogleGenerativeAI(
            model=key.model,
            google_api_key=key.key,
            temperature=extra.get("temperature", 0.3),
            max_retries=extra.get("max_retries", 0),  # Fail fast for fallback
            **{k: v for k, v in extra.items() if k not in ["temperature", "max_retries"]},
        )

    @classmethod
    def _create_openai_model(cls, key: APIKey, extra: Dict[str, Any]) -> "BaseChatModel":
        """Create OpenAI model."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. "
                "Install with: pip install langwatch[openai]"
            )

        return ChatOpenAI(
            model=key.model,
            api_key=key.key,
            temperature=extra.get("temperature", 0.7),
            max_retries=extra.get("max_retries", 0),
            **{k: v for k, v in extra.items() if k not in ["temperature", "max_retries"]},
        )

    @classmethod
    def _create_anthropic_model(cls, key: APIKey, extra: Dict[str, Any]) -> "BaseChatModel":
        """Create Anthropic Claude model."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. "
                "Install with: pip install langwatch[anthropic]"
            )

        return ChatAnthropic(
            model=key.model,
            api_key=key.key,
            temperature=extra.get("temperature", 0.7),
            max_retries=extra.get("max_retries", 0),
            **{k: v for k, v in extra.items() if k not in ["temperature", "max_retries"]},
        )

    @classmethod
    def _create_openrouter_model(cls, key: APIKey, extra: Dict[str, Any]) -> "BaseChatModel":
        """Create OpenRouter model (uses ChatOpenAI with custom base_url)."""
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. "
                "Install with: pip install langwatch[openai]"
            )

        return ChatOpenAI(
            model=key.model,
            api_key=key.key,
            base_url=extra.get("base_url", cls.BASE_URLS["openrouter"]),
            temperature=extra.get("temperature", 0.7),
            max_retries=extra.get("max_retries", 3),  # More retries for fallback
            **{k: v for k, v in extra.items() if k not in ["temperature", "max_retries", "base_url"]},
        )
