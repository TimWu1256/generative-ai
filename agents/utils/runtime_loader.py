from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Callable

from agents.utils.providers import validate_provider
from agents.utils.runtime_builders import NodeBuilderRegistry
from agents.utils.runtime_models import (
    DEFAULT_SUPERVISOR_MODEL,
    DEFAULT_SUPERVISOR_TEMPERATURE,
    NodeConfig,
    SupervisorConfig,
)


class RuntimeConfigLoader:
    def __init__(
        self,
        config_path: Path,
        builder_registry: NodeBuilderRegistry | None = None,
    ):
        self._config_path = config_path
        self._builder_registry = builder_registry or NodeBuilderRegistry()

    def load(self) -> tuple[SupervisorConfig, dict[str, Callable]]:
        data = self._load_toml()
        supervisor = self._parse_supervisor(data)
        node_callables = self._parse_nodes(data)
        return supervisor, node_callables

    def _load_toml(self) -> dict[str, Any]:
        with self._config_path.open("rb") as f:
            return tomllib.load(f)

    def _parse_supervisor(self, data: dict[str, Any]) -> SupervisorConfig:
        supervisor_data = data.get("supervisor", {})
        if supervisor_data.get("provider") is None:
            raise ValueError("[supervisor] must set 'provider'.")

        return SupervisorConfig(
            model=str(supervisor_data.get("model", DEFAULT_SUPERVISOR_MODEL)),
            temperature=float(
                supervisor_data.get("temperature", DEFAULT_SUPERVISOR_TEMPERATURE)
            ),
            provider=validate_provider(str(supervisor_data["provider"]), "[supervisor]"),
        )

    def _parse_nodes(self, data: dict[str, Any]) -> dict[str, Callable]:
        nodes_data = data.get("nodes", [])
        if not nodes_data:
            raise ValueError("No nodes configured. Add at least one [[nodes]] entry.")

        node_callables: dict[str, Callable] = {}
        for node_item in nodes_data:
            node = self._parse_node(node_item)
            if not node.enabled:
                continue

            if node.name in node_callables:
                raise ValueError(f"Duplicate node name '{node.name}' in config.")

            node_callables[node.name] = self._builder_registry.build(node)

        if not node_callables:
            raise ValueError("All configured nodes are disabled. Enable at least one node.")

        return node_callables

    def _parse_node(self, node_item: dict[str, Any]) -> NodeConfig:
        return NodeConfig(
            name=str(node_item["name"]),
            adapter=str(node_item.get("adapter", "python")),
            callable_path=self._optional_str(node_item, "callable"),
            model=self._optional_str(node_item, "model"),
            temperature=self._optional_float(node_item, "temperature"),
            provider=self._optional_str(node_item, "provider"),
            timeout_sec=float(node_item.get("timeout_sec", 30.0)),
            
            enabled=bool(node_item.get("enabled", True)),
        )

    @staticmethod
    def _optional_str(node_item: dict[str, Any], key: str) -> str | None:
        value = node_item.get(key)
        return str(value) if value is not None else None

    @staticmethod
    def _optional_float(node_item: dict[str, Any], key: str) -> float | None:
        value = node_item.get(key)
        return float(value) if value is not None else None

    @staticmethod
    def _optional_string_map(
        node_item: dict[str, Any],
        key: str,
    ) -> dict[str, str] | None:
        value = node_item.get(key)
        if value is None:
            return None
        return {str(k): str(v) for k, v in value.items()}
