"""IOC value normalisation rules — case folding for ip/domain/hash, leave URL alone."""

from app.services.ioc_service import _normalise


def test_ip_lowercases_and_strips():
    assert _normalise("  1.2.3.4 ", "ip") == "1.2.3.4"


def test_domain_lowercases():
    assert _normalise("EVIL.example.COM", "domain") == "evil.example.com"


def test_hash_lowercases():
    assert _normalise("D41D8CD98F00B204", "hash") == "d41d8cd98f00b204"


def test_url_preserves_case():
    """URL query strings can be case-sensitive — don't fold."""
    raw = "https://Evil.com/Path?Token=Abc"
    assert _normalise(raw, "url") == raw


def test_url_strips_whitespace_only():
    assert _normalise("  https://Evil.com  ", "url") == "https://Evil.com"
