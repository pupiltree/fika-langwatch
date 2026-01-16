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

        blocks: List[Dict[str, Any]] = [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {payload.title}", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": payload.message}},
            {"type": "divider"},
        ]

        fields = []
        if payload.failed_key_name:
            fields.append({"type": "mrkdwn", "text": f"*Failed Key:*\n{payload.failed_key_name}"})
        if payload.failed_provider:
            fields.append({"type": "mrkdwn", "text": f"*Provider:*\n{payload.failed_provider}"})
        if payload.fallback_key_name:
            fields.append({"type": "mrkdwn", "text": f"*Fallback:*\n{payload.fallback_key_name}"})

        if fields:
            blocks.append({"type": "section", "fields": fields[:10]})

        if payload.error_message:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Error:*\n```{payload.error_message[:500]}```"}})

        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"Timestamp: {payload.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"}]})

        message: Dict[str, Any] = {"blocks": blocks, "attachments": [{"color": color, "fallback": payload.title}]}

        if self.channel:
            message["channel"] = self.channel
        if self.username:
            message["username"] = self.username
        if self.icon_emoji:
            message["icon_emoji"] = self.icon_emoji

        return message
