"""
HTML email templates for alert notifications.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..alerts.base import AlertPayload


class EmailTemplates:
    """HTML email templates with CSS styling."""

    @staticmethod
    def build_alert_email(payload: "AlertPayload") -> str:
        """Build complete HTML email from alert payload."""

        # Color schemes based on severity
        colors = {
            "info": {"primary": "#4A90E2", "bg": "#E7F0FD"},
            "warning": {"primary": "#FFC107", "bg": "#FFF3CD"},
            "error": {"primary": "#E74C3C", "bg": "#F8D7DA"},
            "critical": {"primary": "#DC3545", "bg": "#F8D7DA"},
        }

        color = colors.get(payload.severity.lower(), colors["warning"])

        # Build failed keys section
        failed_info = ""
        if payload.failed_key_name:
            failed_info = f"""
            <div class="info-section">
                <h3>Failed Key</h3>
                <div class="info-row">
                    <span class="info-label">Key Name:</span>
                    <span class="info-value"><span class="status-badge status-failed">{payload.failed_key_name}</span></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Provider:</span>
                    <span class="info-value">{payload.failed_provider or 'Unknown'}</span>
                </div>
            </div>
            """

        # Build fallback section
        fallback_info = ""
        if payload.fallback_key_name:
            fallback_info = f"""
            <div class="alert-box" style="background: #d4edda; border-left-color: #28a745;">
                <h2 style="color: #28a745;">Fallback Active</h2>
                <p><span class="status-badge status-active">{payload.fallback_key_name}</span> ({payload.fallback_provider or 'Unknown'})</p>
            </div>
            """

        # Build error section
        error_section = ""
        if payload.error_message:
            error_section = f"""
            <div class="info-section">
                <h3>Error Details</h3>
                <div class="error-details">{payload.error_message}</div>
            </div>
            """

        content = f"""
        <div class="header">
            <h1>{payload.title}</h1>
        </div>

        <div class="content">
            <div class="alert-box">
                <h2>{payload.severity.upper()}</h2>
                <p>{payload.message}</p>
            </div>

            <div class="info-section">
                <h3>Alert Information</h3>
                <div class="info-row">
                    <span class="info-label">Timestamp:</span>
                    <span class="info-value"><span class="timestamp">{payload.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</span></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Alert Type:</span>
                    <span class="info-value">{payload.alert_type}</span>
                </div>
            </div>

            {failed_info}
            {fallback_info}
            {error_section}
        </div>

        <div class="footer">
            <p><strong>LangWatch Alert System</strong></p>
            <p>This is an automated alert. Please do not reply to this email.</p>
        </div>
        """

        return EmailTemplates._base_template(content, payload.title, color)

    @staticmethod
    def _base_template(content: str, title: str, color: dict) -> str:
        """Base HTML template with CSS styling."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: 0;
            padding: 40px 20px;
            color: #333;
            line-height: 1.6;
        }}
        .email-container {{
            max-width: 700px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: {color['primary']};
            color: #ffffff;
            padding: 30px 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 40px;
        }}
        .alert-box {{
            background: {color['bg']};
            border-left: 5px solid {color['primary']};
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .alert-box h2 {{
            margin: 0 0 10px 0;
            color: {color['primary']};
            font-size: 18px;
        }}
        .info-section {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .info-section h3 {{
            margin: 0 0 15px 0;
            color: #495057;
            font-size: 16px;
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 10px;
        }}
        .info-row {{
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            font-weight: 600;
            color: #495057;
            display: inline-block;
            min-width: 120px;
        }}
        .info-value {{
            color: #6c757d;
        }}
        .error-details {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-failed {{
            background: #fee;
            color: #c00;
        }}
        .status-active {{
            background: #d4edda;
            color: #155724;
        }}
        .timestamp {{
            font-family: monospace;
            background: #f1f3f5;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            border-top: 1px solid #dee2e6;
        }}
        .footer p {{
            margin: 5px 0;
            color: #6c757d;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        {content}
    </div>
</body>
</html>
"""
