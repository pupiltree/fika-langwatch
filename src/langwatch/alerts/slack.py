"""
Slack alert channel using webhooks.
"""

import logging
from typing import Optional, Dict, Any, List

from .base import AlertChannel, AlertPayload

logger = logging.getLogger(__name__)


class SlackAlert(AlertChannel):
    """
    Slack alert channel using incoming webhooks.

    Usage:
        alert = SlackAlert(
            webhook_url="https://hooks.slack.com/services/T.../B.../xxx",
        )
    """

    def __init__(
        self,
        webhook_url: str,
        channel: Optional[str] = None,
        username: Optional[str] = "LangWatch Alerts",
        icon_emoji: Optional[str] = ":warning:",
    ):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji

    @property
    def name(self) -> str:
        return "slack"

    async def send_async(self, payload: AlertPayload) -> bool:
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed. Install with: pip install langwatch[slack]")
            return False

        try:
            slack_payload = self._build_slack_message(payload)

            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=slack_payload, timeout=10.0)

                if response.status_code == 200:
                    logger.info("Slack alert sent successfully")
                    return True
                else:
                    logger.error(f"Slack API error: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def _build_slack_message(self, payload: AlertPayload) -> Dict[str, Any]:
        severity_colors = {"info": "#4A90E2", "warning": "#FFC107", "error": "#E74C3C", "critical": "#DC3545"}
        color = severity_colors.get(payload.severity.lower(), "#FFC107")

        severity_emoji = {"info": ":information_source:", "warning": ":warning:", "error": ":x:", "critical": ":rotating_light:"}
        emoji = severity_emoji.get(payload.severity.lower(), ":bell:")

        # Extract details from payload
        details = payload.details or {}
        key_name = details.get("key_name") or payload.failed_key_name or "Unknown"
        key_type = details.get("key_type", "primary")
        provider = details.get("provider") or payload.failed_provider or "N/A"
        model = details.get("model") or "N/A"
        api_key_masked = details.get("api_key_masked") or "***"
        failure_count = details.get("failure_count", 0)
        error_truncated = details.get("error_truncated") or payload.error_message or "No details"

        blocks: List[Dict[str, Any]] = [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {payload.title}", "emoji": True}},
            {"type": "divider"},
        ]

        # Key Information fields (2 columns)
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:key: Key Name*\n`{key_name}`"},
                {"type": "mrkdwn", "text": f"*:label: Type*\n`{key_type.upper()}`"},
            ]
        })

        # Provider & Model fields (2 columns)
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:package: Provider*\n`{provider}`"},
                {"type": "mrkdwn", "text": f"*:robot_face: Model*\n`{model}`"},
            ]
        })

        # API Key & Failure Count fields (2 columns)
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:closed_lock_with_key: API Key*\n`{api_key_masked}`"},
                {"type": "mrkdwn", "text": f"*:chart_with_upwards_trend: Failure Count*\n`{failure_count}`"},
            ]
        })

        blocks.append({"type": "divider"})

        # Error section
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*:rotating_light: Error*\n```{error_truncated[:400]}```"}
        })

        # Timestamp footer
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f":clock1: {payload.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"}]
        })

        message: Dict[str, Any] = {"blocks": blocks, "attachments": [{"color": color, "fallback": payload.title}]}

        if self.channel:
            message["channel"] = self.channel
        if self.username:
            message["username"] = self.username
        if self.icon_emoji:
            message["icon_emoji"] = self.icon_emoji

        return message
