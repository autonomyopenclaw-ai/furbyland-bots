"""Load app and account credentials from the environment.

A ``.env`` file and ``tokens/<account>.env`` are read only to fill variables
that are not already set. The process environment always wins, which is how
GitHub Actions secrets are honored. Nothing in this module has a default key.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError

PLACEHOLDERS = {
    "your_api_key_here",
    "your_api_secret_here",
    "your_queen_access_token_here",
    "your_queen_access_token_secret_here",
    "your_xai_api_key_here",
    "your_openai_api_key_here",
}

_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ACCOUNT_RE = re.compile(r"[a-z][a-z0-9_]{0,30}")


@dataclass(frozen=True)
class AppCredentials:
    api_key: str
    api_secret: str


@dataclass(frozen=True)
class AccountCredentials:
    prefix: str
    access_token: str
    access_token_secret: str


def account_prefix(name: str) -> str:
    """Turn ``queen`` into the env prefix ``QUEEN``."""
    cleaned = name.strip().lower()
    if not _ACCOUNT_RE.fullmatch(cleaned):
        raise ConfigError(
            "Account name must be letters, digits, and underscores, "
            "and must start with a letter. Example: queen"
        )
    return cleaned.upper()


def load_local_env(account: str | None = None) -> None:
    """Fill unset variables from ``.env`` and, optionally, a token file."""
    if os.environ.get("FURBYBOTS_SKIP_DOTENV") == "1":
        return
    _load_file(Path(".env"))
    if account:
        _load_file(token_file(account))


def token_file(account: str) -> Path:
    root = Path(os.environ.get("FURBYBOTS_TOKEN_DIR", "tokens"))
    return root / f"{account.strip().lower()}.env"


def require_app() -> AppCredentials:
    key = _value("X_API_KEY")
    secret = _value("X_API_SECRET")
    if not key or not secret:
        raise ConfigError(
            "Set X_API_KEY and X_API_SECRET in the environment or in .env. "
            "Copy .env.example to .env and paste the app's consumer key and "
            "secret from the X developer portal."
        )
    return AppCredentials(api_key=key, api_secret=secret)


def require_account(prefix: str) -> AccountCredentials:
    token = _value(f"{prefix}_ACCESS_TOKEN")
    secret = _value(f"{prefix}_ACCESS_TOKEN_SECRET")
    if not token or not secret:
        raise ConfigError(
            f"Set {prefix}_ACCESS_TOKEN and {prefix}_ACCESS_TOKEN_SECRET. "
            f"Run: python -m furbybots auth --account {prefix.lower()}"
        )
    return AccountCredentials(
        prefix=prefix,
        access_token=token,
        access_token_secret=secret,
    )


def missing_names(names: list[str]) -> list[str]:
    return [name for name in names if not _value(name)]


def _value(name: str) -> str:
    raw = os.environ.get(name, "").strip()
    if raw in PLACEHOLDERS:
        return ""
    return raw


def _load_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if key not in os.environ and value and value not in PLACEHOLDERS:
            os.environ[key] = value


def _parse_line(line: str) -> tuple[str, str] | None:
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith("export "):
        text = text[len("export ") :].strip()
    if "=" not in text:
        return None
    key, value = text.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not _KEY_RE.fullmatch(key):
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value
