"""Publish one post as @QueenOfFurbies, after checking the token's account."""

from __future__ import annotations

from furbybots.queen.access import MISSING_CREDENTIALS, open_queen
from furbybots.queen.generate import generate_post
from furbybots.queen.history import PostHistory
from furbybots.queen.llm import writer_from_env
from furbybots.queen.voice import InvalidPost, validate_post
from furbybots.xapi.errors import ConfigError, XApiError


def queen_post(*, dry_run: bool) -> int:
    client, me, code = open_queen(dry_run=dry_run, allow_missing=True)
    if code is not None:
        return code

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
        print(MISSING_CREDENTIALS)
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
