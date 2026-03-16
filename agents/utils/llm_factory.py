from __future__ import annotations

from typing import Any


def _normalize_provider(provider: str) -> str:
    aliases = {
        "google": "google",
        "gemini": "google",
        "openai": "openai",
        "anthropic": "anthropic",
        "claude": "anthropic",
    }
    normalized = aliases.get(provider.strip().lower())
    if not normalized:
        supported = ", ".join(sorted(set(aliases.values())))
        raise ValueError(
            f"Unsupported provider '{provider}'. Supported providers: {supported}."
        )
    return normalized


def detect_provider_from_model(model: str) -> str:
    model_name = model.strip().lower()

    if not model_name:
        raise ValueError("Model name cannot be empty.")

    if (
        "gemini" in model_name
        or model_name.startswith("models/gemini")
        or model_name.startswith("google/")
    ):
        return "google"

    if (
        model_name.startswith("gpt")
        or model_name.startswith("o1")
        or model_name.startswith("o3")
        or model_name.startswith("openai/")
    ):
        return "openai"

    if "claude" in model_name or model_name.startswith("anthropic/"):
        return "anthropic"

    raise ValueError(
        f"Cannot infer provider from model '{model}'. "
        "Set provider explicitly in config (google/openai/anthropic)."
    )


def create_chat_model(
    *,
    model: str,
    temperature: float,
    provider: str | None = None,
    **kwargs: Any,
):
    resolved_provider = (
        _normalize_provider(provider)
        if provider is not None
        else detect_provider_from_model(model)
    )

    if resolved_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, temperature=temperature, **kwargs)

    if resolved_provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "Provider 'openai' requires package 'langchain-openai'. "
                "Install it with: pip install langchain-openai"
            ) from exc
        return ChatOpenAI(model=model, temperature=temperature, **kwargs)

    if resolved_provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise ImportError(
                "Provider 'anthropic' requires package 'langchain-anthropic'. "
                "Install it with: pip install langchain-anthropic"
            ) from exc
        return ChatAnthropic(model=model, temperature=temperature, **kwargs)

    raise ValueError(f"Unsupported provider '{resolved_provider}'.")