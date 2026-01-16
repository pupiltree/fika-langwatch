# fika-langwatch

LangChain wrapper with automatic fallback and alert notifications when API keys fail.

**Copyright (c) 2026 FIKA Private Limited. All Rights Reserved.**

## Features

| Feature | Description |
|---------|-------------|
| **Automatic Fallback** | When a model fails, automatically try the next one in the chain |
| **Smart Key Skipping** | Skip unhealthy keys to go straight to fallback (configurable timeout) |
| **Alert Notifications** | Get notified via Email, Slack, or Webhooks when keys fail |
| **Rate Limiting** | Built-in cooldown to prevent alert spam (in-memory, no Redis needed) |
| **Tool Binding** | Call `.bind_tools()` once, applies to ALL underlying models |
| **Sync & Async** | Supports both `.invoke()` and `.ainvoke()` |
| **Health Tracking** | Track key health status with automatic recovery detection |
| **Per-Key Alerts** | Alert on EACH key failure with full details (provider, model, masked key, app name) |

## Installation

```bash
pip install fika-langwatch
```

All dependencies are included by default:
- **Alert Channels:** Email (aiosmtplib), Slack (httpx), Webhook (httpx)
- **Providers:** Google Gemini, OpenAI, Anthropic Claude, OpenRouter

## Quick Start

### Option 1: Manual Models (Recommended)

```python
from langwatch import ChatWithFallback
from langwatch.alerts import EmailAlert
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

# Create your own models - works with ANY LangChain-compatible model
models = [
    ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key="..."),
    ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key="..."),
    ChatOpenAI(model="grok-4.1", base_url="https://openrouter.ai/api/v1", api_key="..."),
]

chat = ChatWithFallback(
    models=models,
    model_names=["gemini-1", "gemini-2", "fallback"],
    alerts=[EmailAlert(...)],
)

# Bind tools and use
chat_with_tools = chat.bind_tools(tools)
response = await chat_with_tools.ainvoke(messages)
```

### Option 2: Config-based (Auto-create Models)

```python
from langwatch import ChatWithFallback
from langwatch.alerts import EmailAlert, SlackAlert
from langchain_core.messages import HumanMessage

# Create with config - models are created automatically
chat = ChatWithFallback.from_config(
    models=[
        {
            "name": "gemini-1",
            "provider": "google",
            "model": "gemini-2.5-flash",
            "api_key": "AIza...",
        },
        {
            "name": "gemini-2",
            "provider": "google",
            "model": "gemini-2.5-flash",
            "api_key": "AIza...",
        },
        {
            "name": "fallback",
            "provider": "openrouter",
            "model": "x-ai/grok-4.1-fast",
            "api_key": "sk-...",
            "is_fallback": True,
        },
    ],
    alerts=[
        EmailAlert(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="alerts@company.com",
            password="app-password",
            to=["ops@company.com"],
        ),
        SlackAlert(webhook_url="https://hooks.slack.com/services/..."),
    ],
    app_name="MyApp",         # Shows in alerts: [MyApp] API Key Failure
    cooldown_seconds=300,     # Per-key cooldown (default: 5 minutes)
    skip_unhealthy=True,      # Skip failed keys (default: True)
    unhealthy_timeout=300,    # Retry failed keys after 5 minutes (default: 300s)
)

# Bind tools - applies to ALL models
chat_with_tools = chat.bind_tools([your_tool_1, your_tool_2])

# Use like any LangChain model (sync or async)
response = chat_with_tools.invoke([HumanMessage(content="Hello!")])
response = await chat_with_tools.ainvoke([HumanMessage(content="Hello!")])
```

---

## Feature Details

### 1. Automatic Fallback

When a model fails (rate limit, API error, etc.), the system automatically tries the next model in the chain.

```python
# Define multiple models - they're tried in order
models=[
    {"name": "primary-1", ...},
    {"name": "primary-2", ...},
    {"name": "fallback", ..., "is_fallback": True},
]
```

### 2. Smart Key Skipping (`skip_unhealthy`)

By default, unhealthy keys are skipped to avoid wasting time on failed APIs. After a timeout, they're retried automatically.

```python
chat = ChatWithFallback.from_config(
    models=[...],
    skip_unhealthy=True,      # Skip unhealthy keys (default: True)
    unhealthy_timeout=300,    # Retry after 5 minutes (default: 300 seconds)
)
```

**Behavior with `skip_unhealthy=True`:**
```
Request 1: Gemini-1 ❌ → Gemini-2 ❌ → Gemini-3 ❌ → Fallback ✅ (alert sent)
Request 2: Skip Gemini-1,2,3 → Fallback ✅ (fast! no wasted API calls)
Request 3: Skip Gemini-1,2,3 → Fallback ✅
...
After 5 min timeout:
Request N: Gemini-1 (retry) ✅ → Done! (key recovered)
```

**Behavior with `skip_unhealthy=False`:**
```
Request 1: Gemini-1 ❌ → Gemini-2 ❌ → Gemini-3 ❌ → Fallback ✅
Request 2: Gemini-1 ❌ → Gemini-2 ❌ → Gemini-3 ❌ → Fallback ✅ (slow, retries all)
```

### 3. Alert Notifications

Get notified when all primary keys fail and fallback is activated.

#### Email Alerts

```python
from langwatch.alerts import EmailAlert

alert = EmailAlert(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="alerts@company.com",
    password="your-app-password",  # Use Gmail App Password
    to=["ops@company.com"],
    cc=["team@company.com"],       # Optional
    bcc=["logs@company.com"],      # Optional
    from_name="LangWatch Alerts",  # Optional (default: "LangWatch Alerts")
    use_tls=True,                  # Optional (default: True)
)
```

#### Slack Alerts

```python
from langwatch.alerts import SlackAlert

alert = SlackAlert(
    webhook_url="https://hooks.slack.com/services/T.../B.../xxx",
    channel="#alerts",              # Optional - override webhook default
    username="LangWatch Bot",       # Optional
    icon_emoji=":warning:",         # Optional
)
```

#### Webhook Alerts (Generic HTTP)

```python
from langwatch.alerts import WebhookAlert

alert = WebhookAlert(
    url="https://your-api.com/alerts",
    headers={"Authorization": "Bearer token"},
    method="POST",                  # Optional (default: "POST")
    timeout=10.0,                   # Optional (default: 10 seconds)
)
```

### 4. Rate Limiting (Alert Cooldown)

Prevents alert spam by limiting how often alerts are sent.

```python
chat = ChatWithFallback.from_config(
    models=[...],
    alerts=[...],
    cooldown_seconds=3600,  # Only 1 alert per hour (default: 3600)
)
```

### 5. Tool Binding

Bind tools once - applies to ALL underlying models automatically.

```python
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base."""
    return "Results..."

@tool
def book_appointment(date: str, time: str) -> str:
    """Book an appointment."""
    return "Booked!"

# Bind tools to ALL models at once
chat_with_tools = chat.bind_tools([search_knowledge_base, book_appointment])

# Now all models (primary and fallback) have these tools bound
response = await chat_with_tools.ainvoke(messages)
```

### 6. Callbacks

Get notified programmatically when keys fail or fallback activates.

```python
def on_key_failure(key_name: str, error: str):
    """Called when any key fails."""
    print(f"Key {key_name} failed: {error}")
    # Log to your monitoring system, etc.

def on_fallback_activated(fallback_key: str):
    """Called when fallback is activated."""
    print(f"Now using fallback: {fallback_key}")
    # Trigger additional alerts, update dashboards, etc.

chat = ChatWithFallback.from_config(
    models=[...],
    alerts=[...],
    on_key_failure=on_key_failure,
    on_fallback_activated=on_fallback_activated,
)
```

### 7. Health Status Monitoring

Check the current status of all keys programmatically.

```python
status = chat.get_status()
print(status)
# {
#     "total_keys": 4,
#     "healthy_keys": 1,
#     "failed_keys": 3,
#     "all_primary_failed": True,
#     "keys": [
#         {"name": "gemini-1", "is_healthy": False, "failure_count": 5, ...},
#         {"name": "gemini-2", "is_healthy": False, "failure_count": 3, ...},
#         {"name": "gemini-3", "is_healthy": False, "failure_count": 2, ...},
#         {"name": "fallback", "is_healthy": True, "failure_count": 0, ...},
#     ]
# }
```

### 8. Per-Key Alerts with App Name

Alerts are sent on EVERY key failure with full details. Use `app_name` to identify which client/app the alert is from.

```python
chat = ChatWithFallback.from_config(
    models=[...],
    alerts=[...],
    app_name="ClientA",       # Shows in alert subject: [ClientA] API Key Failure
    cooldown_seconds=300,     # Per-key cooldown (default: 5 minutes)
)
```

**Alert example:**
```
[ClientA] API Key Failure - gemini-1

[ClientA] API key 'gemini-1' (primary) has failed.
Provider: google
Model: gemini-2.5-flash
API Key: AIza...Xyz9
Failure Count: 3
Error: Rate limit exceeded. Please try again in 60 seconds.
```

**Per-key cooldown prevents spam:**
```
gemini-1 fails → alert sent
gemini-1 fails again → NO alert (in 5 min cooldown)
gemini-2 fails → alert sent (different key)
After 5 min: gemini-1 fails → alert sent
```

---

## Supported Providers

When using `from_config()`, these providers are auto-created:

| Provider | Value | LangChain Class | Notes |
|----------|-------|-----------------|-------|
| Google Gemini | `"google"` | `ChatGoogleGenerativeAI` | Requires `langchain-google-genai` |
| OpenAI | `"openai"` | `ChatOpenAI` | Requires `langchain-openai` |
| Anthropic Claude | `"anthropic"` | `ChatAnthropic` | Requires `langchain-anthropic` |
| OpenRouter | `"openrouter"` | `ChatOpenAI` | Uses OpenRouter base_url |

For other providers (Grok, Mistral, etc.), create the model manually and pass it directly.

---

## Configuration Reference

### `ChatWithFallback.from_config()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `models` | `List[dict]` | Required | List of model configurations |
| `alerts` | `List[AlertChannel]` | `[]` | Alert channels (Email, Slack, Webhook) |
| `app_name` | `str` | `None` | App/client name for alert subject (e.g., "[MyApp] API Key Failure") |
| `cooldown_seconds` | `int` | `300` | Per-key cooldown between alerts (5 minutes default) |
| `skip_unhealthy` | `bool` | `True` | Skip unhealthy keys until timeout |
| `unhealthy_timeout` | `int` | `300` | Seconds before retrying unhealthy keys |
| `on_key_failure` | `Callable` | `None` | Callback when a key fails |
| `on_fallback_activated` | `Callable` | `None` | Callback when fallback activates |

### Model Configuration

```python
{
    "name": "gemini-1",           # Unique name for alerts/logging
    "provider": "google",         # Provider: google, openai, anthropic, openrouter
    "model": "gemini-2.5-flash",  # Model name
    "api_key": "AIza...",         # API key
    "is_fallback": False,         # True for fallback models (default: False)
    "extra_config": {             # Optional provider-specific config
        "temperature": 0.7,
        "max_retries": 0,
    }
}
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         Request                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Is key healthy OR timeout expired?                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │Gemini-1 │───▶│Gemini-2 │───▶│Gemini-3 │───▶│Fallback │      │
│  │(skip?)  │    │(skip?)  │    │(skip?)  │    │         │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
         Success ✅                       Failure ❌
              │                               │
              ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────────┐
│  Mark key healthy   │         │  Mark key unhealthy             │
│  Return response    │         │  Try next key                   │
└─────────────────────┘         │  If entering fallback → Alert   │
                                └─────────────────────────────────┘
```

---

## License

Copyright (c) 2026 FIKA Private Limited. All Rights Reserved.

This is proprietary software. Unauthorized copying, modification, or distribution is prohibited.

**Authors:**
- Rahul Kumar - rahul@pupiltree.ai | [GitHub](https://github.com/rahul20110)
- Nikhil Sukthe - nikhil@pupiltree.ai | [GitHub](https://github.com/Nikhils-G)

For licensing inquiries, contact: rahul@pupiltree.ai
