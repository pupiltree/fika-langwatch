"""
Tests for EmailTemplates class.
"""

import pytest
from datetime import datetime

from langwatch.alerts.base import AlertPayload
from langwatch.templates.email_templates import EmailTemplates


class TestEmailTemplates:
    """Tests for EmailTemplates class."""

    @pytest.fixture
    def warning_payload(self):
        """Warning severity payload."""
        return AlertPayload(
            title="API Key Warning",
            message="Primary key failed, using fallback",
            severity="warning",
            alert_type="key_failure",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            details={"provider": "google"},
            failed_key_name="gemini-1",
            failed_provider="google",
            error_message="Quota exceeded",
        )

    @pytest.fixture
    def critical_payload(self):
        """Critical severity payload."""
        return AlertPayload(
            title="Critical API Failure",
            message="All keys have failed",
            severity="critical",
            alert_type="key_failure",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            details={},
            failed_key_name="fallback",
            failed_provider="openrouter",
            error_message="Service unavailable",
        )

    @pytest.fixture
    def info_payload(self):
        """Info severity payload."""
        return AlertPayload(
            title="System Info",
            message="All systems operational",
            severity="info",
            alert_type="status",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            details={},
        )

    @pytest.fixture
    def error_payload(self):
        """Error severity payload."""
        return AlertPayload(
            title="API Error",
            message="Error occurred",
            severity="error",
            alert_type="error",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            details={},
        )


class TestBuildAlertEmail:
    """Tests for build_alert_email method."""

    def test_returns_valid_html(self, sample_alert_payload):
        """Test that returned content is valid HTML."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_includes_title(self, sample_alert_payload):
        """Test that title is included in HTML."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.title in html

    def test_includes_message(self, sample_alert_payload):
        """Test that message is included in HTML."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.message in html

    def test_includes_severity(self, sample_alert_payload):
        """Test that severity is displayed."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.severity.upper() in html

    def test_includes_timestamp(self, sample_alert_payload):
        """Test that timestamp is formatted and included."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        # Timestamp should be formatted as "2024-01-15 10:30:00"
        assert "2024-01-15 10:30:00" in html

    def test_includes_alert_type(self, sample_alert_payload):
        """Test that alert type is included."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.alert_type in html

    def test_includes_failed_key_info(self, sample_alert_payload):
        """Test that failed key information is included."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.failed_key_name in html
        assert sample_alert_payload.failed_provider in html

    def test_includes_error_message(self, sample_alert_payload):
        """Test that error message is included."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert sample_alert_payload.error_message in html

    def test_includes_fallback_info_when_present(self):
        """Test that fallback info is included when present."""
        payload = AlertPayload(
            title="Fallback Active",
            message="Using fallback",
            severity="warning",
            alert_type="fallback_activated",
            timestamp=datetime.now(),
            details={},
            failed_key_name="primary",
            failed_provider="google",
            fallback_key_name="backup",
            fallback_provider="openrouter",
        )

        html = EmailTemplates.build_alert_email(payload)

        assert "backup" in html
        assert "Fallback" in html

    def test_handles_missing_optional_fields(self):
        """Test handling of payload with missing optional fields."""
        payload = AlertPayload(
            title="Simple Alert",
            message="Simple message",
            severity="info",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Should not raise, should produce valid HTML
        assert "<!DOCTYPE html>" in html
        assert "Simple Alert" in html


class TestSeverityColors:
    """Tests for severity-based color coding."""

    def test_warning_color(self):
        """Test warning severity uses correct color."""
        payload = AlertPayload(
            title="Warning",
            message="Warning message",
            severity="warning",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Warning color is #FFC107
        assert "#FFC107" in html

    def test_critical_color(self):
        """Test critical severity uses correct color."""
        payload = AlertPayload(
            title="Critical",
            message="Critical message",
            severity="critical",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Critical color is #DC3545
        assert "#DC3545" in html

    def test_info_color(self):
        """Test info severity uses correct color."""
        payload = AlertPayload(
            title="Info",
            message="Info message",
            severity="info",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Info color is #4A90E2
        assert "#4A90E2" in html

    def test_error_color(self):
        """Test error severity uses correct color."""
        payload = AlertPayload(
            title="Error",
            message="Error message",
            severity="error",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Error color is #E74C3C
        assert "#E74C3C" in html

    def test_unknown_severity_defaults_to_warning(self):
        """Test unknown severity defaults to warning colors."""
        payload = AlertPayload(
            title="Unknown",
            message="Unknown severity",
            severity="unknown_severity",
            alert_type="test",
            timestamp=datetime.now(),
            details={},
        )

        html = EmailTemplates.build_alert_email(payload)

        # Should use warning color #FFC107 as default
        assert "#FFC107" in html


class TestBaseTemplate:
    """Tests for _base_template method."""

    def test_base_template_includes_content(self):
        """Test that base template includes provided content."""
        content = "<div>Custom Content</div>"
        color = {"primary": "#000000", "bg": "#FFFFFF"}

        html = EmailTemplates._base_template(content, "Test Title", color)

        assert "Custom Content" in html

    def test_base_template_includes_title(self):
        """Test that base template includes title."""
        content = "<div>Content</div>"
        color = {"primary": "#000000", "bg": "#FFFFFF"}

        html = EmailTemplates._base_template(content, "My Title", color)

        assert "<title>My Title</title>" in html

    def test_base_template_includes_styles(self):
        """Test that base template includes CSS styles."""
        content = "<div>Content</div>"
        color = {"primary": "#FF0000", "bg": "#FFE0E0"}

        html = EmailTemplates._base_template(content, "Title", color)

        assert "<style>" in html
        assert "#FF0000" in html  # Primary color should be in styles
        assert "#FFE0E0" in html  # Background color should be in styles

    def test_base_template_is_responsive(self):
        """Test that base template includes viewport meta tag."""
        content = "<div>Content</div>"
        color = {"primary": "#000000", "bg": "#FFFFFF"}

        html = EmailTemplates._base_template(content, "Title", color)

        assert 'name="viewport"' in html

    def test_base_template_includes_email_container(self):
        """Test that base template includes email container class."""
        content = "<div>Content</div>"
        color = {"primary": "#000000", "bg": "#FFFFFF"}

        html = EmailTemplates._base_template(content, "Title", color)

        assert "email-container" in html


class TestHTMLStructure:
    """Tests for HTML structure and styling."""

    def test_includes_header_section(self, sample_alert_payload):
        """Test that HTML includes header section."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="header"' in html

    def test_includes_content_section(self, sample_alert_payload):
        """Test that HTML includes content section."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="content"' in html

    def test_includes_footer_section(self, sample_alert_payload):
        """Test that HTML includes footer section."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="footer"' in html
        assert "LangWatch Alert System" in html

    def test_includes_alert_box(self, sample_alert_payload):
        """Test that HTML includes alert box."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="alert-box"' in html

    def test_includes_info_sections(self, sample_alert_payload):
        """Test that HTML includes info sections."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="info-section"' in html

    def test_includes_status_badges(self, sample_alert_payload):
        """Test that HTML includes status badges."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert "status-badge" in html

    def test_error_details_styling(self, sample_alert_payload):
        """Test that error details have proper styling class."""
        html = EmailTemplates.build_alert_email(sample_alert_payload)

        assert 'class="error-details"' in html
