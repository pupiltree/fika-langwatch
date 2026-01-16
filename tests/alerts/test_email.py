"""
Tests for EmailAlert class.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from langwatch.alerts.email import EmailAlert


class TestEmailAlertInit:
    """Tests for EmailAlert initialization."""

    def test_basic_init(self):
        """Test basic EmailAlert initialization."""
        alert = EmailAlert(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@example.com",
            password="password123",
            to=["recipient@example.com"],
        )

        assert alert.smtp_server == "smtp.gmail.com"
        assert alert.smtp_port == 587
        assert alert.username == "test@example.com"
        assert alert.to == ["recipient@example.com"]
        assert alert.use_tls is True  # Default

    def test_init_with_cc_bcc(self):
        """Test EmailAlert with CC and BCC."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        assert alert.cc == ["cc@example.com"]
        assert alert.bcc == ["bcc@example.com"]

    def test_init_custom_from_name(self):
        """Test EmailAlert with custom from name."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
            from_name="Custom Alerts",
        )

        assert alert.from_name == "Custom Alerts"

    def test_name_property(self):
        """Test name property returns 'email'."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        assert alert.name == "email"


class TestEmailAlertSend:
    """Tests for EmailAlert send functionality."""

    @pytest.mark.asyncio
    async def test_send_async_missing_aiosmtplib(self, sample_alert_payload):
        """Test error when aiosmtplib is not installed."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        with patch.dict("sys.modules", {"aiosmtplib": None}):
            result = await alert.send_async(sample_alert_payload)
            # Should return False gracefully
            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_success(self, sample_alert_payload):
        """Test successful email send."""
        pytest.importorskip("aiosmtplib")

        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        with patch("langwatch.alerts.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await alert.send_async(sample_alert_payload)

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_async_with_cc(self, sample_alert_payload):
        """Test email send with CC recipients."""
        pytest.importorskip("aiosmtplib")

        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
            cc=["cc@example.com"],
        )

        with patch("langwatch.alerts.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await alert.send_async(sample_alert_payload)

            # Verify message was created with CC
            call_args = mock_send.call_args
            message = call_args[0][0]  # First positional arg
            assert "Cc" in message

    @pytest.mark.asyncio
    async def test_send_async_smtp_error(self, sample_alert_payload):
        """Test handling of SMTP errors."""
        pytest.importorskip("aiosmtplib")

        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        with patch("langwatch.alerts.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP connection failed")

            result = await alert.send_async(sample_alert_payload)

            assert result is False


class TestEmailAlertSubject:
    """Tests for email subject building."""

    def test_build_subject_warning(self, sample_alert_payload):
        """Test subject for warning severity."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        subject = alert._build_subject(sample_alert_payload)

        assert sample_alert_payload.title in subject

    def test_build_subject_critical(self, critical_alert_payload):
        """Test subject for critical severity."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        subject = alert._build_subject(critical_alert_payload)

        assert critical_alert_payload.title in subject


class TestEmailAlertHTML:
    """Tests for email HTML building."""

    def test_build_html_calls_templates(self, sample_alert_payload):
        """Test that _build_html uses EmailTemplates."""
        alert = EmailAlert(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password",
            to=["to@example.com"],
        )

        html = alert._build_html(sample_alert_payload)

        assert "<!DOCTYPE html>" in html
        assert sample_alert_payload.title in html
