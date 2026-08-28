"""Deterministic, deny-by-default authorization policy."""

from ipaddress import ip_address, ip_network

from .models import AuthorizedScope, ScopeDecision, ScopeKind
from .normalize import NormalizedTarget, normalize_target


class ScopeEngine:
    def check(self, target: str, scopes: list[AuthorizedScope]) -> ScopeDecision:
        try:
            normalized = normalize_target(target)
        except ValueError as exc:
            return ScopeDecision(allowed=False, reason=f"malformed_target:{exc}")
        for scope in scopes:
            if scope.active and self._matches(normalized, scope):
                return ScopeDecision(
                    allowed=True,
                    matched_scope_id=scope.id,
                    reason=f"matched_{scope.kind.value}_scope",
                    normalized_target=normalized.canonical,
                )
        return ScopeDecision(
            allowed=False,
            reason="no_active_scope_match",
            normalized_target=normalized.canonical,
        )

    def _matches(self, target: NormalizedTarget, scope: AuthorizedScope) -> bool:
        value = scope.value.strip()
        if scope.kind in (ScopeKind.IP, ScopeKind.CIDR):
            try:
                if scope.kind is ScopeKind.IP:
                    return target.ip is not None and target.ip == ip_address(value)
                return target.ip is not None and target.ip in ip_network(value, strict=False)
            except ValueError:
                return False

        if scope.kind in (ScopeKind.DOMAIN, ScopeKind.SUBDOMAIN):
            try:
                domain = value.rstrip(".").encode("idna").decode("ascii").lower()
            except UnicodeError:
                return False
            return target.host == domain or target.host.endswith(f".{domain}")

        if scope.kind not in (ScopeKind.URL, ScopeKind.URL_SUBTREE):
            return False

        try:
            scope_target = normalize_target(value if "://" in value else f"https://{value}")
        except ValueError:
            return False

        # URL authorization is endpoint-specific: scheme, effective port, host,
        # and normalized path all participate in the decision.
        if (
            target.scheme != scope_target.scheme
            or target.port != scope_target.port
            or target.host != scope_target.host
        ):
            return False

        if scope.kind is ScopeKind.URL:
            return target.path == scope_target.path

        root = scope_target.path.rstrip("/") or "/"
        if root == "/":
            return target.path.startswith("/")
        return target.path == root or target.path.startswith(root + "/")
