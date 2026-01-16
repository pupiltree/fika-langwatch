"""
HTML email templates for alert notifications.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..alerts.base import AlertPayload


class EmailTemplates:
    """HTML email templates with futuristic CSS styling."""

    @staticmethod
    def build_alert_email(payload: "AlertPayload") -> str:
        """Build complete HTML email from alert payload."""

        # Futuristic color schemes based on severity
        colors = {
            "info": {
                "primary": "#00d4ff",
                "secondary": "#0099cc",
                "glow": "rgba(0, 212, 255, 0.4)",
                "bg": "rgba(0, 212, 255, 0.1)",
            },
            "warning": {
                "primary": "#ffaa00",
                "secondary": "#ff8800",
                "glow": "rgba(255, 170, 0, 0.4)",
                "bg": "rgba(255, 170, 0, 0.1)",
            },
            "error": {
                "primary": "#ff4757",
                "secondary": "#ff3344",
                "glow": "rgba(255, 71, 87, 0.4)",
                "bg": "rgba(255, 71, 87, 0.1)",
            },
            "critical": {
                "primary": "#ff0055",
                "secondary": "#cc0044",
                "glow": "rgba(255, 0, 85, 0.5)",
                "bg": "rgba(255, 0, 85, 0.15)",
            },
        }

        color = colors.get(payload.severity.lower(), colors["warning"])

        # Get details from payload
        details = payload.details or {}
        app_name = details.get("app_name", "")
        key_name = details.get("key_name", payload.failed_key_name or "Unknown")
        key_type = details.get("key_type", "primary")
        provider = details.get("provider", payload.failed_provider or "Unknown")
        model = details.get("model", "Unknown")
        api_key_masked = details.get("api_key_masked", "***")
        failure_count = details.get("failure_count", 0)
        error_truncated = details.get("error_truncated", payload.error_message or "No details available")

        # App name badge
        app_badge = ""
        if app_name:
            app_badge = f'<span class="app-badge">{app_name}</span>'

        content = f"""
        <div class="header">
            <div class="header-glow"></div>
            <div class="header-content">
                {app_badge}
                <h1>{payload.title}</h1>
                <div class="severity-indicator">
                    <span class="pulse"></span>
                    <span class="severity-text">{payload.severity.upper()}</span>
                </div>
            </div>
        </div>

        <div class="content">
            <div class="alert-box">
                <div class="alert-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color['primary']}" stroke-width="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <div class="alert-content">
                    <h2>Alert Triggered</h2>
                    <p>{payload.message}</p>
                </div>
            </div>

            <div class="grid-container">
                <div class="info-card">
                    <div class="card-header">
                        <span class="card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                        </span>
                        <span class="card-title">Key Information</span>
                    </div>
                    <div class="card-body">
                        <div class="data-row">
                            <span class="data-label">Key Name</span>
                            <span class="data-value highlight">{key_name}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Type</span>
                            <span class="data-value">
                                <span class="type-badge {'type-fallback' if key_type == 'fallback' else 'type-primary'}">{key_type.upper()}</span>
                            </span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">API Key</span>
                            <span class="data-value mono">{api_key_masked}</span>
                        </div>
                    </div>
                </div>

                <div class="info-card">
                    <div class="card-header">
                        <span class="card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                            </svg>
                        </span>
                        <span class="card-title">Provider Details</span>
                    </div>
                    <div class="card-body">
                        <div class="data-row">
                            <span class="data-label">Provider</span>
                            <span class="data-value">{provider}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Model</span>
                            <span class="data-value mono">{model}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">Failures</span>
                            <span class="data-value">
                                <span class="failure-count">{failure_count}</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="info-card error-card">
                <div class="card-header">
                    <span class="card-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                        </svg>
                    </span>
                    <span class="card-title">Error Details</span>
                </div>
                <div class="card-body">
                    <div class="error-terminal">
                        <div class="terminal-header">
                            <span class="terminal-dot red"></span>
                            <span class="terminal-dot yellow"></span>
                            <span class="terminal-dot green"></span>
                            <span class="terminal-title">error.log</span>
                        </div>
                        <div class="terminal-body">
                            <code>{error_truncated}</code>
                        </div>
                    </div>
                </div>
            </div>

            <div class="timestamp-section">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span>Triggered at <strong>{payload.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</strong></span>
            </div>
        </div>

        <div class="footer">
            <div class="footer-logo">
                <span class="logo-icon">LW</span>
                <span class="logo-text">LangWatch</span>
            </div>
            <p class="footer-text">Automated Alert System</p>
            <div class="footer-links">
                <span>Powered by FIKA Private Limited</span>
            </div>
        </div>
        """

        return EmailTemplates._base_template(content, payload.title, color)

    @staticmethod
    def _base_template(content: str, title: str, color: dict) -> str:
        """Base HTML template with futuristic CSS styling."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
            margin: 0;
            padding: 40px 20px;
            color: #e4e4e7;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .email-container {{
            max-width: 680px;
            margin: 0 auto;
            background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 25, 0.98) 100%);
            border-radius: 20px;
            box-shadow:
                0 0 0 1px rgba(255, 255, 255, 0.05),
                0 25px 50px -12px rgba(0, 0, 0, 0.5),
                0 0 100px {color['glow']};
            overflow: hidden;
            backdrop-filter: blur(20px);
        }}

        .header {{
            position: relative;
            background: linear-gradient(135deg, {color['primary']}15 0%, transparent 50%);
            padding: 40px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
        }}

        .header-glow {{
            position: absolute;
            top: -50%;
            left: 50%;
            transform: translateX(-50%);
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at center, {color['glow']} 0%, transparent 70%);
            opacity: 0.3;
            pointer-events: none;
        }}

        .header-content {{
            position: relative;
            z-index: 1;
        }}

        .app-badge {{
            display: inline-block;
            background: linear-gradient(135deg, {color['primary']}30 0%, {color['secondary']}20 100%);
            border: 1px solid {color['primary']}50;
            color: {color['primary']};
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }}

        .header h1 {{
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
            margin: 0 0 16px 0;
            text-shadow: 0 0 30px {color['glow']};
        }}

        .severity-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: {color['bg']};
            border: 1px solid {color['primary']}40;
            padding: 8px 20px;
            border-radius: 30px;
        }}

        .pulse {{
            width: 10px;
            height: 10px;
            background: {color['primary']};
            border-radius: 50%;
            box-shadow: 0 0 10px {color['primary']}, 0 0 20px {color['glow']};
        }}

        .severity-text {{
            color: {color['primary']};
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 2px;
        }}

        .content {{
            padding: 32px;
        }}

        .alert-box {{
            display: flex;
            gap: 16px;
            background: linear-gradient(135deg, {color['bg']} 0%, transparent 100%);
            border: 1px solid {color['primary']}30;
            border-left: 4px solid {color['primary']};
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}

        .alert-icon {{
            flex-shrink: 0;
            width: 48px;
            height: 48px;
            background: {color['primary']}20;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .alert-content h2 {{
            color: #ffffff;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .alert-content p {{
            color: #a1a1aa;
            font-size: 14px;
            line-height: 1.6;
        }}

        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}

        @media (max-width: 600px) {{
            .grid-container {{
                grid-template-columns: 1fr;
            }}
        }}

        .info-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .info-card:hover {{
            border-color: rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.03);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 16px 20px;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .card-icon {{
            color: {color['primary']};
            display: flex;
            align-items: center;
        }}

        .card-title {{
            font-size: 13px;
            font-weight: 600;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .card-body {{
            padding: 16px 20px;
        }}

        .data-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .data-row:last-child {{
            border-bottom: none;
        }}

        .data-label {{
            font-size: 13px;
            color: #71717a;
            font-weight: 500;
        }}

        .data-value {{
            font-size: 14px;
            color: #e4e4e7;
            font-weight: 500;
        }}

        .data-value.highlight {{
            color: {color['primary']};
        }}

        .data-value.mono {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            background: rgba(0, 0, 0, 0.3);
            padding: 4px 8px;
            border-radius: 6px;
        }}

        .type-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .type-primary {{
            background: rgba(0, 212, 255, 0.15);
            color: #00d4ff;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }}

        .type-fallback {{
            background: rgba(255, 170, 0, 0.15);
            color: #ffaa00;
            border: 1px solid rgba(255, 170, 0, 0.3);
        }}

        .failure-count {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #ff4757 0%, #ff3344 100%);
            color: #ffffff;
            font-weight: 700;
            font-size: 13px;
            border-radius: 8px;
            box-shadow: 0 0 15px rgba(255, 71, 87, 0.4);
        }}

        .error-card {{
            grid-column: 1 / -1;
        }}

        .error-terminal {{
            background: #0d1117;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .terminal-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .terminal-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        .terminal-dot.red {{ background: #ff5f56; }}
        .terminal-dot.yellow {{ background: #ffbd2e; }}
        .terminal-dot.green {{ background: #27ca40; }}

        .terminal-title {{
            margin-left: auto;
            font-size: 12px;
            color: #6e7681;
            font-family: 'JetBrains Mono', monospace;
        }}

        .terminal-body {{
            padding: 20px;
            max-height: 200px;
            overflow-y: auto;
        }}

        .terminal-body code {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #f85149;
            line-height: 1.7;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .timestamp-section {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 20px;
            margin-top: 8px;
            color: #71717a;
            font-size: 13px;
        }}

        .timestamp-section strong {{
            color: #a1a1aa;
            font-family: 'JetBrains Mono', monospace;
        }}

        .footer {{
            background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
            padding: 32px;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .footer-logo {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .logo-icon {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, {color['primary']} 0%, {color['secondary']} 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: #ffffff;
        }}

        .logo-text {{
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }}

        .footer-text {{
            color: #71717a;
            font-size: 13px;
            margin-bottom: 16px;
        }}

        .footer-links {{
            font-size: 12px;
            color: #52525b;
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
