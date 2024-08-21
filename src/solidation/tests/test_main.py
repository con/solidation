from ..__main__ import sanitize_md


def test_sanitize_md() -> None:
    assert sanitize_md("[gh-actions](deps): Bump") == "gh-actions(deps): Bump"
