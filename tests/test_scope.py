from horde.scope.models import AuthorizedScope, ScopeKind
from horde.scope.policy import ScopeEngine


def test_domain_matches_subdomains_but_not_suffix_attacks():
    engine = ScopeEngine()
    scope = AuthorizedScope(kind=ScopeKind.DOMAIN, value="example.com")
    assert engine.check("https://api.example.com/v1", [scope]).allowed
    assert not engine.check("https://notexample.com", [scope]).allowed


def test_ip_and_cidr():
    engine = ScopeEngine()
    assert engine.check("192.0.2.10", [AuthorizedScope(kind=ScopeKind.CIDR, value="192.0.2.0/24")]).allowed
    assert not engine.check("192.0.3.10", [AuthorizedScope(kind=ScopeKind.CIDR, value="192.0.2.0/24")]).allowed
    assert engine.check("2001:db8::1", [AuthorizedScope(kind=ScopeKind.IP, value="2001:db8::1")]).allowed


def test_url_subtree_boundary_and_inactive_scope():
    engine = ScopeEngine()
    scope = AuthorizedScope(kind=ScopeKind.URL_SUBTREE, value="https://example.com/api")
    assert engine.check("https://example.com/api/v1", [scope]).allowed
    assert not engine.check("https://example.com/apix", [scope]).allowed
    scope.active = False
    assert not engine.check("https://example.com/api", [scope]).allowed


def test_malformed_target_denied():
    decision = ScopeEngine().check("http://", [])
    assert not decision.allowed
    assert decision.reason.startswith("malformed_target")
