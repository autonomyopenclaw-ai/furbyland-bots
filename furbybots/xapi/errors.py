"""Errors for the copyable X helper. Messages never include secrets."""

from __future__ import annotations

import re
from urllib.parse import quote


class ConfigError(Exception):
    """A required environment variable is missing or still a placeholder."""


class XApiError(Exception):
    """X returned an error, or the response could not be used."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class AccountMismatch(Exception):
    """The access token belongs to a different account than the one required."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected.lstrip("@")
        self.actual = actual.lstrip("@")
        super().__init__(
            f"Refusing to post: token belongs to @{self.actual}, "
            f"expected @{self.expected}."
        )


def redact(text: str, secrets: list[str]) -> str:
    """Remove credential material from a string before it is shown."""
    redacted = text
    for secret in secrets:
        if not secret or len(secret) < 6:
            continue
        redacted = redacted.replace(secret, "[redacted]")
        encoded = quote(secret, safe="")
        if encoded and encoded != secret:
            redacted = redacted.replace(encoded, "[redacted]")
    redacted = re.sub(
        r"(oauth_token_secret|oauth_consumer_secret|api_secret)=[^&\s\"']+",
        r"\1=[redacted]",
        redacted,
    )
    return redacted
