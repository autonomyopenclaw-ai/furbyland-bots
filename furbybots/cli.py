"""Command line for the Queen of Furbies poster and the shared auth helper."""

from __future__ import annotations

import argparse

from furbybots.queen.poster import queen_post
from furbybots.queen.replies import queen_hashtag_replies
from furbybots.xapi.auth import KNOWN_ACCOUNTS, run_auth


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="furbybots",
        description="Post as @QueenOfFurbies with the official X API.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    auth = sub.add_parser(
        "auth",
        help="Authorize a bot account with a PIN and save its access token.",
    )
    auth.add_argument("--account", required=True, help="Short name, such as queen.")
    auth.add_argument(
        "--expect",
        help=(
            "Username that GET /2/users/me must return. "
            "For queen, the default is QueenOfFurbies."
        ),
    )
    auth.add_argument(
        "--pin",
        help="PIN from the authorize page. If omitted, you are prompted.",
    )

    queen = sub.add_parser("queen", help="Commands for @QueenOfFurbies.")
    queen_sub = queen.add_subparsers(dest="action", required=True)
    post = queen_sub.add_parser("post", help="Publish today's post.")
    post.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the post. Do not call the write endpoint.",
    )
    hashtags = queen_sub.add_parser(
        "hashtag-replies",
        help="Reply to a few recent posts tagged #furby or #furbyland.",
    )
    hashtags.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the candidates and drafted replies. Do not post them.",
    )
    hashtags.add_argument(
        "--limit",
        type=int,
        default=None,
        help="How many replies to send this run (1-10, default 3).",
    )

    args = parser.parse_args(argv)
    if args.command == "auth":
        expect = args.expect
        if expect is None:
            expect = KNOWN_ACCOUNTS.get(args.account.strip().lower())
        return run_auth(account=args.account, expect=expect, pin=args.pin)
    if args.command == "queen" and args.action == "post":
        return queen_post(dry_run=args.dry_run)
    if args.command == "queen" and args.action == "hashtag-replies":
        return queen_hashtag_replies(dry_run=args.dry_run, limit=args.limit)
    parser.error("Unknown command")
    return 2
