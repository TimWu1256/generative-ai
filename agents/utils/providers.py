from __future__ import annotations

ALLOWED_PROVIDERS = {"google", "openai", "anthropic"}


def validate_provider(provider: str, scope: str = "provider") -> str:
    normalized = provider.strip().lower()
    if normalized not in ALLOWED_PROVIDERS:
        allowed = ", ".join(sorted(ALLOWED_PROVIDERS))
        raise ValueError(
            f"{scope} has unsupported provider '{provider}'. "
            f"Allowed providers: {allowed}."
        )
    return normalized