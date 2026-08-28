"""TLS certificate metadata without probing beyond the requested host and port."""

import asyncio
import socket
import ssl
from datetime import UTC, datetime

from .base import ReconTool, ToolContext, ToolResult


class TlsTool(ReconTool):
    name = "tls"

    async def execute(self, target: str, options: dict, context: ToolContext) -> ToolResult:
        self.validate(target, options)
        host = target.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
        port = int(options.get("port", 443))
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if not context.execute:
            return ToolResult(tool=self.name, target=target, ok=True, data={"host": host, "port": port, "dry_run": True})

        def inspect() -> dict:
            context_ssl = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=context.timeout_seconds) as raw:
                with context_ssl.wrap_socket(raw, server_hostname=host) as conn:
                    cert = conn.getpeercert()
                    sans = [value for kind, value in cert.get("subjectAltName", []) if kind == "DNS"]
                    expires = cert.get("notAfter")
                    return {"host": host, "port": port, "subject": str(cert.get("subject")),
                            "issuer": str(cert.get("issuer")), "sans": sans,
                            "expires_at": datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC).isoformat() if expires else None,
                            "protocol": conn.version()}
        try:
            return ToolResult(tool=self.name, target=target, ok=True, data=await asyncio.to_thread(inspect))
        except (OSError, ssl.SSLError, ValueError) as exc:
            return ToolResult(tool=self.name, target=target, ok=False, error=str(exc))
