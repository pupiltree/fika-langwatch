"""
In-memory rate limiter for alert cooldowns.
Prevents alert spam by tracking when alerts were last sent.
"""

import time
import threading
from typing import Dict, Optional


class InMemoryRateLimiter:
    """
    Thread-safe in-memory rate limiter for alert cooldowns.

    Usage:
        limiter = InMemoryRateLimiter(default_cooldown=3600)  # 1 hour default

        if limiter.can_send("gemini_api_failure"):
            send_alert(...)
            limiter.mark_sent("gemini_api_failure")
    """

    def __init__(self, default_cooldown: int = 3600):
        """
        Initialize the rate limiter.

        Args:
            default_cooldown: Default cooldown period in seconds (default: 3600 = 1 hour)
        """
        self._cache: Dict[str, float] = {}
        self._cooldowns: Dict[str, int] = {}
        self.default_cooldown = default_cooldown
        self._lock = threading.Lock()

    def can_send(self, key: str, cooldown: Optional[int] = None) -> bool:
        """
        Check if an alert can be sent (not in cooldown period).

        Args:
            key: Unique identifier for the alert type (e.g., "gemini_api_failure")
            cooldown: Optional custom cooldown in seconds (uses default if not specified)

        Returns:
            True if alert can be sent, False if in cooldown period
        """
        with self._lock:
            current_time = time.time()

            if key not in self._cache:
                return True

            last_sent = self._cache[key]
            effective_cooldown = cooldown or self._cooldowns.get(key, self.default_cooldown)

            return (current_time - last_sent) >= effective_cooldown

    def mark_sent(self, key: str, cooldown: Optional[int] = None) -> None:
        """
        Mark that an alert was sent, starting the cooldown period.

        Args:
            key: Unique identifier for the alert type
            cooldown: Optional custom cooldown in seconds for this key
        """
        with self._lock:
            self._cache[key] = time.time()
            if cooldown is not None:
                self._cooldowns[key] = cooldown

    def get_remaining_cooldown(self, key: str) -> float:
        """
        Get remaining cooldown time for an alert type.

        Args:
            key: Unique identifier for the alert type

        Returns:
            Remaining cooldown in seconds (0 if not in cooldown)
        """
        with self._lock:
            if key not in self._cache:
                return 0.0

            current_time = time.time()
            last_sent = self._cache[key]
            effective_cooldown = self._cooldowns.get(key, self.default_cooldown)
            remaining = effective_cooldown - (current_time - last_sent)

            return max(0.0, remaining)

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset cooldown for a specific key or all keys.

        Args:
            key: Specific key to reset, or None to reset all
        """
        with self._lock:
            if key is None:
                self._cache.clear()
                self._cooldowns.clear()
            elif key in self._cache:
                del self._cache[key]
                self._cooldowns.pop(key, None)

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache to free memory.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, last_sent in self._cache.items():
                effective_cooldown = self._cooldowns.get(key, self.default_cooldown)
                if (current_time - last_sent) >= effective_cooldown:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._cooldowns.pop(key, None)

            return len(expired_keys)
