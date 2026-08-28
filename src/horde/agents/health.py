"""Deterministic health scoring and stale heartbeat detection."""

from dataclasses import dataclass
from datetime import datetime

from horde.core.models import Agent, utcnow


@dataclass(frozen=True)
class HealthInputs:
    heartbeat_age_seconds: float = 0
    success_rate: float = 1
    consecutive_failures: int = 0
    worker_exceptions: int = 0
    memory_pressure: float = 0
    disk_pressure: float = 0
    tool_availability: float = 1
    database_available: bool = True
    queue_backlog: int = 0


def score_health(inputs: HealthInputs, heartbeat_timeout: int = 120) -> int:
    score = 100.0
    score -= min(30, max(0, inputs.heartbeat_age_seconds / max(heartbeat_timeout, 1) * 30))
    score -= min(30, max(0, 1 - inputs.success_rate) * 30)
    score -= min(25, inputs.consecutive_failures * 5)
    score -= min(10, inputs.worker_exceptions * 2)
    score -= min(10, max(0, inputs.memory_pressure) * 10)
    score -= min(10, max(0, inputs.disk_pressure) * 10)
    score -= min(15, max(0, 1 - inputs.tool_availability) * 15)
    score -= 15 if not inputs.database_available else 0
    score -= min(10, inputs.queue_backlog / 100)
    return max(0, min(100, round(score)))


def heartbeat_age(agent: Agent, now: datetime | None = None) -> float:
    if agent.heartbeat_at is None:
        return float("inf")
    return max(0, (now or utcnow() - agent.heartbeat_at).total_seconds())
