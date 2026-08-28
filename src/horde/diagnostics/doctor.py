"""Operator diagnostics with explicit PASS/WARN/FAIL results."""

import shutil
import sys
from pathlib import Path

from horde.config import Settings
from horde.tools.registry import ToolRegistry


def doctor(settings: Settings, registry: ToolRegistry) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = [{"check": "python", "status": "PASS", "detail": sys.version.split()[0]}]
    data_dir: Path = settings.data_dir
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks.append({"check": "data_dir", "status": "PASS", "detail": str(data_dir)})
    except OSError as exc:
        checks.append({"check": "data_dir", "status": "FAIL", "detail": str(exc)})
    checks.append({"check": "supabase_config", "status": "PASS" if settings.supabase_url and settings.supabase_service_role_key else "WARN",
                   "detail": "configured" if settings.supabase_url and settings.supabase_service_role_key else "not configured for local dry-run"})
    checks.append({"check": "tool_adapters", "status": "PASS" if registry.names() else "FAIL", "detail": ", ".join(registry.names())})
    checks.append({"check": "docker", "status": "PASS" if shutil.which("docker") or shutil.which("podman") else "WARN", "detail": "optional"})
    return checks
