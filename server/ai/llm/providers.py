import os
import random
import logging
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("ai.llm.providers")
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
RETIRED_GEMINI_MODELS = {"gemini-2.5-flash", "gemini-2.5-flash-lite"}
RETIRED_GROQ_MODELS = {"mixtral-8x7b-32768"}


def get_chat_model(*, user: Any = None, streaming: bool = True):
    """
    Factory for the chat LLM used across the app.
    Supports user-provided BYOK (Groq or Gemini) with automatic fallback
    to the system environment keys if no custom key is configured.
    """
    # Check if a user is passed with custom AI settings
    if user and hasattr(user, "ai_settings"):
        try:
            settings = user.ai_settings
            if settings.provider == "groq" and settings.groq_api_key:
                from langchain_groq import ChatGroq
                model_name = settings.preferred_model or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
                if model_name in RETIRED_GROQ_MODELS:
                    model_name = DEFAULT_GROQ_MODEL
                temp_env = os.getenv("GROQ_TEMPERATURE", "0.3").strip()
                temperature = float(temp_env) if temp_env else 0.3
                return ChatGroq(
                    model=model_name,
                    api_key=settings.groq_api_key,
                    temperature=temperature,
                    streaming=streaming,
                )
            elif settings.provider == "gemini" and settings.gemini_api_key:
                model_name = settings.preferred_model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
                if model_name in RETIRED_GEMINI_MODELS:
                    model_name = DEFAULT_GEMINI_MODEL
                temp_env = os.getenv("GEMINI_TEMPERATURE", "0.3").strip()
                temperature = float(temp_env) if temp_env else 0.3
                return ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    google_api_key=settings.gemini_api_key,
                    streaming=streaming,
                    convert_system_message_to_human=False,
                )
        except Exception as exc:
            logger.warning("Failed to load user custom AI settings, falling back to system defaults: %s", exc)

    # 1. Fallback: Server environment default keys (Gemini rotation or single key)
    api_keys_raw = os.getenv("GEMINI_API_KEYS", "").strip()
    if api_keys_raw:
        api_keys = [
            key.strip()
            for key in api_keys_raw.split(",")
            if key.strip() and not key.strip().lower().startswith("your_")
        ]
        selected_key = random.choice(api_keys) if api_keys else None
    else:
        selected_key = None

    if not selected_key:
        selected_key = os.getenv("GEMINI_API_KEY")
        if selected_key and selected_key.lower().startswith("your_"):
            selected_key = None

    # If Gemini is not set, check if GROQ_API_KEY is available in environment
    if not selected_key and os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        if model_name in RETIRED_GROQ_MODELS:
            model_name = DEFAULT_GROQ_MODEL
        return ChatGroq(
            model=model_name,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.3,
            streaming=streaming,
        )

    if not selected_key:
        raise ValueError(
            "Missing API Key: Please configure an API key in AI Settings or set "
            "'GEMINI_API_KEY' or 'GROQ_API_KEY' in your environment variables."
        )

    temp_env = os.getenv("GEMINI_TEMPERATURE", "0.3").strip()
    temperature = float(temp_env) if temp_env else 0.3

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    if model_name in RETIRED_GEMINI_MODELS:
        model_name = DEFAULT_GEMINI_MODEL

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=selected_key,
        streaming=streaming,
        convert_system_message_to_human=False,
    )
