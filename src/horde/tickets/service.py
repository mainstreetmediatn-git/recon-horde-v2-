"""Deduplicated internal maintenance tickets."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from horde.core.models import utcnow


@dataclass
class Ticket:
    title: str
    fingerprint: str
    kind: str = "maintenance"
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utcnow)
    resolved_at: datetime | None = None


class TicketService:
    def __init__(self) -> None:
        self._tickets: dict[str, Ticket] = {}

    def create_if_missing(self, ticket: Ticket) -> Ticket:
        existing = self._tickets.get(ticket.fingerprint)
        if existing and existing.resolved_at is None:
            return existing
        self._tickets[ticket.fingerprint] = ticket
        return ticket

    def resolve(self, fingerprint: str) -> None:
        if fingerprint in self._tickets:
            self._tickets[fingerprint].resolved_at = utcnow()

    def unresolved(self) -> list[Ticket]:
        return [ticket for ticket in self._tickets.values() if ticket.resolved_at is None]
