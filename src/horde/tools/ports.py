"""Bounded TCP connectivity checks for explicitly requested ports."""

import asyncio

from .base import ReconTool, ToolContext, ToolResult


class PortsTool(ReconTool):
    name = "ports"

    async def execute(self, target: str, options: dict, context: ToolContext) -> ToolResult:
        self.validate(target, options)
        host = target.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
        requested = options.get("ports", [80, 443])
        ports = sorted({int(port) for port in requested})
        if len(ports) > 64 or any(port < 1 or port > 65535 for port in ports):
            raise ValueError("ports must contain at most 64 values in the range 1..65535")
        if not context.execute:
            return ToolResult(tool=self.name, target=target, ok=True, data={"host": host, "ports": ports, "dry_run": True})

        async def check(port: int) -> dict:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), context.timeout_seconds)
                writer.close()
                await writer.wait_closed()
                return {"port": port, "state": "open"}
            except (OSError, TimeoutError):
                return {"port": port, "state": "closed_or_filtered"}

        return ToolResult(tool=self.name, target=target, ok=True, data={"host": host, "observations": await asyncio.gather(*(check(port) for port in ports))})
