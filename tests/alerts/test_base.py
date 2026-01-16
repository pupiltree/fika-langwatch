"""
Tests for AlertPayload and AlertChannel base classes.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from langwatch.alerts.base import AlertPayload, AlertChannel


class TestAlertPayload:
    """Tests for AlertPayload dataclass."""

    def test_alert_payload_creation(self):
        """Test basic AlertPayload creation."""
        payload = AlertPayload(
            title="Test Alert",
            message="This is a test message",
            severity="warning",
            alert_type="test",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            details={"key": "value"},
        )

        assert payload.title == "Test Alert"
        assert payload.message == "This is a test message"
        assert payload.severity == "warning"
        assert payload.alert_type == "test"
        assert payload.details == {"key": "value"}

    def test_alert_payload_optional_fields(self):
        """Test AlertPayload optional fields default to None."""
        payload = AlertPayload(
            title="Test",
            message="Test",
            severity="info",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        assert payload.failed_key_name is None
        assert payload.failed_provider is None
        assert payload.fallback_key_name is None
        assert payload.fallback_provider is None
        assert payload.error_message is None

    def test_alert_payload_with_all_fields(self, sample_alert_payload):
        """Test AlertPayload with all fields populated."""
        assert sample_alert_payload.failed_key_name == "gemini-1"
        assert sample_alert_payload.failed_provider == "google"
        assert sample_alert_payload.error_message == "API quota exceeded"

    def test_to_dict(self, sample_alert_payload):
        """Test AlertPayload serialization to dict."""
        result = sample_alert_payload.to_dict()

        assert result["title"] == "API Key Failure - gemini-1"
        assert result["message"] == "API key 'gemini-1' (primary) has failed."
        assert result["severity"] == "warning"
        assert result["alert_type"] == "key_failure"
        assert result["timestamp"] == "2024-01-15T10:30:00"
        assert result["failed_key_name"] == "gemini-1"
        assert result["failed_provider"] == "google"
        assert isinstance(result["details"], dict)

    def test_to_dict_with_none_fields(self):
        """Test to_dict with None optional fields."""
        payload = AlertPayload(
            title="Test",
            message="Test",
            severity="info",
            alert_type="test",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            details={},
        )

        result = payload.to_dict()

        assert result["failed_key_name"] is None
        assert result["fallback_key_name"] is None


class TestAlertChannelABC:
    """Tests for AlertChannel abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that AlertChannel cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AlertChannel()

    def test_concrete_implementation(self, mock_alert_channel):
        """Test concrete implementation of AlertChannel."""
        assert mock_alert_channel.name == "mock"

    @pytest.mark.asyncio
    async def test_send_async(self, mock_alert_channel, sample_alert_payload):
        """Test async send method."""
        result = await mock_alert_channel.send_async(sample_alert_payload)

        assert result is True
        assert len(mock_alert_channel.sent_payloads) == 1
        assert mock_alert_channel.sent_payloads[0] == sample_alert_payload

    @pytest.mark.asyncio
    async def test_send_async_failure(self, mock_alert_channel, sample_alert_payload):
        """Test async send method failure."""
        mock_alert_channel.should_fail = True

        result = await mock_alert_channel.send_async(sample_alert_payload)

        assert result is False
        assert len(mock_alert_channel.sent_payloads) == 0

    def test_sync_send_wrapper(self, mock_alert_channel, sample_alert_payload):
        """Test synchronous send wrapper."""
        result = mock_alert_channel.send(sample_alert_payload)

        assert result is True
        assert len(mock_alert_channel.sent_payloads) == 1
