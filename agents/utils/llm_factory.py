from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from agents.utils.providers import validate_provider


@dataclass(frozen=True)
class ProviderSpec:
    module_name: str
    class_name: str
    package_name: str


class ModelClassResolver:
    def __init__(self, provider_specs: dict[str, ProviderSpec]):
        self._provider_specs = provider_specs

    def resolve(self, provider: str) -> type:
        normalized_provider = validate_provider(provider, "create_chat_model")
        spec = self._provider_specs.get(normalized_provider)
        if spec is None:
            raise ValueError(f"Unsupported provider '{normalized_provider}'.")

        try:
            module = importlib.import_module(spec.module_name)
            model_class = getattr(module, spec.class_name)
        except (ImportError, AttributeError) as exc:
            raise ImportError(
                f"Provider '{normalized_provider}' requires package '{spec.package_name}'. "
                f"Install it with: pip install {spec.package_name}"
            ) from exc

        return model_class


_PROVIDER_SPECS = {
    "google": ProviderSpec(
        module_name="langchain_google_genai",
        class_name="ChatGoogleGenerativeAI",
        package_name="langchain-google-genai",
    ),
    "openai": ProviderSpec(
        module_name="langchain_openai",
        class_name="ChatOpenAI",
        package_name="langchain-openai",
    ),
}

_RESOLVER = ModelClassResolver(_PROVIDER_SPECS)


def create_chat_model(
    *,
    model: str,
    temperature: float,
    provider: str,
    **kwargs: Any,
):
    model_class = _RESOLVER.resolve(provider)
    return model_class(model=model, temperature=temperature, **kwargs)