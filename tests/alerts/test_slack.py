"""
Tests for SlackAlert class.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from langwatch.alerts.slack import SlackAlert


class TestSlackAlertInit:
    """Tests for SlackAlert initialization."""

    def test_basic_init(self):
        """Test basic SlackAlert initialization."""
        alert = SlackAlert(
            webhook_url="https://hooks.slack.com/services/T123/B456/xxx",
        )

        assert alert.webhook_url == "https://hooks.slack.com/services/T123/B456/xxx"
        assert alert.channel is None
        assert alert.username == "LangWatch Alerts"
        assert alert.icon_emoji == ":warning:"

    def test_init_with_channel(self):
        """Test SlackAlert with custom channel."""
        alert = SlackAlert(
            webhook_url="https://hooks.slack.com/services/xxx",
            channel="#alerts",
        )

        assert alert.channel == "#alerts"

    def test_init_custom_username_emoji(self):
        """Test SlackAlert with custom username and emoji."""
        alert = SlackAlert(
            webhook_url="https://hooks.slack.com/services/xxx",
            username="Custom Bot",
            icon_emoji=":robot_face:",
        )

        assert alert.username == "Custom Bot"
        assert alert.icon_emoji == ":robot_face:"

    def test_name_property(self):
        """Test name property returns 'slack'."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")
        assert alert.name == "slack"


class TestSlackAlertSend:
    """Tests for SlackAlert send functionality."""

    @pytest.mark.asyncio
    async def test_send_async_missing_httpx(self, sample_alert_payload):
        """Test error when httpx is not installed."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        with patch.dict("sys.modules", {"httpx": None}):
            result = await alert.send_async(sample_alert_payload)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_success(self, sample_alert_payload):
        """Test successful Slack send."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_async_api_error(self, sample_alert_payload):
        """Test handling of Slack API errors."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_network_error(self, sample_alert_payload):
        """Test handling of network errors."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is False


class TestSlackAlertMessage:
    """Tests for Slack message building."""

    def test_build_slack_message_structure(self, sample_alert_payload):
        """Test Slack message structure."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        message = alert._build_slack_message(sample_alert_payload)

        assert "blocks" in message
        assert "attachments" in message
        assert len(message["blocks"]) > 0

    def test_build_slack_message_with_channel(self, sample_alert_payload):
        """Test Slack message includes channel when set."""
        alert = SlackAlert(
            webhook_url="https://hooks.slack.com/services/xxx",
            channel="#my-channel",
        )

        message = alert._build_slack_message(sample_alert_payload)

        assert message["channel"] == "#my-channel"

    def test_build_slack_message_includes_failed_key(self, sample_alert_payload):
        """Test Slack message includes failed key info."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        message = alert._build_slack_message(sample_alert_payload)

        # Check that failed key info is in the message
        message_str = str(message)
        assert "gemini-1" in message_str

    def test_build_slack_message_includes_error(self, sample_alert_payload):
        """Test Slack message includes error message."""
        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        message = alert._build_slack_message(sample_alert_payload)

        message_str = str(message)
        assert "API quota exceeded" in message_str

    def test_build_slack_message_severity_colors(self):
        """Test different severity levels produce different colors."""
        from langwatch.alerts.base import AlertPayload
        from datetime import datetime

        alert = SlackAlert(webhook_url="https://hooks.slack.com/services/xxx")

        warning_payload = AlertPayload(
            title="Warning",
            message="Warning message",
            severity="warning",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        critical_payload = AlertPayload(
            title="Critical",
            message="Critical message",
            severity="critical",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        warning_msg = alert._build_slack_message(warning_payload)
        critical_msg = alert._build_slack_message(critical_payload)

        # Colors should be different
        warning_color = warning_msg["attachments"][0]["color"]
        critical_color = critical_msg["attachments"][0]["color"]

        assert warning_color != critical_color
