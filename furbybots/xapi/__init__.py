"""Small X API helper: PIN-based OAuth 1.0a and user-context posts.

Copy this package into another repository when a second bot needs the same
app. It depends only on ``requests`` and ``requests-oauthlib``.

- ``X_API_KEY`` and ``X_API_SECRET`` are the app's consumer key and secret.
- Each account then gets ``<NAME>_ACCESS_TOKEN`` and
  ``<NAME>_ACCESS_TOKEN_SECRET`` from ``python -m xapi.auth``.
- ``XClient`` calls ``GET /2/users/me`` and ``POST /2/tweets``.
- ``create_tweet(..., in_reply_to=...)`` posts a reply. Reading replies is a
  separate endpoint and is not implemented here.

The consumer secret is never printed. This module does not import ``auth``,
so ``python -m xapi.auth`` can run the PIN flow on its own.
"""

from .client import XClient, XUser
from .errors import AccountMismatch, ConfigError, XApiError

__all__ = [
    "AccountMismatch",
    "ConfigError",
    "XApiError",
    "XClient",
    "XUser",
]
