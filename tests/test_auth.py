"""PIN auth saves the account token and keeps the consumer secret off the screen."""

import re

import responses

from furbybots.cli import main
from furbybots.xapi.errors import redact

REQUEST = re.compile(r"https://api\.twitter\.com/oauth/request_token")
ACCESS = re.compile(r"https://api\.twitter\.com/oauth/access_token")
USERS_ME = re.compile(r"https://api\.twitter\.com/2/users/me")
CONSUMER_SECRET = "super-secret-consumer"


def _oauth(body: str) -> dict:
    return {
        "body": body,
        "status": 200,
        "content_type": "application/x-www-form-urlencoded",
    }


@responses.activate
def test_auth_saves_queen_and_hides_the_consumer_secret(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("X_API_KEY", "app-key")
    monkeypatch.setenv("X_API_SECRET", CONSUMER_SECRET)
    responses.add(
        responses.POST,
        REQUEST,
        **_oauth(
            "oauth_token=req-token&oauth_token_secret=req-secret"
            "&oauth_callback_confirmed=true"
        ),
    )
    responses.add(
        responses.POST,
        ACCESS,
        **_oauth(
            "oauth_token=user-token&oauth_token_secret=user-secret"
            "&user_id=42&screen_name=QueenOfFurbies"
        ),
    )
    responses.add(
        responses.GET,
        USERS_ME,
        json={"data": {"id": "42", "name": "Queen of Furbies", "username": "QueenOfFurbies"}},
        status=200,
    )

    code = main(["auth", "--account", "queen", "--pin", "1234567"])
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert code == 0
    assert "https://api.twitter.com/oauth/authorize?oauth_token=req-token" in output
    assert "Signed in as @QueenOfFurbies" in output
    assert "req-secret" not in output
    assert CONSUMER_SECRET not in output
    saved_path = tmp_path / "tokens" / "queen.env"
    saved = saved_path.read_text(encoding="utf-8")
    assert "QUEEN_ACCESS_TOKEN=user-token" in saved
    assert "QUEEN_ACCESS_TOKEN_SECRET=user-secret" in saved
    assert CONSUMER_SECRET not in saved
    assert "X_API_SECRET" not in saved
    assert saved_path.stat().st_mode & 0o777 == 0o600
    assert "export QUEEN_ACCESS_TOKEN=" in output
    assert "user-secret" in output


@responses.activate
def test_auth_discards_a_token_for_the_wrong_account(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("X_API_KEY", "app-key")
    monkeypatch.setenv("X_API_SECRET", CONSUMER_SECRET)
    responses.add(
        responses.POST,
        REQUEST,
        **_oauth(
            "oauth_token=req-token&oauth_token_secret=req-secret"
            "&oauth_callback_confirmed=true"
        ),
    )
    responses.add(
        responses.POST,
        ACCESS,
        **_oauth(
            "oauth_token=user-token&oauth_token_secret=user-secret&user_id=7"
        ),
    )
    responses.add(
        responses.GET,
        USERS_ME,
        json={"data": {"id": "7", "name": "Nope", "username": "SomeoneElse"}},
        status=200,
    )
    code = main(["auth", "--account", "queen", "--pin", "1234567"])
    output = capsys.readouterr().out
    assert code == 2
    assert "SomeoneElse" in output
    assert "QueenOfFurbies" in output
    assert "not saved" in output
    assert "user-token" not in output
    assert "user-secret" not in output
    assert CONSUMER_SECRET not in output
    assert not (tmp_path / "tokens" / "queen.env").exists()


@responses.activate
def test_auth_failure_does_not_print_the_consumer_secret(monkeypatch, capsys):
    monkeypatch.setenv("X_API_KEY", "app-key")
    monkeypatch.setenv("X_API_SECRET", CONSUMER_SECRET)
    responses.add(
        responses.POST,
        REQUEST,
        body=f"invalid signature for {CONSUMER_SECRET}",
        status=401,
    )
    code = main(["auth", "--account", "queen"])
    output = capsys.readouterr().out + capsys.readouterr().err
    assert code == 1
    assert CONSUMER_SECRET not in output
    assert "[redacted]" in output or "Could not start authorization" in output


def test_redact_removes_a_secret_and_its_quoted_form():
    hidden = redact(
        "saw super-secret-consumer and oauth_token_secret=abc123",
        ["super-secret-consumer"],
    )
    assert "super-secret-consumer" not in hidden
    assert "abc123" not in hidden
