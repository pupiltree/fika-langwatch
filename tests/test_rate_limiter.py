"""
Tests for InMemoryRateLimiter class.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from langwatch import InMemoryRateLimiter


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter class."""

    def test_creation_with_default_cooldown(self):
        """Test rate limiter creation with custom default cooldown."""
        limiter = InMemoryRateLimiter(default_cooldown=3600)
        assert limiter.default_cooldown == 3600

    def test_can_send_new_key(self, rate_limiter):
        """Test that new keys can always send."""
        assert rate_limiter.can_send("new_key") is True

    def test_can_send_after_mark_sent(self, rate_limiter):
        """Test that key cannot send immediately after being marked."""
        rate_limiter.mark_sent("test_key")

        # Should be blocked (in cooldown)
        assert rate_limiter.can_send("test_key") is False

    def test_can_send_after_cooldown_expires(self, rate_limiter_short):
        """Test that key can send after cooldown expires."""
        rate_limiter_short.mark_sent("test_key")

        # Should be blocked initially
        assert rate_limiter_short.can_send("test_key") is False

        # Wait for cooldown to expire
        time.sleep(1.1)

        # Should be allowed now
        assert rate_limiter_short.can_send("test_key") is True

    def test_custom_cooldown_per_key(self, rate_limiter):
        """Test custom cooldown for specific key."""
        # Mark with custom cooldown of 1 second
        rate_limiter.mark_sent("custom_key", cooldown=1)

        assert rate_limiter.can_send("custom_key") is False

        time.sleep(1.1)

        assert rate_limiter.can_send("custom_key") is True

    def test_can_send_with_custom_cooldown_check(self):
        """Test checking with custom cooldown parameter."""
        rate_limiter = InMemoryRateLimiter(default_cooldown=60)
        rate_limiter.mark_sent("test_key")

        # Default cooldown is 60, so should be blocked
        assert rate_limiter.can_send("test_key") is False

        # With very short cooldown (1 second), wait and check
        time.sleep(1.1)
        assert rate_limiter.can_send("test_key", cooldown=1) is True

    def test_multiple_keys_independent(self, rate_limiter):
        """Test that different keys have independent cooldowns."""
        rate_limiter.mark_sent("key_a")

        # key_a should be blocked
        assert rate_limiter.can_send("key_a") is False

        # key_b should be allowed
        assert rate_limiter.can_send("key_b") is True

    def test_get_remaining_cooldown_new_key(self, rate_limiter):
        """Test remaining cooldown for key that hasn't been sent."""
        assert rate_limiter.get_remaining_cooldown("new_key") == 0.0

    def test_get_remaining_cooldown_after_send(self, rate_limiter):
        """Test remaining cooldown after marking sent."""
        rate_limiter.mark_sent("test_key")

        remaining = rate_limiter.get_remaining_cooldown("test_key")
        assert 59 <= remaining <= 60  # Should be close to 60

    def test_get_remaining_cooldown_after_expire(self, rate_limiter_short):
        """Test remaining cooldown after expiration."""
        rate_limiter_short.mark_sent("test_key")

        time.sleep(1.1)

        assert rate_limiter_short.get_remaining_cooldown("test_key") == 0.0

    def test_reset_specific_key(self, rate_limiter):
        """Test resetting a specific key."""
        rate_limiter.mark_sent("key_a")
        rate_limiter.mark_sent("key_b")

        rate_limiter.reset("key_a")

        assert rate_limiter.can_send("key_a") is True
        assert rate_limiter.can_send("key_b") is False

    def test_reset_all_keys(self, rate_limiter):
        """Test resetting all keys."""
        rate_limiter.mark_sent("key_a")
        rate_limiter.mark_sent("key_b")
        rate_limiter.mark_sent("key_c")

        rate_limiter.reset()  # Reset all

        assert rate_limiter.can_send("key_a") is True
        assert rate_limiter.can_send("key_b") is True
        assert rate_limiter.can_send("key_c") is True

    def test_reset_nonexistent_key(self, rate_limiter):
        """Test resetting a key that doesn't exist (should not raise)."""
        rate_limiter.reset("nonexistent")  # Should not raise

    def test_cleanup_expired(self, rate_limiter_short):
        """Test cleanup of expired entries."""
        rate_limiter_short.mark_sent("key_a")
        rate_limiter_short.mark_sent("key_b")

        # Both should be in cache
        assert rate_limiter_short.can_send("key_a") is False
        assert rate_limiter_short.can_send("key_b") is False

        # Wait for expiration
        time.sleep(1.1)

        # Cleanup
        removed = rate_limiter_short.cleanup_expired()

        assert removed == 2

    def test_cleanup_expired_partial(self):
        """Test cleanup when some entries are still valid."""
        limiter = InMemoryRateLimiter(default_cooldown=10)

        limiter.mark_sent("short_key", cooldown=1)
        limiter.mark_sent("long_key", cooldown=10)

        time.sleep(1.1)

        removed = limiter.cleanup_expired()

        assert removed == 1
        # short_key should be cleaned up, long_key should remain
        assert limiter.can_send("short_key") is True
        assert limiter.can_send("long_key") is False

    def test_thread_safety(self, rate_limiter):
        """Test that rate limiter is thread-safe."""
        results = []

        def mark_and_check(key):
            rate_limiter.mark_sent(key)
            can_send = rate_limiter.can_send(key)
            results.append((key, can_send))

        threads = []
        for i in range(10):
            t = threading.Thread(target=mark_and_check, args=(f"key_{i}",))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All should have been marked and should not be able to send
        assert len(results) == 10
        for key, can_send in results:
            assert can_send is False

    def test_concurrent_access(self):
        """Test concurrent access from multiple threads."""
        limiter = InMemoryRateLimiter(default_cooldown=60)
        send_count = 0
        lock = threading.Lock()

        def try_send():
            nonlocal send_count
            if limiter.can_send("shared_key"):
                limiter.mark_sent("shared_key")
                with lock:
                    send_count += 1

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(try_send) for _ in range(100)]
            for f in futures:
                f.result()

        # Only one thread should have successfully sent
        assert send_count == 1

    def test_custom_cooldown_persists(self, rate_limiter):
        """Test that custom cooldown is remembered for subsequent checks."""
        # First mark with custom cooldown
        rate_limiter.mark_sent("persistent", cooldown=5)

        # Check uses stored cooldown
        remaining = rate_limiter.get_remaining_cooldown("persistent")
        assert 4 <= remaining <= 5

    def test_mark_sent_updates_time(self, rate_limiter_short):
        """Test that marking sent again updates the timestamp."""
        rate_limiter_short.mark_sent("test_key")

        time.sleep(0.5)

        # Mark again
        rate_limiter_short.mark_sent("test_key")

        # Remaining should be close to full cooldown again
        remaining = rate_limiter_short.get_remaining_cooldown("test_key")
        assert remaining > 0.4

    def test_empty_cleanup(self, rate_limiter):
        """Test cleanup on empty cache."""
        removed = rate_limiter.cleanup_expired()
        assert removed == 0
