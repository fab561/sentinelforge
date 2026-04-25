"""_safe() coerces text into latin-1 so fpdf2 (default core fonts) doesn't
500 the case PDF export when an alert title contains an emoji or unicode."""

from app.services.pdf_service import _safe


def test_safe_passes_plain_ascii():
    assert _safe("hello world") == "hello world"


def test_safe_returns_empty_for_none():
    assert _safe(None) == ""


def test_safe_replaces_unsupported_glyphs():
    """Non-latin1 glyphs should be replaced (not raise) so the PDF renders."""
    out = _safe("emoji 🔥 alert — malicious")
    assert "?" in out  # replaced
    assert "alert" in out
    # The em-dash (—, U+2014) is also outside latin-1 → also replaced.


def test_safe_stringifies_non_strings():
    assert _safe(42) == "42"
    assert _safe(True) == "True"
