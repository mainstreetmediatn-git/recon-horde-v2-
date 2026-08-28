"""Normalized, serializable reconnaissance observations."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from horde.core.models import FindingSeverity, utcnow


class Observation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    target: str
    observed_at: datetime = Field(default_factory=utcnow)
    fingerprint: str
    raw: dict[str, Any] | None = None


class Asset(Observation):
    hostname: str
    addresses: list[str] = Field(default_factory=list)


class Endpoint(Observation):
    url: str
    status_code: int | None = None


class DnsRecord(Observation):
    record_type: str
    value: str


class PortObservation(Observation):
    port: int
    protocol: str = "tcp"
    state: str


class HttpObservation(Observation):
    url: str
    status_code: int
    final_url: str
    headers: dict[str, str] = Field(default_factory=dict)
    title: str | None = None
    response_bytes: int = 0


class TlsObservation(Observation):
    host: str
    port: int = 443
    subject: str | None = None
    issuer: str | None = None
    sans: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    protocol: str | None = None


class Finding(BaseModel):
    fingerprint: str
    title: str
    severity: FindingSeverity = FindingSeverity.INFO
    description: str
    evidence_ids: list[UUID] = Field(default_factory=list)


def stable_fingerprint(kind: str, *parts: object) -> str:
    import hashlib

    payload = "|".join([kind, *(str(part).strip().lower() for part in parts)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
