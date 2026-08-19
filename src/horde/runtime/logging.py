"""Structured logging with conservative secret redaction."""

import logging


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for secret in ("service_role", "SUPABASE_SERVICE_ROLE_KEY", "Bearer "):
            message = message.replace(secret, "[REDACTED]")
        return message


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler], force=True)
