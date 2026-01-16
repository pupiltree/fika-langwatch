"""
Generic webhook alert channel.
"""

import logging
from typing import Optional, Dict, Any

from .base import AlertChannel, AlertPayload

logger = logging.getLogger(__name__)


class WebhookAlert(AlertChannel):
    """
    Generic HTTP webhook alert channel.

    Usage:
        alert = WebhookAlert(
            url="https://your-api.com/alerts",
            headers={"Authorization": "Bearer token"},
        )
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        timeout: float = 10.0,
    ):
        self.url = url
        self.headers = headers or {}
        self.method = method.upper()
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "webhook"

    async def send_async(self, payload: AlertPayload) -> bool:
        try:
            import httpx
        except ImportError:
            logger.error("httpx not installed. Install with: pip install langwatch[webhook]")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=self.method,
                    url=self.url,
                    json=payload.to_dict(),
                    headers=self.headers,
                    timeout=self.timeout,
                )

                if response.status_code < 400:
                    logger.info(f"Webhook alert sent: {response.status_code}")
                    return True
                else:
                    logger.error(f"Webhook error: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
