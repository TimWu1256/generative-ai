from __future__ import annotations

import importlib
from typing import Any

from agents.utils.providers import validate_provider

def create_chat_model(
    *,
    model: str,
    temperature: float,
    provider: str,
    **kwargs: Any,
):
    resolved_provider = validate_provider(provider, "create_chat_model")

    if resolved_provider == "google":
        try:
            module = importlib.import_module("langchain_google_genai")
            ChatGoogleGenerativeAI = getattr(module, "ChatGoogleGenerativeAI")
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                "Provider 'google' requires package 'langchain-google-genai'. "
                "Install it with: pip install langchain-google-genai"
            ) from exc
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, **kwargs)

    if resolved_provider == "openai":
        try:
            module = importlib.import_module("langchain_openai")
            ChatOpenAI = getattr(module, "ChatOpenAI")
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                "Provider 'openai' requires package 'langchain-openai'. "
                "Install it with: pip install langchain-openai"
            ) from exc
        return ChatOpenAI(model=model, temperature=temperature, **kwargs)

    if resolved_provider == "anthropic":
        try:
            module = importlib.import_module("langchain_anthropic")
            ChatAnthropic = getattr(module, "ChatAnthropic")
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                "Provider 'anthropic' requires package 'langchain-anthropic'. "
                "Install it with: pip install langchain-anthropic"
            ) from exc
        return ChatAnthropic(model=model, temperature=temperature, **kwargs)

    raise ValueError(f"Unsupported provider '{resolved_provider}'.")