from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SUPERVISOR_MODEL = "gemini-2.5-flash"
DEFAULT_SUPERVISOR_TEMPERATURE = 0.7


@dataclass(frozen=True)
class SupervisorConfig:
    """Supervisor Node 的執行參數設定。

    用於描述 supervisor 在啟動時需要的模型、溫度與供應商資訊。
    """

    model: str
    temperature: float
    provider: str


@dataclass(frozen=True)
class NodeConfig:
    """Worker Node (subagent) 的設定資料。

    目前僅支援 `python` 類型節點，包含 callable 路徑與模型推論參數。
    """

    name: str
    adapter: str = "python"
    callable_path: str | None = None
    model: str | None = None
    temperature: float | None = None
    provider: str | None = None
    enabled: bool = True
