from __future__ import annotations

from pathlib import Path
from typing import Callable

from agents.utils.runtime_loader import RuntimeConfigLoader
from agents.utils.runtime_models import (
    NodeConfig,
    SupervisorConfig,
)


def load_runtime_config(config_path: Path) -> tuple[SupervisorConfig, dict[str, Callable]]:
    """對外提供的 runtime 設定載入入口。

    讀取指定 TOML 檔，回傳 supervisor 設定與節點 callable 映射。
    """

    return RuntimeConfigLoader(config_path).load()


__all__ = [
    "SupervisorConfig",
    "NodeConfig",
    "load_runtime_config",
]
