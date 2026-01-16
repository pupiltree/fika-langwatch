"""
Base alert channel abstract class.
All alert channels (Email, Slack, Webhook) inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AlertPayload:
    """Standard alert payload passed to all channels."""

    title: str
    message: str
    severity: str  # "info", "warning", "error", "critical"
    alert_type: str  # e.g., "api_key_failure", "fallback_activated"
    timestamp: datetime
    details: Dict[str, Any]

    # API key specific fields
    failed_key_name: Optional[str] = None
    failed_provider: Optional[str] = None
    fallback_key_name: Optional[str] = None
    fallback_provider: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "alert_type": self.alert_type,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "failed_key_name": self.failed_key_name,
            "failed_provider": self.failed_provider,
            "fallback_key_name": self.fallback_key_name,
            "fallback_provider": self.fallback_provider,
            "error_message": self.error_message,
        }


class AlertChannel(ABC):
    """
    Abstract base class for alert channels.

    Implement this to create custom alert channels (Email, Slack, Webhook, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the channel name for logging."""
        pass

    @abstractmethod
    async def send_async(self, payload: AlertPayload) -> bool:
        """
        Send an alert asynchronously.

        Args:
            payload: The alert payload containing all alert details

        Returns:
            True if alert was sent successfully, False otherwise
        """
        pass

    def send(self, payload: AlertPayload) -> bool:
        """
        Send an alert synchronously.

        Default implementation runs async version in event loop.
        Override for truly synchronous implementations.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.send_async(payload))
                    return future.result()
            else:
                return loop.run_until_complete(self.send_async(payload))
        except RuntimeError:
            return asyncio.run(self.send_async(payload))
