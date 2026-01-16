"""
Key manager for tracking API key health and status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """Represents an API key with health tracking."""

    name: str
    key: str
    provider: str
    model: str
    is_fallback: bool = False
    is_healthy: bool = True
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    last_error: Optional[str] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)

    def mark_failed(self, error: str) -> None:
        """Mark this key as failed."""
        self.is_healthy = False
        self.failure_count += 1
        self.last_failure = datetime.now()
        self.last_error = error
        logger.warning(f"Key '{self.name}' marked as failed: {error[:100]}")

    def mark_healthy(self) -> None:
        """Mark this key as healthy (recovered)."""
        self.is_healthy = True
        self.failure_count = 0
        self.last_error = None
        logger.info(f"Key '{self.name}' marked as healthy")

    def should_skip(self, unhealthy_timeout: int = 300) -> bool:
        """
        Check if this key should be skipped (unhealthy and not timed out).

        Args:
            unhealthy_timeout: Seconds after which to retry unhealthy keys

        Returns:
            True if key should be skipped, False if it should be tried
        """
        if self.is_healthy:
            return False

        if self.last_failure is None:
            return False

        # Check if timeout has passed
        seconds_since_failure = (datetime.now() - self.last_failure).total_seconds()
        if seconds_since_failure >= unhealthy_timeout:
            logger.info(f"Key '{self.name}' unhealthy timeout expired, will retry")
            return False

        return True

    def seconds_until_retry(self, unhealthy_timeout: int = 300) -> float:
        """Get seconds until this key can be retried."""
        if self.is_healthy or self.last_failure is None:
            return 0.0

        seconds_since_failure = (datetime.now() - self.last_failure).total_seconds()
        remaining = unhealthy_timeout - seconds_since_failure
        return max(0.0, remaining)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "is_fallback": self.is_fallback,
            "is_healthy": self.is_healthy,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "last_error": self.last_error,
        }


class KeyManager:
    """
    Manages multiple API keys with health tracking.

    Usage:
        manager = KeyManager([
            {"name": "gemini-1", "key": "AIza...", "provider": "google", "model": "gemini-2.5-flash"},
            {"name": "gemini-2", "key": "AIza...", "provider": "google", "model": "gemini-2.5-flash"},
            {"name": "openrouter", "key": "sk-...", "provider": "openrouter", "model": "grok-4.1", "is_fallback": True},
        ])
    """

    def __init__(self, keys: List[Dict[str, Any]]):
        """
        Initialize key manager.

        Args:
            keys: List of key configurations with name, key, provider, model, is_fallback
        """
        self.keys: List[APIKey] = []

        for key_config in keys:
            self.keys.append(APIKey(
                name=key_config["name"],
                key=key_config["key"],
                provider=key_config["provider"],
                model=key_config.get("model", ""),
                is_fallback=key_config.get("is_fallback", False),
                extra_config=key_config.get("extra_config", {}),
            ))

        # Separate primary and fallback keys
        self._primary_keys = [k for k in self.keys if not k.is_fallback]
        self._fallback_keys = [k for k in self.keys if k.is_fallback]

        logger.info(f"KeyManager initialized with {len(self._primary_keys)} primary keys and {len(self._fallback_keys)} fallback keys")

    def get_key_by_name(self, name: str) -> Optional[APIKey]:
        """Get a key by its name."""
        for key in self.keys:
            if key.name == name:
                return key
        return None

    def get_key_by_index(self, index: int) -> Optional[APIKey]:
        """Get a key by its index in the list."""
        if 0 <= index < len(self.keys):
            return self.keys[index]
        return None

    def mark_failed(self, key_name: str, error: str) -> None:
        """Mark a key as failed by name."""
        key = self.get_key_by_name(key_name)
        if key:
            key.mark_failed(error)

    def mark_failed_by_index(self, index: int, error: str) -> None:
        """Mark a key as failed by index."""
        key = self.get_key_by_index(index)
        if key:
            key.mark_failed(error)

    def mark_healthy(self, key_name: str) -> None:
        """Mark a key as healthy by name."""
        key = self.get_key_by_name(key_name)
        if key:
            key.mark_healthy()

    def all_primary_keys_failed(self) -> bool:
        """Check if all primary (non-fallback) keys have failed."""
        return all(not k.is_healthy for k in self._primary_keys)

    def get_failed_key_names(self) -> List[str]:
        """Get list of failed key names."""
        return [k.name for k in self.keys if not k.is_healthy]

    def get_healthy_key_names(self) -> List[str]:
        """Get list of healthy key names."""
        return [k.name for k in self.keys if k.is_healthy]

    def reset_all(self) -> None:
        """Reset all keys to healthy state."""
        for key in self.keys:
            key.mark_healthy()

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of all key statuses."""
        return {
            "total_keys": len(self.keys),
            "healthy_keys": len([k for k in self.keys if k.is_healthy]),
            "failed_keys": len([k for k in self.keys if not k.is_healthy]),
            "all_primary_failed": self.all_primary_keys_failed(),
            "keys": [k.to_dict() for k in self.keys],
        }
