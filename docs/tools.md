# Tool adapters

The default registry includes native DNS, HTTP metadata, TLS certificate, and bounded TCP port adapters. Each adapter validates options and returns a typed `ToolResult`. External tools can be added as fixed adapters using `asyncio.create_subprocess_exec`; never pass database text to a shell.

Execution is disabled by default. HTTP, TLS, and ports require `HORDE_EXECUTE_TOOLS=true`; dry-run results show the planned operation without touching a target.
