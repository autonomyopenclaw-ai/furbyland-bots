"""PIN-based (out-of-band) 3-legged OAuth 1.0a.

The user opens an authorize URL while signed in as the bot account, approves
the app, and pastes the PIN. The access token and secret are saved to a
gitignored file and printed as export lines. The consumer secret is not printed.

Run from this repo::

    python -m furbybots auth --account queen

After this package is copied elsewhere::

    python -m xapi.auth --account queen --expect QueenOfFurbies
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from urllib.parse import quote

from requests_oauthlib import OAuth1Session

from .client import XClient
from .config import account_prefix, load_local_env, require_app, token_file
from .errors import ConfigError, XApiError, redact

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

# Usernames this repository already posts as. Copied bots can pass --expect
# or add their own line here.
KNOWN_ACCOUNTS = {
    "queen": "QueenOfFurbies",
}

_TOKEN_VALUE_RE = re.compile(r"[A-Za-z0-9%\-_.]+")


def run_auth(
    *,
    account: str,
    expect: str | None = None,
    pin: str | None = None,
    input_fn=input,
) -> int:
    """Walk one account through the PIN flow. Returns a process status code."""
    try:
        account_name = account.strip().lower()
        prefix = account_prefix(account_name)
    except ConfigError as exc:
        print(exc)
        return 2

    if expect is None:
        expect = KNOWN_ACCOUNTS.get(account_name)
    elif expect.strip():
        expect = expect.strip().lstrip("@")
    else:
        expect = None

    load_local_env()
    try:
        app = require_app()
    except ConfigError as exc:
        print(exc)
        return 2

    secrets = [app.api_key, app.api_secret]
    session = OAuth1Session(app.api_key, client_secret=app.api_secret, callback_uri="oob")
    try:
        request_token = session.fetch_request_token(
            REQUEST_TOKEN_URL, timeout=30, allow_redirects=False
        )
    except Exception as exc:
        print(_failure("Could not start authorization.", exc, secrets))
        print(
            "Check that the app has OAuth 1.0a turned on, with Read and write "
            "permission. If the portal requires a callback URL, use http://127.0.0.1 "
            "and choose a native app so the PIN flow is allowed."
        )
        return 1

    oauth_token = str(request_token.get("oauth_token") or "")
    oauth_secret = str(request_token.get("oauth_token_secret") or "")
    secrets.extend([oauth_token, oauth_secret])
    confirmed = str(request_token.get("oauth_callback_confirmed", "true")).lower()
    if not oauth_token or not oauth_secret or confirmed == "false":
        print(
            "X did not return a PIN-based request token. In the developer portal, "
            "set the app to OAuth 1.0a / native, with Read and write permission."
        )
        return 1

    who = f"@{expect}" if expect else "the bot account"
    authorize = f"{AUTHORIZE_URL}?oauth_token={quote(oauth_token, safe='')}"
    print(f"Sign in to X in your browser as {who}.")
    print("Open this URL, approve the app, and copy the PIN:\n")
    print(authorize)
    print()
    if pin is None:
        try:
            pin = input_fn("Paste the PIN here: ")
        except EOFError:
            print("No PIN was entered.")
            return 2
    pin = pin.strip()
    if not pin:
        print("No PIN was entered.")
        return 2

    exchange = OAuth1Session(
        app.api_key,
        client_secret=app.api_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_secret,
        verifier=pin,
    )
    try:
        access = exchange.fetch_access_token(
            ACCESS_TOKEN_URL, timeout=30, allow_redirects=False
        )
    except Exception as exc:
        print(_failure("Could not exchange the PIN.", exc, secrets))
        print("The PIN may be wrong or already used. Run the command again and open the new URL.")
        return 1

    access_token = str(access.get("oauth_token") or "")
    access_secret = str(access.get("oauth_token_secret") or "")
    secrets.extend([access_token, access_secret])
    if not access_token or not access_secret:
        print("X did not return an access token. Run the command again.")
        return 1

    client = XClient(app.api_key, app.api_secret, access_token, access_secret)
    try:
        me = client.get_me()
    except XApiError as exc:
        print(exc)
        print("The account could not be confirmed, so the token was not saved.")
        return 1

    print(f"Signed in as @{me.username} (id {me.id}).")
    if expect and me.username.lower() != expect.lower():
        print(f"Expected @{expect}. Tokens were not saved.")
        print(
            f"@{me.username} approved the app. Sign out, sign in as @{expect}, "
            "and run this command again."
        )
        return 2

    path = token_file(account_name)
    lines = [
        f"{prefix}_ACCESS_TOKEN={_env_value(access_token)}",
        f"{prefix}_ACCESS_TOKEN_SECRET={_env_value(access_secret)}",
    ]
    print("Export lines (the app consumer secret is not included):")
    print(f"export {prefix}_ACCESS_TOKEN={shlex.quote(access_token)}")
    print(f"export {prefix}_ACCESS_TOKEN_SECRET={shlex.quote(access_secret)}")
    try:
        _write_token_file(path, prefix, lines)
    except OSError as exc:
        print(f"Could not save {path}: {exc.strerror or exc}")
        print("Copy the export lines above into your environment.")
        return 1
    print(f"Saved {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m furbybots.xapi.auth",
        description="Authorize one bot account with the PIN-based X OAuth flow.",
    )
    parser.add_argument("--account", required=True, help="Short name, such as queen.")
    parser.add_argument(
        "--expect",
        help="Username GET /2/users/me must return. Defaults for known accounts.",
    )
    parser.add_argument("--pin", help="PIN from the authorize page. If omitted, you are prompted.")
    args = parser.parse_args(argv)
    return run_auth(account=args.account, expect=args.expect, pin=args.pin)


def _write_token_file(path, prefix: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    body = (
        f"# Access token for the {prefix.lower()} account.\n"
        "# Gitignored. Do not commit.\n"
        + "\n".join(lines)
        + "\n"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, body.encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def _env_value(value: str) -> str:
    if _TOKEN_VALUE_RE.fullmatch(value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _failure(summary: str, exc: Exception, secrets: list[str]) -> str:
    message = redact(str(exc), secrets).replace("\n", " ")
    if len(message) > 300:
        message = message[:300] + "..."
    return f"{summary} {exc.__class__.__name__}: {message}"


if __name__ == "__main__":
    sys.exit(main())
