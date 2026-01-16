"""
HTML email templates for alert notifications.
Email-client compatible with tables and inline styles.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..alerts.base import AlertPayload


class EmailTemplates:
    """HTML email templates optimized for email clients."""

    @staticmethod
    def build_alert_email(payload: "AlertPayload") -> str:
        """Build complete HTML email from alert payload."""

        # Color schemes based on severity
        colors = {
            "info": {"primary": "#00d4ff", "bg": "#0a1929", "badge_bg": "#0d2137"},
            "warning": {"primary": "#ffaa00", "bg": "#1a1500", "badge_bg": "#2d2200"},
            "error": {"primary": "#ff4757", "bg": "#1a0a0a", "badge_bg": "#2d1010"},
            "critical": {"primary": "#ff0055", "bg": "#1a0011", "badge_bg": "#2d001a"},
        }

        color = colors.get(payload.severity.lower(), colors["warning"])

        # Get details from payload
        details = payload.details or {}
        app_name = details.get("app_name", "")
        key_name = details.get("key_name", payload.failed_key_name or "Unknown")
        key_type = details.get("key_type", "primary")
        provider = details.get("provider") or payload.failed_provider or "N/A"
        model = details.get("model") or "N/A"
        api_key_masked = details.get("api_key_masked") or "***"
        failure_count = details.get("failure_count", 0)
        error_truncated = details.get("error_truncated") or payload.error_message or "No details"

        # App name badge
        app_badge_html = ""
        if app_name:
            app_badge_html = f'''
            <tr>
                <td align="center" style="padding-bottom: 16px;">
                    <span style="display: inline-block; background: {color['badge_bg']}; border: 1px solid {color['primary']}; color: {color['primary']}; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{app_name}</span>
                </td>
            </tr>
            '''

        # Severity emoji
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(payload.severity.lower(), "⚠️")

        # Type badge color
        type_color = "#00d4ff" if key_type != "fallback" else "#ffaa00"
        type_bg = "#0d2137" if key_type != "fallback" else "#2d2200"

        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{payload.title}</title>
    <!--[if mso]>
    <style type="text/css">
        table {{ border-collapse: collapse; }}
        td {{ font-family: Arial, sans-serif; }}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #0a0a0f;">
        <tr>
            <td align="center" style="padding: 40px 20px;">

                <!-- Main Container -->
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #12121a; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.4);">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a1a2e 0%, #0f0f19 100%); padding: 40px 32px; text-align: center; border-bottom: 1px solid #2a2a3e;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                {app_badge_html}
                                <tr>
                                    <td align="center" style="padding-bottom: 20px;">
                                        <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #ffffff;">{payload.title}</h1>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center">
                                        <span style="display: inline-block; background: {color['badge_bg']}; border: 1px solid {color['primary']}; color: {color['primary']}; padding: 10px 24px; border-radius: 30px; font-size: 14px; font-weight: 600; letter-spacing: 2px;">
                                            {severity_emoji} {payload.severity.upper()}
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Alert Message -->
                    <tr>
                        <td style="padding: 32px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: {color['bg']}; border-left: 4px solid {color['primary']}; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 24px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td style="font-size: 32px; width: 50px; vertical-align: top;">⚡</td>
                                                <td>
                                                    <h2 style="margin: 0 0 12px 0; font-size: 18px; font-weight: 600; color: #ffffff;">Alert Triggered</h2>
                                                    <p style="margin: 0; font-size: 14px; color: #a1a1aa; line-height: 1.6;">API key '<strong style="color: {color['primary']};">{key_name}</strong>' ({key_type}) has failed.</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Info Cards -->
                    <tr>
                        <td style="padding: 0 32px 32px 32px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <!-- Key Information Card -->
                                    <td width="48%" valign="top" style="padding-right: 12px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px; overflow: hidden;">
                                            <tr>
                                                <td style="background: #1f1f33; padding: 16px 20px; border-bottom: 1px solid #2a2a3e;">
                                                    <span style="font-size: 16px; margin-right: 8px;">🔑</span>
                                                    <span style="font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Key Information</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 20px;">
                                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                                        <tr>
                                                            <td style="padding: 8px 0; border-bottom: 1px solid #2a2a3e;">
                                                                <span style="font-size: 13px; color: #71717a;">Key Name</span><br>
                                                                <span style="font-size: 14px; color: {color['primary']}; font-weight: 600;">{key_name}</span>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 8px 0; border-bottom: 1px solid #2a2a3e;">
                                                                <span style="font-size: 13px; color: #71717a;">Type</span><br>
                                                                <span style="display: inline-block; margin-top: 4px; background: {type_bg}; border: 1px solid {type_color}; color: {type_color}; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{key_type.upper()}</span>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 8px 0;">
                                                                <span style="font-size: 13px; color: #71717a;">API Key</span><br>
                                                                <code style="font-family: 'Courier New', monospace; font-size: 13px; color: #e4e4e7; background: #0d0d14; padding: 4px 8px; border-radius: 4px;">{api_key_masked}</code>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>

                                    <!-- Provider Details Card -->
                                    <td width="48%" valign="top" style="padding-left: 12px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px; overflow: hidden;">
                                            <tr>
                                                <td style="background: #1f1f33; padding: 16px 20px; border-bottom: 1px solid #2a2a3e;">
                                                    <span style="font-size: 16px; margin-right: 8px;">📦</span>
                                                    <span style="font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Provider Details</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 20px;">
                                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                                        <tr>
                                                            <td style="padding: 8px 0; border-bottom: 1px solid #2a2a3e;">
                                                                <span style="font-size: 13px; color: #71717a;">Provider</span><br>
                                                                <span style="font-size: 14px; color: #e4e4e7; font-weight: 500;">{provider}</span>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 8px 0; border-bottom: 1px solid #2a2a3e;">
                                                                <span style="font-size: 13px; color: #71717a;">Model</span><br>
                                                                <code style="font-family: 'Courier New', monospace; font-size: 13px; color: #e4e4e7; background: #0d0d14; padding: 4px 8px; border-radius: 4px;">{model}</code>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding: 8px 0;">
                                                                <span style="font-size: 13px; color: #71717a;">Failure Count</span><br>
                                                                <span style="display: inline-block; margin-top: 4px; background: linear-gradient(135deg, #ff4757 0%, #ff3344 100%); color: #ffffff; padding: 6px 14px; border-radius: 8px; font-size: 14px; font-weight: 700;">{failure_count}</span>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Error Details -->
                    <tr>
                        <td style="padding: 0 32px 32px 32px;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 12px; overflow: hidden;">
                                <tr>
                                    <td style="background: #1f1f33; padding: 16px 20px; border-bottom: 1px solid #2a2a3e;">
                                        <span style="font-size: 16px; margin-right: 8px;">📋</span>
                                        <span style="font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Error Details</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 0;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #0d1117; margin: 16px; width: calc(100% - 32px); border-radius: 8px; overflow: hidden;">
                                            <tr>
                                                <td style="background: #161b22; padding: 12px 16px; border-bottom: 1px solid #21262d;">
                                                    <span style="display: inline-block; width: 12px; height: 12px; background: #ff5f56; border-radius: 50%; margin-right: 6px;"></span>
                                                    <span style="display: inline-block; width: 12px; height: 12px; background: #ffbd2e; border-radius: 50%; margin-right: 6px;"></span>
                                                    <span style="display: inline-block; width: 12px; height: 12px; background: #27ca40; border-radius: 50%; margin-right: 6px;"></span>
                                                    <span style="font-family: 'Courier New', monospace; font-size: 12px; color: #6e7681; margin-left: 8px;">error.log</span>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 20px;">
                                                    <code style="font-family: 'Courier New', monospace; font-size: 13px; color: #f85149; line-height: 1.7; word-break: break-word; white-space: pre-wrap;">{error_truncated}</code>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Timestamp -->
                    <tr>
                        <td style="padding: 0 32px 24px 32px; text-align: center;">
                            <span style="font-size: 13px; color: #71717a;">
                                🕐 Triggered at <strong style="color: #a1a1aa; font-family: 'Courier New', monospace;">{payload.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</strong>
                            </span>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background: #0d0d14; padding: 32px; text-align: center; border-top: 1px solid #2a2a3e;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                <tr>
                                    <td style="background: linear-gradient(135deg, {color['primary']} 0%, {color['primary']}cc 100%); width: 36px; height: 36px; border-radius: 10px; text-align: center; vertical-align: middle;">
                                        <span style="font-weight: 700; font-size: 14px; color: #ffffff;">LW</span>
                                    </td>
                                    <td style="padding-left: 12px;">
                                        <span style="font-size: 18px; font-weight: 700; color: #ffffff;">LangWatch</span>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 16px 0 0 0; font-size: 13px; color: #71717a;">Automated Alert System</p>
                            <p style="margin: 8px 0 0 0; font-size: 12px; color: #52525b;">Powered by FIKA Private Limited</p>
                        </td>
                    </tr>

                </table>

            </td>
        </tr>
    </table>
</body>
</html>
'''
