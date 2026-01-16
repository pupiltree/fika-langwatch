"""
Tests for APIKey and KeyManager classes.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from langwatch import APIKey, KeyManager


class TestAPIKey:
    """Tests for APIKey dataclass."""

    def test_api_key_creation(self):
        """Test basic APIKey creation with defaults."""
        key = APIKey(
            name="test",
            key="sk-test-123",
            provider="openai",
            model="gpt-4",
        )
        assert key.name == "test"
        assert key.key == "sk-test-123"
        assert key.provider == "openai"
        assert key.model == "gpt-4"
        assert key.is_fallback is False
        assert key.is_healthy is True
        assert key.failure_count == 0
        assert key.last_failure is None
        assert key.last_error is None
        assert key.extra_config == {}

    def test_api_key_with_extra_config(self):
        """Test APIKey with extra configuration."""
        key = APIKey(
            name="custom",
            key="sk-custom",
            provider="openai",
            model="gpt-4",
            extra_config={"temperature": 0.5, "max_tokens": 1000},
        )
        assert key.extra_config["temperature"] == 0.5
        assert key.extra_config["max_tokens"] == 1000

    def test_mark_failed(self, sample_api_key):
        """Test marking an API key as failed."""
        assert sample_api_key.is_healthy is True
        assert sample_api_key.failure_count == 0

        sample_api_key.mark_failed("API quota exceeded")

        assert sample_api_key.is_healthy is False
        assert sample_api_key.failure_count == 1
        assert sample_api_key.last_error == "API quota exceeded"
        assert sample_api_key.last_failure is not None

    def test_mark_failed_increments_count(self, sample_api_key):
        """Test that failure count increments on multiple failures."""
        sample_api_key.mark_failed("Error 1")
        sample_api_key.mark_failed("Error 2")
        sample_api_key.mark_failed("Error 3")

        assert sample_api_key.failure_count == 3
        assert sample_api_key.last_error == "Error 3"

    def test_mark_healthy(self, sample_api_key):
        """Test marking a failed key as healthy."""
        sample_api_key.mark_failed("Some error")
        assert sample_api_key.is_healthy is False
        assert sample_api_key.failure_count == 1

        sample_api_key.mark_healthy()

        assert sample_api_key.is_healthy is True
        assert sample_api_key.failure_count == 0
        assert sample_api_key.last_error is None

    def test_should_skip_healthy_key(self, sample_api_key):
        """Test that healthy keys should not be skipped."""
        assert sample_api_key.should_skip(unhealthy_timeout=300) is False

    def test_should_skip_unhealthy_key_within_timeout(self, sample_api_key):
        """Test that unhealthy keys within timeout should be skipped."""
        sample_api_key.mark_failed("Error")

        # Should be skipped (just failed)
        assert sample_api_key.should_skip(unhealthy_timeout=300) is True

    def test_should_not_skip_after_timeout(self, sample_api_key):
        """Test that unhealthy keys are retried after timeout."""
        sample_api_key.mark_failed("Error")

        # Simulate time passing by setting last_failure in the past
        sample_api_key.last_failure = datetime.now() - timedelta(seconds=400)

        # Should NOT be skipped (timeout expired)
        assert sample_api_key.should_skip(unhealthy_timeout=300) is False

    def test_seconds_until_retry_healthy(self, sample_api_key):
        """Test seconds_until_retry for healthy key."""
        assert sample_api_key.seconds_until_retry(unhealthy_timeout=300) == 0.0

    def test_seconds_until_retry_unhealthy(self, sample_api_key):
        """Test seconds_until_retry for recently failed key."""
        sample_api_key.mark_failed("Error")

        remaining = sample_api_key.seconds_until_retry(unhealthy_timeout=300)
        assert 299 <= remaining <= 300  # Should be close to 300

    def test_seconds_until_retry_expired(self, sample_api_key):
        """Test seconds_until_retry after timeout expired."""
        sample_api_key.mark_failed("Error")
        sample_api_key.last_failure = datetime.now() - timedelta(seconds=400)

        assert sample_api_key.seconds_until_retry(unhealthy_timeout=300) == 0.0

    def test_to_dict(self, sample_api_key):
        """Test serialization to dictionary."""
        sample_api_key.mark_failed("Test error")

        result = sample_api_key.to_dict()

        assert result["name"] == "test-key"
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4"
        assert result["is_fallback"] is False
        assert result["is_healthy"] is False
        assert result["failure_count"] == 1
        assert result["last_error"] == "Test error"
        assert result["last_failure"] is not None

    def test_to_dict_healthy_key(self, sample_api_key):
        """Test serialization of healthy key."""
        result = sample_api_key.to_dict()

        assert result["is_healthy"] is True
        assert result["failure_count"] == 0
        assert result["last_failure"] is None
        assert result["last_error"] is None


class TestKeyManager:
    """Tests for KeyManager class."""

    def test_key_manager_creation(self, sample_key_configs):
        """Test KeyManager initialization."""
        manager = KeyManager(sample_key_configs)

        assert len(manager.keys) == 3
        assert manager.keys[0].name == "gemini-1"
        assert manager.keys[1].name == "gemini-2"
        assert manager.keys[2].name == "fallback"

    def test_primary_and_fallback_separation(self, key_manager):
        """Test that primary and fallback keys are separated."""
        assert len(key_manager._primary_keys) == 2
        assert len(key_manager._fallback_keys) == 1

        # Check primary keys
        primary_names = [k.name for k in key_manager._primary_keys]
        assert "gemini-1" in primary_names
        assert "gemini-2" in primary_names

        # Check fallback
        assert key_manager._fallback_keys[0].name == "fallback"

    def test_get_key_by_name(self, key_manager):
        """Test retrieving key by name."""
        key = key_manager.get_key_by_name("gemini-1")
        assert key is not None
        assert key.name == "gemini-1"
        assert key.provider == "google"

    def test_get_key_by_name_not_found(self, key_manager):
        """Test retrieving non-existent key."""
        key = key_manager.get_key_by_name("nonexistent")
        assert key is None

    def test_get_key_by_index(self, key_manager):
        """Test retrieving key by index."""
        key = key_manager.get_key_by_index(0)
        assert key is not None
        assert key.name == "gemini-1"

        key = key_manager.get_key_by_index(2)
        assert key.name == "fallback"

    def test_get_key_by_index_out_of_range(self, key_manager):
        """Test retrieving key with invalid index."""
        assert key_manager.get_key_by_index(-1) is None
        assert key_manager.get_key_by_index(100) is None

    def test_mark_failed_by_name(self, key_manager):
        """Test marking key as failed by name."""
        key_manager.mark_failed("gemini-1", "API error")

        key = key_manager.get_key_by_name("gemini-1")
        assert key.is_healthy is False
        assert key.last_error == "API error"

    def test_mark_failed_by_index(self, key_manager):
        """Test marking key as failed by index."""
        key_manager.mark_failed_by_index(0, "API error")

        key = key_manager.get_key_by_index(0)
        assert key.is_healthy is False

    def test_mark_healthy_by_name(self, key_manager):
        """Test marking key as healthy by name."""
        key_manager.mark_failed("gemini-1", "Error")
        key_manager.mark_healthy("gemini-1")

        key = key_manager.get_key_by_name("gemini-1")
        assert key.is_healthy is True

    def test_all_primary_keys_failed(self, key_manager):
        """Test detection when all primary keys have failed."""
        assert key_manager.all_primary_keys_failed() is False

        key_manager.mark_failed("gemini-1", "Error 1")
        assert key_manager.all_primary_keys_failed() is False

        key_manager.mark_failed("gemini-2", "Error 2")
        assert key_manager.all_primary_keys_failed() is True

    def test_all_primary_keys_failed_excludes_fallback(self, key_manager):
        """Test that fallback key failure doesn't affect primary check."""
        key_manager.mark_failed("gemini-1", "Error 1")
        key_manager.mark_failed("gemini-2", "Error 2")
        key_manager.mark_failed("fallback", "Error 3")

        # Still only checks primary keys
        assert key_manager.all_primary_keys_failed() is True

    def test_get_failed_key_names(self, key_manager):
        """Test getting list of failed key names."""
        assert key_manager.get_failed_key_names() == []

        key_manager.mark_failed("gemini-1", "Error")
        assert key_manager.get_failed_key_names() == ["gemini-1"]

        key_manager.mark_failed("fallback", "Error")
        failed = key_manager.get_failed_key_names()
        assert "gemini-1" in failed
        assert "fallback" in failed

    def test_get_healthy_key_names(self, key_manager):
        """Test getting list of healthy key names."""
        healthy = key_manager.get_healthy_key_names()
        assert len(healthy) == 3

        key_manager.mark_failed("gemini-1", "Error")
        healthy = key_manager.get_healthy_key_names()
        assert len(healthy) == 2
        assert "gemini-1" not in healthy

    def test_reset_all(self, key_manager):
        """Test resetting all keys to healthy."""
        key_manager.mark_failed("gemini-1", "Error 1")
        key_manager.mark_failed("gemini-2", "Error 2")
        key_manager.mark_failed("fallback", "Error 3")

        assert len(key_manager.get_healthy_key_names()) == 0

        key_manager.reset_all()

        assert len(key_manager.get_healthy_key_names()) == 3

    def test_get_status_summary(self, key_manager):
        """Test status summary generation."""
        key_manager.mark_failed("gemini-1", "Error")

        summary = key_manager.get_status_summary()

        assert summary["total_keys"] == 3
        assert summary["healthy_keys"] == 2
        assert summary["failed_keys"] == 1
        assert summary["all_primary_failed"] is False
        assert len(summary["keys"]) == 3

    def test_get_status_summary_all_failed(self, key_manager_all_failed):
        """Test status summary when all primary keys failed."""
        summary = key_manager_all_failed.get_status_summary()

        assert summary["all_primary_failed"] is True
        assert summary["failed_keys"] == 2  # Only primary keys failed
        assert summary["healthy_keys"] == 1  # Fallback still healthy

    def test_extra_config_preserved(self):
        """Test that extra_config is preserved through KeyManager."""
        configs = [
            {
                "name": "custom",
                "key": "sk-123",
                "provider": "openai",
                "model": "gpt-4",
                "extra_config": {"temperature": 0.9, "max_tokens": 2000},
            }
        ]
        manager = KeyManager(configs)

        key = manager.get_key_by_name("custom")
        assert key.extra_config["temperature"] == 0.9
        assert key.extra_config["max_tokens"] == 2000
