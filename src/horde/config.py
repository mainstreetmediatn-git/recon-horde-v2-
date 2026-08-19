"""Typed runtime configuration with safe defaults for local development."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str | None = None
    supabase_service_role_key: SecretStr | None = None
    execute_tools: bool = Field(False, alias="HORDE_EXECUTE_TOOLS")
    tool_allowlist: list[str] = Field(default_factory=lambda: ["dns", "http", "tls", "ports"], alias="HORDE_TOOL_ALLOWLIST")
    tool_timeout_seconds: float = Field(30.0, alias="HORDE_TOOL_TIMEOUT_SECONDS", gt=0, le=3600)
    worker_interval_seconds: float = Field(5.0, alias="HORDE_WORKER_INTERVAL_SECONDS", gt=0)
    retire_health_below: int = Field(40, alias="HORDE_RETIRE_HEALTH_BELOW", ge=0, le=100)
    agent_max_cycles: int = Field(1000, alias="HORDE_AGENT_MAX_CYCLES", gt=0)
    agent_heartbeat_timeout: int = Field(120, alias="HORDE_AGENT_HEARTBEAT_TIMEOUT", gt=0)
    max_concurrent_jobs: int = Field(4, alias="HORDE_MAX_CONCURRENT_JOBS", gt=0)
    result_max_bytes: int = Field(1_048_576, alias="HORDE_RESULT_MAX_BYTES", gt=0)
    log_level: str = Field("INFO", alias="HORDE_LOG_LEVEL")
    data_dir: Path = Field(Path(".horde-data"), alias="HORDE_DATA_DIR")

    @field_validator("tool_allowlist", mode="before")
    @classmethod
    def split_allowlist(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def validate_production(self) -> None:
        """Fail clearly when production execution is enabled without Supabase credentials."""
        if self.execute_tools and (not self.supabase_url or not self.supabase_service_role_key):
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required when tools execute")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
