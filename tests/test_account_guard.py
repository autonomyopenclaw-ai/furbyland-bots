"""The poster checks GET /2/users/me and will not write for the wrong account."""

import json
import re

import responses

from furbybots.cli import main
from furbybots.queen.voice import validate_post
from furbybots.xapi.client import XClient

XAI = "https://api.x.ai/v1/chat/completions"
MODEL_POST = (
    "Royal Decree: Furbyland grants an extra pillow at Pillow Palace. "
    "The Crown signs it with a yawn. 👑"
)

USERS_ME = re.compile(r"https://api\.twitter\.com/2/users/me")
TWEETS = re.compile(r"https://api\.twitter\.com/2/tweets$")
QUEEN = {"data": {"id": "42", "name": "Queen of Furbies", "username": "QueenOfFurbies"}}
OTHER = {"data": {"id": "9", "name": "Someone", "username": "NotTheQueen"}}


@responses.activate
def test_wrong_account_is_refused_and_not_written(queen_env, capsys):
    responses.add(responses.GET, USERS_ME, json=OTHER, status=200)
    code = main(["queen", "post"])
    assert code == 2
    assert [call.request.method for call in responses.calls] == ["GET"]
    message = capsys.readouterr().out
    assert "NotTheQueen" in message
    assert "QueenOfFurbies" in message
    assert "Refusing to post" in message


@responses.activate
def test_dry_run_also_refuses_the_wrong_account(queen_env, capsys):
    responses.add(responses.GET, USERS_ME, json=OTHER, status=200)
    code = main(["queen", "post", "--dry-run"])
    assert code == 2
    assert [call.request.method for call in responses.calls] == ["GET"]
    assert "Dry run" not in capsys.readouterr().out


@responses.activate
def test_matching_account_posts_a_valid_line(queen_env, capsys, tmp_path):
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    responses.add(
        responses.POST,
        TWEETS,
        json={"data": {"id": "555", "text": "posted"}},
        status=201,
    )
    code = main(["queen", "post"])
    assert code == 0
    methods = [call.request.method for call in responses.calls]
    assert methods == ["GET", "POST"]
    body = json.loads(responses.calls[1].request.body)
    validate_post(body["text"])
    assert body["text"].endswith("👑")
    assert "@" not in body["text"]
    assert len(body["text"]) <= 280
    assert "reply" not in body
    message = capsys.readouterr().out
    assert "https://x.com/QueenOfFurbies/status/555" in message
    assert body["text"] in message
    saved = json.loads((tmp_path / "queen_posted.json").read_text(encoding="utf-8"))
    assert saved["posts"][0]["text"] == body["text"]
    assert saved["posts"][0]["tweet_id"] == "555"


@responses.activate
def test_dry_run_verifies_and_does_not_write(queen_env, capsys, tmp_path):
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    code = main(["queen", "post", "--dry-run"])
    assert code == 0
    assert [call.request.method for call in responses.calls] == ["GET"]
    message = capsys.readouterr().out
    assert "Verified @QueenOfFurbies." in message
    assert "Dry run" in message
    assert "👑" in message
    assert "No write request was sent" in message
    assert not (tmp_path / "queen_posted.json").exists()


def test_dry_run_without_tokens_makes_no_requests(capsys, tmp_path):
    with responses.RequestsMock() as mocked:
        code = main(["queen", "post", "--dry-run"])
    assert code == 0
    assert len(mocked.calls) == 0
    message = capsys.readouterr().out
    assert "Tokens are not set" in message
    assert "👑" in message
    assert not (tmp_path / "queen_posted.json").exists()


def test_placeholders_do_not_count_as_credentials(monkeypatch, capsys):
    monkeypatch.setenv("X_API_KEY", "your_api_key_here")
    monkeypatch.setenv("X_API_SECRET", "your_api_secret_here")
    monkeypatch.setenv("QUEEN_ACCESS_TOKEN", "your_queen_access_token_here")
    monkeypatch.setenv(
        "QUEEN_ACCESS_TOKEN_SECRET", "your_queen_access_token_secret_here"
    )
    with responses.RequestsMock() as mocked:
        code = main(["queen", "post", "--dry-run"])
    assert code == 0
    assert len(mocked.calls) == 0
    assert "👑" in capsys.readouterr().out


def test_partial_credentials_stop_before_any_request(monkeypatch, capsys):
    monkeypatch.setenv("X_API_KEY", "only-the-key")
    with responses.RequestsMock() as mocked:
        code = main(["queen", "post", "--dry-run"])
    assert code == 2
    assert len(mocked.calls) == 0
    assert "X_API_SECRET" in capsys.readouterr().out


@responses.activate
def test_rejected_credentials_do_not_write(queen_env, capsys, tmp_path):
    responses.add(
        responses.GET,
        USERS_ME,
        json={"title": "Unauthorized", "status": 401, "detail": "bad token"},
        status=401,
    )
    code = main(["queen", "post"])
    assert code == 1
    assert [call.request.method for call in responses.calls] == ["GET"]
    message = capsys.readouterr().out
    assert "rejected these credentials" in message
    assert "test-api-secret" not in message
    assert "test-access-secret" not in message
    assert not (tmp_path / "queen_posted.json").exists()


@responses.activate
def test_rate_limit_does_not_record_a_post(queen_env, capsys, tmp_path):
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    responses.add(
        responses.POST,
        TWEETS,
        json={"detail": "Too Many Requests"},
        status=429,
        headers={"x-rate-limit-reset": "1700000000"},
    )
    code = main(["queen", "post"])
    assert code == 1
    message = capsys.readouterr().out
    assert "rate limited" in message
    assert "1700000000" in message
    assert not (tmp_path / "queen_posted.json").exists()


@responses.activate
def test_forbidden_explains_read_and_write(queen_env, capsys):
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    responses.add(
        responses.POST,
        TWEETS,
        json={"detail": "Forbidden"},
        status=403,
    )
    code = main(["queen", "post"])
    assert code == 1
    message = capsys.readouterr().out
    assert "Read and write" in message
    assert "test-api-secret" not in message


@responses.activate
def test_create_tweet_can_reply_for_a_copied_bot():
    responses.add(
        responses.POST,
        TWEETS,
        json={"data": {"id": "9"}},
        status=201,
    )
    client = XClient("key", "secret", "token", "token-secret")
    tweet_id = client.create_tweet("next chapter", in_reply_to="42")
    assert tweet_id == "9"
    body = json.loads(responses.calls[0].request.body)
    assert body == {
        "text": "next chapter",
        "reply": {"in_reply_to_tweet_id": "42"},
    }


@responses.activate
def test_second_post_does_not_repeat(queen_env, tmp_path):
    for tweet_id in ("1", "2"):
        responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
        responses.add(
            responses.POST,
            TWEETS,
            json={"data": {"id": tweet_id}},
            status=201,
        )
    assert main(["queen", "post"]) == 0
    assert main(["queen", "post"]) == 0
    posted = [
        json.loads(call.request.body)["text"]
        for call in responses.calls
        if call.request.method == "POST"
    ]
    assert posted[0] != posted[1]
    for text in posted:
        validate_post(text)
        assert text.endswith("👑")
        assert "@" not in text
    saved = json.loads((tmp_path / "queen_posted.json").read_text(encoding="utf-8"))
    assert [item["text"] for item in saved["posts"]] == posted


@responses.activate
def test_llm_text_is_posted_when_the_provider_returns_it(queen_env, monkeypatch, capsys):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key")
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    responses.add(
        responses.POST,
        XAI,
        json={"choices": [{"message": {"content": MODEL_POST}}]},
        status=200,
    )
    responses.add(
        responses.POST,
        TWEETS,
        json={"data": {"id": "77"}},
        status=201,
    )
    code = main(["queen", "post"])
    output = capsys.readouterr()
    assert code == 0
    posted = json.loads(responses.calls[-1].request.body)
    assert posted["text"] == MODEL_POST
    assert "xai-test-key" not in output.out
    assert "xai-test-key" not in output.err
    assert any(call.request.url.startswith(XAI) for call in responses.calls)


@responses.activate
def test_llm_failure_falls_back_to_a_local_post(queen_env, monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    responses.add(responses.GET, USERS_ME, json=QUEEN, status=200)
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={"error": "unavailable"},
        status=503,
    )
    responses.add(
        responses.POST,
        TWEETS,
        json={"data": {"id": "88"}},
        status=201,
    )
    code = main(["queen", "post"])
    output = capsys.readouterr()
    assert code == 0
    posted = json.loads(responses.calls[-1].request.body)["text"]
    validate_post(posted)
    assert posted.endswith("👑")
    assert "@" not in posted
    assert "openai-test-key" not in output.out
    assert "openai-test-key" not in output.err
    assert "local post" in output.err
