"""Shared domain models used by adapters, workers, and persistence."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class JobState(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(StrEnum):
    PROVISIONING = "provisioning"
    READY = "ready"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRING = "retiring"
    RETIRED = "retired"
    FAILED = "failed"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    target: str
    tool: str
    options: dict[str, Any] = Field(default_factory=dict)
    state: JobState = JobState.QUEUED
    attempt_count: int = 0
    max_attempts: int = Field(3, ge=1, le=10)
    lease_expires_at: datetime | None = None
    worker_id: str | None = None
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Agent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    name: str
    generation: int = Field(1, ge=1)
    status: AgentStatus = AgentStatus.READY
    health_score: int = Field(100, ge=0, le=100)
    cycles_completed: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    consecutive_failures: int = 0
    max_cycles: int = Field(1000, ge=1)
    heartbeat_at: datetime | None = None
    parent_id: UUID | None = None
    successor_id: UUID | None = None


class ExecutionEvent(BaseModel):
    agent_id: UUID
    job_id: UUID
    event: str
    duration_ms: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
