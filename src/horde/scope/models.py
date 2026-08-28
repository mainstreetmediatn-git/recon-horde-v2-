"""Authorization scope primitives."""

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ScopeKind(StrEnum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP = "ip"
    CIDR = "cidr"
    URL = "url"
    URL_SUBTREE = "url_subtree"


class AuthorizedScope(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    kind: ScopeKind
    value: str
    active: bool = True
    label: str | None = None


class ScopeDecision(BaseModel):
    allowed: bool
    matched_scope_id: UUID | None = None
    reason: str
    normalized_target: str | None = None
