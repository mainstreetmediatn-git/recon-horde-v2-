"""Structured logging with conservative secret redaction."""

import logging
import re


_BEARER_RE = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)(SUPABASE_SERVICE_ROLE_KEY|service_role)(\s*[:=]\s*)([^\s,;]+)"
)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        message = _BEARER_RE.sub("Bearer [REDACTED]", message)
        message = _KEY_VALUE_SECRET_RE.sub(r"\1\2[REDACTED]", message)
        return message


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[handler], force=True)
