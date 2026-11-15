"""Open an X client only when the token belongs to @QueenOfFurbies."""

from __future__ import annotations

from furbybots.xapi.client import XClient, XUser
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
MISSING_CREDENTIALS = (
    "Set X_API_KEY, X_API_SECRET, QUEEN_ACCESS_TOKEN, and "
    "QUEEN_ACCESS_TOKEN_SECRET. Run: python -m furbybots auth --account queen"
)


def open_queen(
    *,
    dry_run: bool,
    allow_missing: bool,
    missing_message: str | None = None,
) -> tuple[XClient | None, XUser | None, int | None]:
    """Return ``(client, user, exit_code)``.

    ``exit_code`` is set when the command should stop. A dry run may continue
    with no client when ``allow_missing`` is true and no credentials are set.
    """
    load_local_env("queen")
    gaps = missing_names(QUEEN_ENV)
    if gaps and len(gaps) != len(QUEEN_ENV):
        print(
            "Some credentials are missing: "
            + ", ".join(gaps)
            + ". Fill them in .env or tokens/queen.env before posting."
        )
        return None, None, 2
    if gaps:
        if allow_missing and dry_run:
            return None, None, None
        print(missing_message or MISSING_CREDENTIALS)
        return None, None, 2
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
        return None, None, 2
    except ConfigError as exc:
        print(exc)
        return None, None, 2
    except XApiError as exc:
        print(exc)
        return None, None, 1
    return client, me, None
