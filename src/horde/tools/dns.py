"""Python-native DNS address discovery with an optional fixed-tool fallback."""

import asyncio
import socket

from .base import ReconTool, ToolContext, ToolResult


class DnsTool(ReconTool):
    name = "dns"

    async def execute(self, target: str, options: dict, context: ToolContext) -> ToolResult:
        self.validate(target, options)
        host = target.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
        try:
            infos = await asyncio.wait_for(asyncio.to_thread(socket.getaddrinfo, host, None), context.timeout_seconds)
            addresses = sorted({info[4][0] for info in infos})
            return ToolResult(tool=self.name, target=target, ok=True, data={"hostname": host, "addresses": addresses})
        except (OSError, TimeoutError) as exc:
            return ToolResult(tool=self.name, target=target, ok=False, error=str(exc))
