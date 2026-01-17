"""
LangWatch - LangChain wrapper with automatic fallback and alert notifications.

Copyright (c) 2026 FIKA Private Limited. All Rights Reserved.

Usage:
    from langwatch import ChatWithFallback
    from langwatch.alerts import EmailAlert, SlackAlert

    chat = ChatWithFallback.from_config(
        models=[
            {"name": "gemini-1", "provider": "google", "model": "gemini-2.5-flash", "api_key": "..."},
            {"name": "fallback", "provider": "openrouter", "model": "grok-4.1", "api_key": "...", "is_fallback": True},
        ],
        alerts=[EmailAlert(...), SlackAlert(...)],
    )

    # Bind tools to ALL models
    chat_with_tools = chat.bind_tools([tool1, tool2])

    # Use like any LangChain model
    response = await chat_with_tools.ainvoke(messages)
"""

from .langchain.chat_with_fallback import ChatWithFallback
from .key_manager import KeyManager, APIKey
from .rate_limiter import InMemoryRateLimiter
from .providers import ProviderFactory

__version__ = "0.3.3"
__author__ = "FIKA Private Limited"

__all__ = [
    # Main class
    "ChatWithFallback",
    # Supporting classes
    "KeyManager",
    "APIKey",
    "InMemoryRateLimiter",
    "ProviderFactory",
    # Version
    "__version__",
]
