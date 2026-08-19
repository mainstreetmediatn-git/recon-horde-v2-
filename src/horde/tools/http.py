"""Conservative HTTP metadata collection."""

import re

import httpx

from .base import ReconTool, ToolContext, ToolResult


class HttpTool(ReconTool):
    name = "http"

    async def execute(self, target: str, options: dict, context: ToolContext) -> ToolResult:
        self.validate(target, options)
        url = target if "://" in target else f"https://{target}"
        if not context.execute:
            return ToolResult(tool=self.name, target=target, ok=True, data={"planned_url": url, "dry_run": True})
        try:
            timeout = httpx.Timeout(context.timeout_seconds)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, max_redirects=5) as client:
                response = await client.get(url, headers={"User-Agent": "ReconHorde/2.0 authorized-recon"})
            body = response.content[: context.max_output_bytes]
            title_match = re.search(rb"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            title = title_match.group(1).decode("utf-8", errors="replace").strip() if title_match else None
            headers = {key.lower(): value[:512] for key, value in response.headers.items()}
            return ToolResult(tool=self.name, target=target, ok=True, data={
                "url": url, "status_code": response.status_code, "final_url": str(response.url),
                "headers": headers, "title": title, "response_bytes": len(response.content),
            })
        except httpx.HTTPError as exc:
            return ToolResult(tool=self.name, target=target, ok=False, error=str(exc))
