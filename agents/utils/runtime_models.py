from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SUPERVISOR_MODEL = "gemini-2.5-flash"
DEFAULT_SUPERVISOR_TEMPERATURE = 0.7


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
    enabled: bool = True
