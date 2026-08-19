"""Allowlisted adapter registry."""

from collections.abc import Iterable

from .base import ReconTool
from .dns import DnsTool
from .http import HttpTool
from .ports import PortsTool
from .tls import TlsTool


class ToolRegistry:
    def __init__(self, tools: Iterable[ReconTool] = ()) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def register(self, tool: ReconTool) -> None:
        if not tool.name.isidentifier():
            raise ValueError("tool names must be identifiers")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ReconTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"tool adapter is not registered: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tools)

    def doctor(self) -> dict[str, str]:
        return {name: "native" for name in self.names()}


def default_registry() -> ToolRegistry:
    return ToolRegistry([DnsTool(), HttpTool(), TlsTool(), PortsTool()])
