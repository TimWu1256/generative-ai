from __future__ import annotations

from pathlib import Path
from typing import Callable

from agents.utils.runtime_loader import RuntimeConfigLoader
from agents.utils.runtime_models import (
    MCPNodeConfig,
    NodeConfig,
    PythonNodeConfig,
    SupervisorConfig,
)


def load_runtime_config(config_path: Path) -> tuple[SupervisorConfig, dict[str, Callable]]:
    return RuntimeConfigLoader(config_path).load()


__all__ = [
    "SupervisorConfig",
    "NodeConfig",
    "PythonNodeConfig",
    "MCPNodeConfig",
    "load_runtime_config",
]
