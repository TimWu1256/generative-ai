from __future__ import annotations

import importlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agents.utils.external_adapters import create_http_node, create_mcp_node


@dataclass(frozen=True)
class SupervisorConfig:
    model: str
    temperature: float
    provider: str | None = None


@dataclass(frozen=True)
class NodeConfig:
    name: str
    adapter: str = "python"
    callable_path: str | None = None
    callable_type: str = "node"
    model: str | None = None
    temperature: float | None = None
    provider: str | None = None
    endpoint: str | None = None
    method: str = "POST"
    headers: dict[str, str] | None = None
    timeout_sec: float = 30.0
    mcp_command: str | None = None
    mcp_args: list[str] | None = None
    mcp_tool: str = "run_agent"
    mcp_env: dict[str, str] | None = None
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

    symbol = _import_callable(node.callable_path)

    if node.callable_type == "node":
        if node.model is not None or node.temperature is not None or node.provider is not None:
            raise ValueError(
                f"Node '{node.name}' sets model options but uses callable_type='node'. "
                "Use callable_type='factory' to inject model/provider settings."
            )
        return symbol

    if node.callable_type == "factory":
        kwargs = {}
        if node.model is not None:
            kwargs["model"] = node.model
        if node.temperature is not None:
            kwargs["temperature"] = node.temperature
        if node.provider is not None:
            kwargs["provider"] = node.provider
        produced = symbol(**kwargs)
        if not callable(produced):
            raise ValueError(
                f"Factory callable '{node.callable_path}' did not return a callable node."
            )
        return produced

    raise ValueError(
        f"Invalid callable_type '{node.callable_type}' for node '{node.name}'. "
        "Use 'node' or 'factory'."
    )


def _build_http_node(node: NodeConfig) -> Callable:
    if not node.endpoint:
        raise ValueError(f"Node '{node.name}' requires 'endpoint' for http adapter.")
    return create_http_node(
        node_name=node.name,
        endpoint=node.endpoint,
        timeout_sec=node.timeout_sec,
        method=node.method,
        headers=node.headers,
    )


def _build_mcp_node(node: NodeConfig) -> Callable:
    if not node.mcp_command:
        raise ValueError(f"Node '{node.name}' requires 'mcp_command' for mcp adapter.")

    return create_mcp_node(
        node_name=node.name,
        command=node.mcp_command,
        args=node.mcp_args,
        tool_name=node.mcp_tool,
        timeout_sec=node.timeout_sec,
        env=node.mcp_env,
    )


def load_runtime_config(config_path: Path) -> tuple[SupervisorConfig, dict[str, Callable]]:
    with config_path.open("rb") as f:
        data = tomllib.load(f)

    supervisor_data = data.get("supervisor", {})
    model = supervisor_data.get("model", "gemini-2.5-flash")
    temperature = float(supervisor_data.get("temperature", 0.7))
    provider = (
        str(supervisor_data["provider"])
        if supervisor_data.get("provider") is not None
        else None
    )
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
            callable_type=str(node_item.get("callable_type", "node")),
            model=str(node_item["model"]) if node_item.get("model") is not None else None,
            temperature=(
                float(node_item["temperature"])
                if node_item.get("temperature") is not None
                else None
            ),
            provider=str(node_item["provider"]) if node_item.get("provider") is not None else None,
            endpoint=str(node_item["endpoint"]) if node_item.get("endpoint") is not None else None,
            method=str(node_item.get("method", "POST")),
            headers=(
                {str(k): str(v) for k, v in node_item["headers"].items()}
                if node_item.get("headers") is not None
                else None
            ),
            timeout_sec=float(node_item.get("timeout_sec", 30.0)),
            mcp_command=(
                str(node_item["mcp_command"])
                if node_item.get("mcp_command") is not None
                else None
            ),
            mcp_args=(
                [str(item) for item in node_item.get("mcp_args", [])]
                if node_item.get("mcp_args") is not None
                else None
            ),
            mcp_tool=str(node_item.get("mcp_tool", "run_agent")),
            mcp_env=(
                {str(k): str(v) for k, v in node_item["mcp_env"].items()}
                if node_item.get("mcp_env") is not None
                else None
            ),
            enabled=bool(node_item.get("enabled", True)),
        )
        if not node.enabled:
            continue

        if node.name in node_callables:
            raise ValueError(f"Duplicate node name '{node.name}' in config.")

        if node.adapter == "python":
            node_callables[node.name] = _build_python_node(node)
        elif node.adapter == "http":
            node_callables[node.name] = _build_http_node(node)
        elif node.adapter == "mcp":
            node_callables[node.name] = _build_mcp_node(node)
        else:
            raise ValueError(
                f"Unsupported adapter '{node.adapter}' for node '{node.name}'. "
                "Supported adapters: python, http, mcp."
            )

    if not node_callables:
        raise ValueError("All configured nodes are disabled. Enable at least one node.")

    return supervisor, node_callables
