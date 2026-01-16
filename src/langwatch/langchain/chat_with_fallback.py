"""
ChatWithFallback - LangChain chat model wrapper with automatic fallback and alerts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Callable, Union, TYPE_CHECKING

from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from pydantic import ConfigDict

from ..alerts.base import AlertChannel, AlertPayload
from ..key_manager import KeyManager, APIKey
from ..rate_limiter import InMemoryRateLimiter
from ..providers import ProviderFactory

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class ChatWithFallback(BaseChatModel):
    """
    LangChain-compatible chat model with automatic fallback and alert notifications.

    When a model fails, it automatically tries the next model in the chain.
    When all primary keys fail and fallback is activated, alerts are sent.

    Usage (Option A - bind_tools after creation):
        chat = ChatWithFallback.from_config(
            models=[
                {"name": "gemini-1", "provider": "google", "model": "gemini-2.5-flash", "api_key": "..."},
                {"name": "gemini-2", "provider": "google", "model": "gemini-2.5-flash", "api_key": "..."},
                {"name": "fallback", "provider": "openrouter", "model": "grok-4.1", "api_key": "...", "is_fallback": True},
            ],
            alerts=[EmailAlert(...), SlackAlert(...)],
        )

        # Bind tools - applies to ALL underlying models
        chat_with_tools = chat.bind_tools([tool1, tool2])
        response = await chat_with_tools.ainvoke(messages)

    Usage (Manual models):
        chat = ChatWithFallback(
            models=[model1, model2, fallback_model],
            model_names=["gemini-1", "gemini-2", "fallback"],
            alerts=[EmailAlert(...)],
        )
    """

    # Pydantic fields
    models: List[BaseChatModel] = []
    key_manager: Optional[KeyManager] = None
    alerts: List[AlertChannel] = []
    alert_rate_limiter: Optional[InMemoryRateLimiter] = None
    cooldown_seconds: int = 300
    model_names: List[str] = []
    app_name: Optional[str] = None
    on_key_failure: Optional[Callable] = None
    on_fallback_activated: Optional[Callable] = None
    skip_unhealthy: bool = True
    unhealthy_timeout: int = 300

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        models: List[BaseChatModel],
        model_names: Optional[List[str]] = None,
        alerts: Optional[List[AlertChannel]] = None,
        key_manager: Optional[KeyManager] = None,
        alert_rate_limiter: Optional[InMemoryRateLimiter] = None,
        cooldown_seconds: int = 300,
        app_name: Optional[str] = None,
        on_key_failure: Optional[Callable] = None,
        on_fallback_activated: Optional[Callable] = None,
        skip_unhealthy: bool = True,
        unhealthy_timeout: int = 300,
        **kwargs,
    ):
        """
        Initialize ChatWithFallback.

        Args:
            models: List of LangChain chat models (primary + fallbacks)
            model_names: Names for each model (for alerts). Auto-generated if not provided.
            alerts: List of alert channels (Email, Slack, Webhook)
            key_manager: Optional KeyManager for detailed health tracking
            alert_rate_limiter: Optional rate limiter for alerts (created automatically if not provided)
            cooldown_seconds: Per-key cooldown between alerts (default: 300 = 5 minutes)
            app_name: App/client name for alert subject lines (e.g., "[ClientA] API Key Failure")
            on_key_failure: Optional callback when a key fails: fn(key_name, error)
            on_fallback_activated: Optional callback when fallback activates: fn(fallback_key_name)
            skip_unhealthy: Skip unhealthy keys until timeout (default: True)
            unhealthy_timeout: Seconds before retrying unhealthy keys (default: 300 = 5 minutes)
        """
        super().__init__(**kwargs)

        self.models = models
        self.model_names = model_names or [f"model-{i}" for i in range(len(models))]
        self.alerts = alerts or []
        self.alert_rate_limiter = alert_rate_limiter or InMemoryRateLimiter(default_cooldown=cooldown_seconds)
        self.cooldown_seconds = cooldown_seconds
        self.app_name = app_name
        self.on_key_failure = on_key_failure
        self.on_fallback_activated = on_fallback_activated
        self.skip_unhealthy = skip_unhealthy
        self.unhealthy_timeout = unhealthy_timeout

        if len(self.model_names) != len(self.models):
            raise ValueError(f"model_names length ({len(self.model_names)}) must match models length ({len(self.models)})")

        # Auto-create KeyManager if not provided
        if key_manager:
            self.key_manager = key_manager
        else:
            self.key_manager = self._create_key_manager_from_models()

        logger.info(f"ChatWithFallback initialized with {len(models)} models: {self.model_names} (app_name={app_name})")

    def _create_key_manager_from_models(self) -> KeyManager:
        """Auto-create KeyManager by extracting info from LangChain model objects."""
        keys_config = []

        for i, model_obj in enumerate(self.models):
            name = self.model_names[i]

            # Extract model name
            model_id = getattr(model_obj, 'model', None) or getattr(model_obj, 'model_name', None) or "unknown"

            # Infer provider from class name
            class_name = model_obj.__class__.__name__.lower()
            if 'openai' in class_name:
                provider = 'openai'
            elif 'google' in class_name or 'genai' in class_name or 'gemini' in class_name:
                provider = 'google'
            elif 'anthropic' in class_name or 'claude' in class_name:
                provider = 'anthropic'
            else:
                provider = class_name.replace('chat', '').strip() or 'unknown'

            # Try to extract API key
            api_key = (
                getattr(model_obj, 'openai_api_key', None) or
                getattr(model_obj, 'google_api_key', None) or
                getattr(model_obj, 'anthropic_api_key', None) or
                getattr(model_obj, 'api_key', None)
            )
            if api_key and hasattr(api_key, 'get_secret_value'):
                api_key = api_key.get_secret_value()
            api_key_str = str(api_key) if api_key else ""

            # Last model is fallback by default
            is_fallback = (i == len(self.models) - 1)

            keys_config.append({
                "name": name,
                "key": api_key_str,
                "provider": provider,
                "model": model_id,
                "is_fallback": is_fallback,
            })

        return KeyManager(keys_config)

    @classmethod
    def from_config(
        cls,
        models: List[Dict[str, Any]],
        alerts: Optional[List[AlertChannel]] = None,
        cooldown_seconds: int = 300,
        app_name: Optional[str] = None,
        on_key_failure: Optional[Callable] = None,
        on_fallback_activated: Optional[Callable] = None,
        skip_unhealthy: bool = True,
        unhealthy_timeout: int = 300,
    ) -> "ChatWithFallback":
        """
        Create ChatWithFallback from configuration dictionaries.

        Args:
            models: List of model configs with keys: name, provider, model, api_key, is_fallback
            alerts: List of alert channels
            cooldown_seconds: Per-key cooldown between alerts (default: 300 = 5 minutes)
            app_name: App/client name for alert subject lines (e.g., "[ClientA] API Key Failure")
            on_key_failure: Callback when key fails
            on_fallback_activated: Callback when fallback activates
            skip_unhealthy: Skip unhealthy keys until timeout (default: True)
            unhealthy_timeout: Seconds before retrying unhealthy keys (default: 300)

        Returns:
            ChatWithFallback instance

        Example:
            chat = ChatWithFallback.from_config(
                models=[
                    {"name": "gemini-1", "provider": "google", "model": "gemini-2.5-flash", "api_key": "AIza..."},
                    {"name": "fallback", "provider": "openrouter", "model": "grok-4.1", "api_key": "sk-...", "is_fallback": True},
                ],
                alerts=[EmailAlert(...), SlackAlert(...)],
                app_name="MyApp",  # Shows in alert: [MyApp] API Key Failure
                cooldown_seconds=300,  # 5 min cooldown per key
            )
        """
        # Create KeyManager
        key_manager = KeyManager([
            {
                "name": m["name"],
                "key": m["api_key"],
                "provider": m["provider"],
                "model": m["model"],
                "is_fallback": m.get("is_fallback", False),
                "extra_config": m.get("extra_config", {}),
            }
            for m in models
        ])

        # Create LangChain models using factory
        langchain_models = []
        for key in key_manager.keys:
            model = ProviderFactory.create_model(key)
            langchain_models.append(model)

        model_names = [m["name"] for m in models]

        return cls(
            models=langchain_models,
            model_names=model_names,
            alerts=alerts,
            key_manager=key_manager,
            cooldown_seconds=cooldown_seconds,
            app_name=app_name,
            on_key_failure=on_key_failure,
            on_fallback_activated=on_fallback_activated,
            skip_unhealthy=skip_unhealthy,
            unhealthy_timeout=unhealthy_timeout,
        )

    def bind_tools(
        self,
        tools: Sequence["BaseTool"],
        **kwargs,
    ) -> "ChatWithFallback":
        """
        Bind tools to ALL underlying models and return a new ChatWithFallback.

        Args:
            tools: Sequence of tools to bind
            **kwargs: Additional arguments passed to each model's bind_tools

        Returns:
            New ChatWithFallback with tools bound to all models
        """
        # Bind tools to each model
        bound_models = []
        for model in self.models:
            if hasattr(model, "bind_tools"):
                bound_model = model.bind_tools(tools, **kwargs)
                bound_models.append(bound_model)
            else:
                logger.warning(f"Model {type(model).__name__} does not support bind_tools")
                bound_models.append(model)

        # Create new instance with bound models
        return ChatWithFallback(
            models=bound_models,
            model_names=self.model_names,
            alerts=self.alerts,
            key_manager=self.key_manager,
            alert_rate_limiter=self.alert_rate_limiter,
            cooldown_seconds=self.cooldown_seconds,
            app_name=self.app_name,
            on_key_failure=self.on_key_failure,
            on_fallback_activated=self.on_fallback_activated,
            skip_unhealthy=self.skip_unhealthy,
            unhealthy_timeout=self.unhealthy_timeout,
        )

    @property
    def _llm_type(self) -> str:
        return "chat_with_fallback"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_names": self.model_names,
            "num_models": len(self.models),
        }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        """Synchronous generation with fallback."""
        last_error = None
        skipped_count = 0

        for i, model in enumerate(self.models):
            model_name = self.model_names[i]
            is_fallback = self.key_manager and self.key_manager.keys[i].is_fallback if self.key_manager else (i == len(self.models) - 1)

            # Skip unhealthy keys if enabled
            if self.skip_unhealthy and self.key_manager:
                key = self.key_manager.keys[i]
                if key.should_skip(self.unhealthy_timeout):
                    remaining = key.seconds_until_retry(self.unhealthy_timeout)
                    logger.debug(f"Skipping unhealthy model: {model_name} (retry in {remaining:.0f}s)")
                    skipped_count += 1
                    continue

            try:
                logger.debug(f"Trying model: {model_name}")
                result = model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

                # Mark as healthy if we have key_manager
                if self.key_manager:
                    self.key_manager.mark_healthy(model_name)

                return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model {model_name} failed: {last_error[:100]}")

                # Track failure
                self._handle_failure(i, model_name, last_error, is_fallback)

        # All models failed or skipped
        raise RuntimeError(f"All {len(self.models)} models failed ({skipped_count} skipped as unhealthy). Last error: {last_error}")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        """Asynchronous generation with fallback."""
        last_error = None
        skipped_count = 0

        for i, model in enumerate(self.models):
            model_name = self.model_names[i]
            is_fallback = self.key_manager and self.key_manager.keys[i].is_fallback if self.key_manager else (i == len(self.models) - 1)

            # Skip unhealthy keys if enabled
            if self.skip_unhealthy and self.key_manager:
                key = self.key_manager.keys[i]
                if key.should_skip(self.unhealthy_timeout):
                    remaining = key.seconds_until_retry(self.unhealthy_timeout)
                    logger.debug(f"Skipping unhealthy model: {model_name} (retry in {remaining:.0f}s)")
                    skipped_count += 1
                    continue

            try:
                logger.debug(f"Trying model: {model_name}")
                result = await model._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)

                # Mark as healthy
                if self.key_manager:
                    self.key_manager.mark_healthy(model_name)

                return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Model {model_name} failed: {last_error[:100]}")

                # Track failure
                await self._handle_failure_async(i, model_name, last_error, is_fallback)

        # All models failed or skipped
        raise RuntimeError(f"All {len(self.models)} models failed ({skipped_count} skipped as unhealthy). Last error: {last_error}")

    def _handle_failure(self, index: int, model_name: str, error: str, is_fallback: bool) -> None:
        """Handle model failure synchronously."""
        # Mark as failed in key manager
        if self.key_manager:
            self.key_manager.mark_failed_by_index(index, error)

        # Callback
        if self.on_key_failure:
            try:
                self.on_key_failure(model_name, error)
            except Exception as e:
                logger.error(f"on_key_failure callback error: {e}")

        # Send per-key failure alert (with per-key cooldown)
        self._send_failure_alert_sync(index, model_name, error, is_fallback)

        # Callback when fallback is activated
        if not is_fallback and self._is_entering_fallback(index):
            if self.on_fallback_activated:
                fallback_name = self.model_names[index + 1] if index + 1 < len(self.model_names) else None
                if fallback_name:
                    try:
                        self.on_fallback_activated(fallback_name)
                    except Exception as e:
                        logger.error(f"on_fallback_activated callback error: {e}")

    async def _handle_failure_async(self, index: int, model_name: str, error: str, is_fallback: bool) -> None:
        """Handle model failure asynchronously."""
        # Mark as failed in key manager
        if self.key_manager:
            self.key_manager.mark_failed_by_index(index, error)

        # Callback
        if self.on_key_failure:
            try:
                self.on_key_failure(model_name, error)
            except Exception as e:
                logger.error(f"on_key_failure callback error: {e}")

        # Send per-key failure alert (with per-key cooldown)
        await self._send_failure_alert_async(index, model_name, error, is_fallback)

        # Callback when fallback is activated
        if not is_fallback and self._is_entering_fallback(index):
            if self.on_fallback_activated:
                fallback_name = self.model_names[index + 1] if index + 1 < len(self.model_names) else None
                if fallback_name:
                    try:
                        self.on_fallback_activated(fallback_name)
                    except Exception as e:
                        logger.error(f"on_fallback_activated callback error: {e}")

    def _is_entering_fallback(self, failed_index: int) -> bool:
        """Check if we're about to enter fallback mode."""
        next_index = failed_index + 1
        if next_index >= len(self.models):
            return False

        if self.key_manager:
            next_key = self.key_manager.keys[next_index]
            return next_key.is_fallback
        else:
            return next_index == len(self.models) - 1

    def _send_failure_alert_sync(self, index: int, model_name: str, error: str, is_fallback: bool) -> None:
        """Send per-key failure alert synchronously."""
        alert_key = f"key_failure:{model_name}"

        # Check rate limit for this specific key
        if not self.alert_rate_limiter.can_send(alert_key, self.cooldown_seconds):
            logger.debug(f"Alert for {model_name} in cooldown, skipping")
            return

        # Build payload with full details
        payload = self._build_failure_payload(index, model_name, error, is_fallback)

        # Send to all channels
        for channel in self.alerts:
            try:
                channel.send(payload)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.name}: {e}")

        # Mark sent
        self.alert_rate_limiter.mark_sent(alert_key, self.cooldown_seconds)

    async def _send_failure_alert_async(self, index: int, model_name: str, error: str, is_fallback: bool) -> None:
        """Send per-key failure alert asynchronously."""
        alert_key = f"key_failure:{model_name}"

        # Check rate limit for this specific key
        if not self.alert_rate_limiter.can_send(alert_key, self.cooldown_seconds):
            logger.debug(f"Alert for {model_name} in cooldown, skipping")
            return

        # Build payload with full details
        payload = self._build_failure_payload(index, model_name, error, is_fallback)

        # Send to all channels concurrently
        tasks = [channel.send_async(payload) for channel in self.alerts]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to send alert via {self.alerts[i].name}: {result}")

        # Mark sent
        self.alert_rate_limiter.mark_sent(alert_key, self.cooldown_seconds)

    def _build_failure_payload(self, index: int, model_name: str, error: str, is_fallback: bool) -> AlertPayload:
        """Build alert payload for key failure with full details."""
        # Get full key details
        provider = None
        model_id = None
        api_key_masked = None
        failure_count = 0

        if self.key_manager and index < len(self.key_manager.keys):
            key = self.key_manager.keys[index]
            provider = key.provider
            model_id = key.model
            failure_count = key.failure_count
            # Mask API key - show first 8 and last 4 chars for better identification
            if key.key and len(key.key) > 16:
                api_key_masked = f"{key.key[:8]}...{key.key[-4:]}"
            elif key.key and len(key.key) > 8:
                api_key_masked = f"{key.key[:4]}...{key.key[-4:]}"
            elif key.key:
                api_key_masked = f"{key.key[:2]}..."
        else:
            # Extract info from LangChain model object when KeyManager not available
            if index < len(self.models):
                model_obj = self.models[index]
                # Extract model name
                model_id = getattr(model_obj, 'model', None) or getattr(model_obj, 'model_name', None)
                # Infer provider from class name
                class_name = model_obj.__class__.__name__.lower()
                if 'openai' in class_name:
                    provider = 'openai'
                elif 'google' in class_name or 'genai' in class_name or 'gemini' in class_name:
                    provider = 'google'
                elif 'anthropic' in class_name or 'claude' in class_name:
                    provider = 'anthropic'
                else:
                    provider = class_name.replace('chat', '').strip()
                # Try to extract and mask API key
                api_key = (
                    getattr(model_obj, 'openai_api_key', None) or
                    getattr(model_obj, 'google_api_key', None) or
                    getattr(model_obj, 'anthropic_api_key', None) or
                    getattr(model_obj, 'api_key', None)
                )
                if api_key:
                    api_key_str = str(api_key.get_secret_value() if hasattr(api_key, 'get_secret_value') else api_key)
                    if len(api_key_str) > 16:
                        api_key_masked = f"{api_key_str[:8]}...{api_key_str[-4:]}"
                    elif len(api_key_str) > 8:
                        api_key_masked = f"{api_key_str[:4]}...{api_key_str[-4:]}"
                    elif api_key_str:
                        api_key_masked = f"{api_key_str[:2]}..."

        # Build title with app_name prefix
        key_type = "fallback" if is_fallback else "primary"
        if self.app_name:
            title = f"[{self.app_name}] API Key Failure - {model_name}"
        else:
            title = f"API Key Failure - {model_name}"

        # Build detailed message
        message = f"API key '{model_name}' ({key_type}) has failed."
        if self.app_name:
            message = f"[{self.app_name}] " + message
        if provider:
            message += f"\nProvider: {provider}"
        if model_id:
            message += f"\nModel: {model_id}"
        if api_key_masked:
            message += f"\nAPI Key: {api_key_masked}"
        message += f"\nFailure Count: {failure_count}"
        message += f"\nError: {error[:500]}"  # Truncate long errors

        return AlertPayload(
            title=title,
            message=message,
            severity="critical" if is_fallback else "warning",
            alert_type="key_failure",
            timestamp=datetime.now(),
            details={
                "app_name": self.app_name,
                "key_name": model_name,
                "key_type": key_type,
                "provider": provider,
                "model": model_id,
                "api_key_masked": api_key_masked,
                "is_fallback": is_fallback,
                "failure_count": failure_count,
                "error_truncated": error[:500],
            },
            failed_key_name=model_name,
            failed_provider=provider,
            fallback_key_name=None,
            fallback_provider=None,
            error_message=error,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current status of all models."""
        if self.key_manager:
            return self.key_manager.get_status_summary()
        return {
            "model_names": self.model_names,
            "num_models": len(self.models),
        }
