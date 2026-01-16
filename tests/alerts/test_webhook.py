"""
Tests for WebhookAlert class.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from langwatch.alerts.webhook import WebhookAlert


class TestWebhookAlertInit:
    """Tests for WebhookAlert initialization."""

    def test_basic_init(self):
        """Test basic WebhookAlert initialization."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        assert alert.url == "https://api.example.com/alerts"
        assert alert.headers == {}
        assert alert.method == "POST"
        assert alert.timeout == 10.0

    def test_init_with_headers(self):
        """Test WebhookAlert with custom headers."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            headers={
                "Authorization": "Bearer token123",
                "X-Custom-Header": "value",
            },
        )

        assert alert.headers["Authorization"] == "Bearer token123"
        assert alert.headers["X-Custom-Header"] == "value"

    def test_init_custom_method(self):
        """Test WebhookAlert with custom HTTP method."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            method="PUT",
        )

        assert alert.method == "PUT"

    def test_method_normalized_to_uppercase(self):
        """Test that HTTP method is normalized to uppercase."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            method="put",  # lowercase
        )

        assert alert.method == "PUT"

    def test_init_custom_timeout(self):
        """Test WebhookAlert with custom timeout."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            timeout=30.0,
        )

        assert alert.timeout == 30.0

    def test_name_property(self):
        """Test name property returns 'webhook'."""
        alert = WebhookAlert(url="https://api.example.com/alerts")
        assert alert.name == "webhook"


class TestWebhookAlertSend:
    """Tests for WebhookAlert send functionality."""

    @pytest.mark.asyncio
    async def test_send_async_missing_httpx(self, sample_alert_payload):
        """Test error when httpx is not installed."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        with patch.dict("sys.modules", {"httpx": None}):
            result = await alert.send_async(sample_alert_payload)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_success(self, sample_alert_payload):
        """Test successful webhook send."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is True
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_async_201_success(self, sample_alert_payload):
        """Test 201 status code is treated as success."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        mock_response = MagicMock()
        mock_response.status_code = 201

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_async_4xx_error(self, sample_alert_payload):
        """Test handling of 4xx errors."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_5xx_error(self, sample_alert_payload):
        """Test handling of 5xx errors."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_network_error(self, sample_alert_payload):
        """Test handling of network errors."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=Exception("Connection timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await alert.send_async(sample_alert_payload)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_uses_correct_method(self, sample_alert_payload):
        """Test that correct HTTP method is used."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            method="PUT",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await alert.send_async(sample_alert_payload)

            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["method"] == "PUT"

    @pytest.mark.asyncio
    async def test_send_async_includes_headers(self, sample_alert_payload):
        """Test that custom headers are included."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            headers={"Authorization": "Bearer secret"},
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await alert.send_async(sample_alert_payload)

            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer secret"

    @pytest.mark.asyncio
    async def test_send_async_payload_is_dict(self, sample_alert_payload):
        """Test that payload is sent as JSON dict."""
        alert = WebhookAlert(url="https://api.example.com/alerts")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await alert.send_async(sample_alert_payload)

            call_kwargs = mock_client.request.call_args[1]
            json_payload = call_kwargs["json"]

            assert isinstance(json_payload, dict)
            assert json_payload["title"] == sample_alert_payload.title
            assert json_payload["severity"] == sample_alert_payload.severity

    @pytest.mark.asyncio
    async def test_send_async_uses_timeout(self, sample_alert_payload):
        """Test that custom timeout is used."""
        alert = WebhookAlert(
            url="https://api.example.com/alerts",
            timeout=30.0,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            await alert.send_async(sample_alert_payload)

            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["timeout"] == 30.0
