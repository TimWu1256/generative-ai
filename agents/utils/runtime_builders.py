from __future__ import annotations

import importlib
from typing import Callable

from agents.utils.providers import validate_provider
from agents.utils.runtime_models import NodeConfig


def _import_callable(path: str) -> Callable:
    module_name, sep, symbol_name = path.partition(":")
    if not sep:
        raise ValueError(
            f"Invalid callable path '{path}'. Expected format 'module.submodule:symbol'."
        )

    module = importlib.import_module(module_name)
    symbol = getattr(module, symbol_name, None)
    if symbol is None or not callable(symbol):
        raise ValueError(f"Callable '{symbol_name}' not found in module '{module_name}'.")
    return symbol


class NodeBuilderRegistry:
    def build(self, node: NodeConfig) -> Callable:
        if node.adapter == "python":
            return self._build_python_node(node)
        raise ValueError(
            f"Unsupported adapter '{node.adapter}' for node '{node.name}'. "
            "Supported adapters: python."
        )

    def _build_python_node(self, node: NodeConfig) -> Callable:
        if not node.callable_path:
            raise ValueError(f"Node '{node.name}' requires 'callable' for python adapter.")
        if node.provider is None:
            raise ValueError(
                f"Node '{node.name}' uses adapter='python' and must set 'provider'."
            )
        if node.model is None:
            raise ValueError(
                f"Node '{node.name}' uses adapter='python' and must set 'model'."
            )

        symbol = _import_callable(node.callable_path)
        normalized_provider = validate_provider(node.provider, f"Node '{node.name}'")
        kwargs = {"model": node.model, "provider": normalized_provider}
        if node.temperature is not None:
            kwargs["temperature"] = node.temperature

        produced = symbol(**kwargs)
        if not callable(produced):
            raise ValueError(
                f"Factory callable '{node.callable_path}' did not return a callable node."
            )
        return produced

    
