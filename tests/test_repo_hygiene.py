"""Repository files that must not leak secrets or post on their own."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_covers_secrets_and_token_files():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in text.splitlines()}
    assert ".env" in lines
    assert "tokens/" in lines
    assert "data/" in lines
    assert "!.env.example" in lines


def test_env_example_has_placeholders_only():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "X_API_KEY=your_api_key_here" in text
    assert "X_API_SECRET=your_api_secret_here" in text
    assert "QUEEN_ACCESS_TOKEN=your_queen_access_token_here" in text
    assert "QUEEN_ACCESS_TOKEN_SECRET=your_queen_access_token_secret_here" in text
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        _, _, value = stripped.partition("=")
        assert value.startswith("your_"), line


def test_schedule_is_commented_out():
    text = (ROOT / ".github" / "workflows" / "queen-daily.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "QUEEN_ACCESS_TOKEN" in text
    _assert_no_active_schedule(text)


def test_hashtag_workflow_is_a_manual_dry_run():
    text = (ROOT / ".github" / "workflows" / "queen-hashtag-dry-run.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "X_API_KEY" in text
    assert "X_API_SECRET" in text
    assert "QUEEN_ACCESS_TOKEN" in text
    assert "QUEEN_ACCESS_TOKEN_SECRET" in text
    assert "XAI_API_KEY" in text
    assert "OPENAI_API_KEY" in text
    assert 'default: "3"' in text
    _assert_no_active_schedule(text)
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "queen post" not in stripped
        if "hashtag-replies" in stripped:
            assert "--dry-run" in stripped


def _assert_no_active_schedule(text: str) -> None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert not stripped.startswith("schedule:")
        assert "cron:" not in stripped
