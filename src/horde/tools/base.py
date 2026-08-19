"""Safe adapter interface. Database rows select adapters; they never supply commands."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


class ToolContext(BaseModel):
    timeout_seconds: float = 30
    max_output_bytes: int = 1_048_576
    execute: bool = False


class ToolResult(BaseModel):
    tool: str
    target: str
    ok: bool
    data: dict[str, Any] = {}
    raw: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


class ReconTool(ABC):
    name: str

    def validate(self, target: str, options: dict[str, Any]) -> None:
        if not target.strip():
            raise ValueError("target is required")

    @abstractmethod
    async def execute(self, target: str, options: dict[str, Any], context: ToolContext) -> ToolResult:
        raise NotImplementedError

    def normalize(self, result: ToolResult) -> list[dict[str, Any]]:
        return [result.data] if result.ok and result.data else []

    @staticmethod
    async def run_executable(executable: str, args: list[str], context: ToolContext) -> ProcessResult:
        """Run a fixed executable plus argument vector; shell execution is impossible here."""
        if any("\x00" in item for item in [executable, *args]):
            raise ValueError("NUL bytes are not allowed in process arguments")
        process = await asyncio.create_subprocess_exec(
            executable,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), context.timeout_seconds)
        except TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"{executable} timed out") from None
        return ProcessResult(
            process.returncode or 0,
            stdout[: context.max_output_bytes].decode("utf-8", errors="replace"),
            stderr[: context.max_output_bytes].decode("utf-8", errors="replace"),
        )

    @staticmethod
    def json_data(value: object) -> dict[str, Any]:
        return json.loads(json.dumps(value, default=str))
