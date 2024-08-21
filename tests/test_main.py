from solidation.__main__ import sanitize_md


def test_sanitize_md() -> None:
    assert sanitize_md(r"[gh-actions](deps): Fix \n") == r"\[gh-actions\](deps): Fix \\n"
