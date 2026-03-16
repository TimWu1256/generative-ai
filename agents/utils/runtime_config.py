from __future__ import annotations

import importlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agents.utils.mcp_adapters import create_mcp_node
from agents.utils.providers import validate_provider


@dataclass(frozen=True)
class SupervisorConfig:
    model: str
    temperature: float
    provider: str


@dataclass(frozen=True)
class NodeConfig:
    name: str
    adapter: str = "python"
    callable_path: str | None = None
    model: str | None = None
    temperature: float | None = None
    provider: str | None = None
    timeout_sec: float = 30.0
    mcp_url: str | None = None
    mcp_headers: dict[str, str] | None = None
    mcp_read_timeout: float = 300.0
    mcp_tool: str = "run_agent"
    enabled: bool = True


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


def _build_python_node(node: NodeConfig) -> Callable:
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


def _build_mcp_node(node: NodeConfig) -> Callable:
    if not node.mcp_url:
        raise ValueError(f"Node '{node.name}' requires 'mcp_url' for mcp adapter.")

    return create_mcp_node(
        node_name=node.name,
        url=node.mcp_url,
        tool_name=node.mcp_tool,
        timeout_sec=node.timeout_sec,
        headers=node.mcp_headers,
        read_timeout=node.mcp_read_timeout,
    )


def load_runtime_config(config_path: Path) -> tuple[SupervisorConfig, dict[str, Callable]]:
    with config_path.open("rb") as f:
        data = tomllib.load(f)

    supervisor_data = data.get("supervisor", {})
    model = supervisor_data.get("model", "gemini-2.5-flash")
    temperature = float(supervisor_data.get("temperature", 0.7))
    if supervisor_data.get("provider") is None:
        raise ValueError("[supervisor] must set 'provider'.")
    provider = validate_provider(str(supervisor_data["provider"]), "[supervisor]")
    supervisor = SupervisorConfig(model=model, temperature=temperature, provider=provider)

    nodes = data.get("nodes", [])
    if not nodes:
        raise ValueError("No nodes configured. Add at least one [[nodes]] entry.")

    node_callables: dict[str, Callable] = {}
    for node_item in nodes:
        node = NodeConfig(
            name=str(node_item["name"]),
            adapter=str(node_item.get("adapter", "python")),
            callable_path=(
                str(node_item["callable"]) if node_item.get("callable") is not None else None
            ),
            model=str(node_item["model"]) if node_item.get("model") is not None else None,
            temperature=(
                float(node_item["temperature"])
                if node_item.get("temperature") is not None
                else None
            ),
            provider=str(node_item["provider"]) if node_item.get("provider") is not None else None,
            timeout_sec=float(node_item.get("timeout_sec", 30.0)),
            mcp_url=(str(node_item["mcp_url"]) if node_item.get("mcp_url") is not None else None),
            mcp_headers=(
                {str(k): str(v) for k, v in node_item["mcp_headers"].items()}
                if node_item.get("mcp_headers") is not None
                else None
            ),
            mcp_read_timeout=float(node_item.get("mcp_read_timeout", 300.0)),
            mcp_tool=str(node_item.get("mcp_tool", "run_agent")),
            enabled=bool(node_item.get("enabled", True)),
        )
        if not node.enabled:
            continue

        if node.name in node_callables:
            raise ValueError(f"Duplicate node name '{node.name}' in config.")

        if node.adapter == "python":
            node_callables[node.name] = _build_python_node(node)
        elif node.adapter == "mcp":
            node_callables[node.name] = _build_mcp_node(node)
        else:
            raise ValueError(
                f"Unsupported adapter '{node.adapter}' for node '{node.name}'. "
                "Supported adapters: python, mcp."
            )

    if not node_callables:
        raise ValueError("All configured nodes are disabled. Enable at least one node.")

    return supervisor, node_callables
