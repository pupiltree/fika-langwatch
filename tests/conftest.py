"""
Shared pytest fixtures for langwatch tests.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from langwatch import APIKey, KeyManager, InMemoryRateLimiter
from langwatch.alerts.base import AlertPayload, AlertChannel


# ============================================================================
# API Key Fixtures
# ============================================================================


@pytest.fixture
def sample_api_key():
    """Single API key for testing."""
    return APIKey(
        name="test-key",
        key="sk-test-1234567890abcdef",
        provider="openai",
        model="gpt-4",
    )


@pytest.fixture
def primary_api_key():
    """Primary API key (non-fallback)."""
    return APIKey(
        name="primary",
        key="sk-primary-1234567890",
        provider="openai",
        model="gpt-4",
        is_fallback=False,
    )


@pytest.fixture
def fallback_api_key():
    """Fallback API key."""
    return APIKey(
        name="fallback",
        key="sk-fallback-0987654321",
        provider="anthropic",
        model="claude-3-sonnet",
        is_fallback=True,
    )


@pytest.fixture
def sample_key_configs():
    """List of key configuration dictionaries."""
    return [
        {
            "name": "gemini-1",
            "key": "AIzaSyA-test-key-1",
            "provider": "google",
            "model": "gemini-2.5-flash",
        },
        {
            "name": "gemini-2",
            "key": "AIzaSyA-test-key-2",
            "provider": "google",
            "model": "gemini-2.5-flash",
        },
        {
            "name": "fallback",
            "key": "sk-or-test-fallback",
            "provider": "openrouter",
            "model": "grok-4.1",
            "is_fallback": True,
        },
    ]


# ============================================================================
# Key Manager Fixtures
# ============================================================================


@pytest.fixture
def key_manager(sample_key_configs):
    """KeyManager instance with sample keys."""
    return KeyManager(sample_key_configs)


@pytest.fixture
def key_manager_all_failed(key_manager):
    """KeyManager with all primary keys marked as failed."""
    key_manager.mark_failed("gemini-1", "API quota exceeded")
    key_manager.mark_failed("gemini-2", "Invalid API key")
    return key_manager


# ============================================================================
# Rate Limiter Fixtures
# ============================================================================


@pytest.fixture
def rate_limiter():
    """InMemoryRateLimiter with 60 second default cooldown."""
    return InMemoryRateLimiter(default_cooldown=60)


@pytest.fixture
def rate_limiter_short():
    """InMemoryRateLimiter with 1 second cooldown for fast tests."""
    return InMemoryRateLimiter(default_cooldown=1)


# ============================================================================
# Alert Fixtures
# ============================================================================


@pytest.fixture
def sample_alert_payload():
    """Sample AlertPayload for testing."""
    return AlertPayload(
        title="API Key Failure - gemini-1",
        message="API key 'gemini-1' (primary) has failed.",
        severity="warning",
        alert_type="key_failure",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        details={
            "app_name": "TestApp",
            "key_name": "gemini-1",
            "key_type": "primary",
            "provider": "google",
            "model": "gemini-2.5-flash",
            "api_key_masked": "AIza...st-1",
            "is_fallback": False,
            "failure_count": 1,
            "error_truncated": "API quota exceeded",
        },
        failed_key_name="gemini-1",
        failed_provider="google",
        fallback_key_name=None,
        fallback_provider=None,
        error_message="API quota exceeded",
    )


@pytest.fixture
def critical_alert_payload():
    """Critical severity AlertPayload (fallback failed)."""
    return AlertPayload(
        title="[TestApp] API Key Failure - fallback",
        message="[TestApp] API key 'fallback' (fallback) has failed.",
        severity="critical",
        alert_type="key_failure",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        details={
            "app_name": "TestApp",
            "key_name": "fallback",
            "key_type": "fallback",
            "provider": "openrouter",
            "model": "grok-4.1",
            "is_fallback": True,
            "failure_count": 3,
        },
        failed_key_name="fallback",
        failed_provider="openrouter",
        error_message="Service unavailable",
    )


# ============================================================================
# Mock Alert Channel
# ============================================================================


class MockAlertChannel(AlertChannel):
    """Mock alert channel for testing."""

    def __init__(self):
        self.sent_payloads = []
        self.should_fail = False

    @property
    def name(self) -> str:
        return "mock"

    async def send_async(self, payload: AlertPayload) -> bool:
        if self.should_fail:
            return False
        self.sent_payloads.append(payload)
        return True


@pytest.fixture
def mock_alert_channel():
    """Mock alert channel that records sent payloads."""
    return MockAlertChannel()


# ============================================================================
# Mock LangChain Model Fixtures
# ============================================================================


@pytest.fixture
def mock_chat_model():
    """Mock LangChain chat model."""
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.messages import AIMessage

    model = MagicMock()
    model._llm_type = "mock"

    # Sync response
    mock_result = ChatResult(
        generations=[ChatGeneration(message=AIMessage(content="Mock response"))]
    )
    model._generate = MagicMock(return_value=mock_result)

    # Async response
    model._agenerate = AsyncMock(return_value=mock_result)

    # bind_tools support
    model.bind_tools = MagicMock(return_value=model)

    return model


@pytest.fixture
def mock_failing_model():
    """Mock model that always fails."""
    model = MagicMock()
    model._llm_type = "mock_failing"
    model._generate = MagicMock(side_effect=Exception("API Error: quota exceeded"))
    model._agenerate = AsyncMock(side_effect=Exception("API Error: quota exceeded"))
    model.bind_tools = MagicMock(return_value=model)
    return model


@pytest.fixture
def mock_models_with_fallback(mock_chat_model, mock_failing_model):
    """List of models where first fails, second succeeds."""
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.messages import AIMessage

    failing = MagicMock()
    failing._llm_type = "failing"
    failing._generate = MagicMock(side_effect=Exception("Primary failed"))
    failing._agenerate = AsyncMock(side_effect=Exception("Primary failed"))
    failing.bind_tools = MagicMock(return_value=failing)

    success_result = ChatResult(
        generations=[ChatGeneration(message=AIMessage(content="Fallback response"))]
    )
    success = MagicMock()
    success._llm_type = "success"
    success._generate = MagicMock(return_value=success_result)
    success._agenerate = AsyncMock(return_value=success_result)
    success.bind_tools = MagicMock(return_value=success)

    return [failing, success]
