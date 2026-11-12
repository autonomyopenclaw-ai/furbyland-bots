"""Publish one post as @QueenOfFurbies, after checking the token's account."""

from __future__ import annotations

from furbybots.queen.generate import generate_post
from furbybots.queen.history import PostHistory
from furbybots.queen.llm import writer_from_env
from furbybots.queen.voice import InvalidPost, validate_post
from furbybots.xapi.client import XClient
from furbybots.xapi.config import load_local_env, missing_names, require_account, require_app
from furbybots.xapi.errors import AccountMismatch, ConfigError, XApiError

EXPECTED_USERNAME = "QueenOfFurbies"
QUEEN_PREFIX = "QUEEN"
QUEEN_ENV = [
    "X_API_KEY",
    "X_API_SECRET",
    "QUEEN_ACCESS_TOKEN",
    "QUEEN_ACCESS_TOKEN_SECRET",
]


def queen_post(*, dry_run: bool) -> int:
    load_local_env("queen")
    gaps = missing_names(QUEEN_ENV)
    if gaps and len(gaps) != len(QUEEN_ENV):
        print(
            "Some credentials are missing: "
            + ", ".join(gaps)
            + ". Fill them in .env or tokens/queen.env before posting."
        )
        return 2
    if gaps and not dry_run:
        print(
            "Set X_API_KEY, X_API_SECRET, QUEEN_ACCESS_TOKEN, and "
            "QUEEN_ACCESS_TOKEN_SECRET. Run: python -m furbybots auth --account queen"
        )
        return 2

    me = None
    client = None
    if not gaps:
        try:
            app = require_app()
            account = require_account(QUEEN_PREFIX)
            client = XClient(
                app.api_key,
                app.api_secret,
                account.access_token,
                account.access_token_secret,
            )
            me = client.require_user(EXPECTED_USERNAME)
        except AccountMismatch as exc:
            print(exc)
            return 2
        except ConfigError as exc:
            print(exc)
            return 2
        except XApiError as exc:
            print(exc)
            return 1

    try:
        history = PostHistory()
        post = generate_post(history, writer=writer_from_env())
        validate_post(post.text)
    except (ConfigError, InvalidPost, RuntimeError, OSError) as exc:
        print(exc)
        return 1

    if dry_run:
        if me is not None:
            print(f"Verified @{me.username}.")
        else:
            print("Tokens are not set, so the account was not checked.")
        print("Dry run. This would be posted:")
        print()
        print(post.text)
        print()
        print("No write request was sent. This line was not marked as used.")
        return 0

    if client is None or me is None:
        print(
            "Set X_API_KEY, X_API_SECRET, QUEEN_ACCESS_TOKEN, and "
            "QUEEN_ACCESS_TOKEN_SECRET. Run: python -m furbybots auth --account queen"
        )
        return 2
    try:
        tweet_id = client.create_tweet(post.text)
    except XApiError as exc:
        print(exc)
        return 1
    history.add(post.text, post.format_name, tweet_id)
    print(f"Posted https://x.com/{me.username}/status/{tweet_id}")
    print()
    print(post.text)
    return 0
