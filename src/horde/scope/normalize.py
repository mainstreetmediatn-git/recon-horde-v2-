"""Target normalization shared by every execution path."""

from dataclasses import dataclass
from ipaddress import ip_address
import posixpath
from urllib.parse import urlsplit


def _normalize_path(path: str) -> str:
    raw = path or "/"
    if not raw.startswith("/"):
        raw = f"/{raw}"
    trailing_slash = raw.endswith("/")
    normalized = posixpath.normpath(raw)
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if trailing_slash and normalized != "/" and not normalized.endswith("/"):
        normalized += "/"
    return normalized


@dataclass(frozen=True)
class NormalizedTarget:
    original: str
    host: str
    path: str
    scheme: str | None
    port: int | None
    ip: object | None
    canonical: str


def normalize_target(value: str) -> NormalizedTarget:
    raw = value.strip()
    if not raw or any(ord(char) < 32 for char in raw):
        raise ValueError("target is empty or contains control characters")

    # Bare IP literals are handled before URL parsing so IPv6 colons are never
    # mistaken for a host/port separator.
    try:
        bare_ip = ip_address(raw)
    except ValueError:
        bare_ip = None
    if bare_ip is not None:
        host = str(bare_ip)
        return NormalizedTarget(raw, host, "/", None, None, bare_ip, f"{host}/")

    candidate = raw if "://" in raw else f"//{raw}"
    try:
        parsed = urlsplit(candidate)
        parsed_port = parsed.port
    except ValueError as exc:
        raise ValueError("target has an invalid port") from exc
    if parsed.username is not None:
        raise ValueError("target contains userinfo")
    if not parsed.hostname:
        raise ValueError("target has no hostname")
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("target hostname is not a valid IDN") from exc
    try:
        parsed_ip = ip_address(host)
    except ValueError:
        parsed_ip = None

    scheme = parsed.scheme.lower() if parsed.scheme else None
    port = parsed_port
    if port is None and scheme == "http":
        port = 80
    elif port is None and scheme == "https":
        port = 443

    path = _normalize_path(parsed.path)
    display_host = f"[{host}]" if parsed_ip is not None and getattr(parsed_ip, "version", 4) == 6 and scheme else host
    port_part = ""
    if parsed_port is not None:
        port_part = f":{parsed_port}"
    canonical = f"{scheme + '://' if scheme else ''}{display_host}{port_part}{path}"
    return NormalizedTarget(raw, host, path, scheme, port, parsed_ip, canonical)
