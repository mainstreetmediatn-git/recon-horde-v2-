import pytest

from horde.scope.normalize import normalize_target


def test_userinfo_username_only_rejected():
    with pytest.raises(ValueError, match="userinfo"):
        normalize_target("https://user@example.com/")


def test_userinfo_username_password_rejected():
    with pytest.raises(ValueError, match="userinfo"):
        normalize_target("https://evil.example:pw@allowed.example/")


def test_valid_target_without_userinfo():
    result = normalize_target("https://example.com/path")
    assert result.host == "example.com"
    assert result.path == "/path"
    assert result.scheme == "https"
