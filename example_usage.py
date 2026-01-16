"""
Simple test of fika-langwatch with Gemini and OpenAI fallback.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langwatch import ChatWithFallback, KeyManager

# Create models manually
gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="YOUR_GEMINI_API_KEY",
    max_retries=0,
)

openai = ChatOpenAI(
    model="gpt-4o-mini",
    api_key="YOUR_OPENAI_API_KEY",
    max_retries=0,
)

# Create KeyManager for health tracking
key_manager = KeyManager([
    {"name": "gemini", "key": "xxx", "provider": "google", "model": "gemini-2.0-flash"},
    {"name": "openai", "key": "xxx", "provider": "openai", "model": "gpt-4o-mini", "is_fallback": True},
])

# Create ChatWithFallback
chat = ChatWithFallback(
    models=[gemini, openai],
    model_names=["gemini", "openai"],
    key_manager=key_manager,
    app_name="TestApp",
)

# Test it
response = chat.invoke("Hello, how are you?")
print(response.content)
print(f"\nStatus: {chat.get_status()}")
