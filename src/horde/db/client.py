"""Small Supabase REST adapter; service-role credentials never leave this process."""

from typing import Any

import httpx

from horde.config import Settings


class SupabaseClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Supabase URL and service-role key are required")
        self.base_url = settings.supabase_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"apikey": settings.supabase_service_role_key.get_secret_value(),
                     "Authorization": f"Bearer {settings.supabase_service_role_key.get_secret_value()}",
                     "Content-Type": "application/json"},
            transport=transport,
            timeout=settings.tool_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def table(self, table: str, method: str = "GET", payload: Any = None, **params: Any) -> Any:
        if not table.replace("_", "").isalnum():
            raise ValueError("invalid table name")
        response = await self._client.request(method, f"/rest/v1/{table}", json=payload, params=params)
        response.raise_for_status()
        return response.json() if response.content else None

    async def rpc(self, function: str, payload: dict[str, Any]) -> Any:
        if not function.replace("_", "").isalnum():
            raise ValueError("invalid function name")
        response = await self._client.post(f"/rest/v1/rpc/{function}", json=payload)
        response.raise_for_status()
        return response.json() if response.content else None
