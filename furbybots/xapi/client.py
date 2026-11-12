"""User-context client for X API v2.

Endpoints used here are ``GET /2/users/me`` and ``POST /2/tweets``.
``create_tweet`` accepts ``in_reply_to`` so a copied bot can continue a thread.
Reading replies (recent search) is intentionally not included.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests
from requests_oauthlib import OAuth1

from .errors import AccountMismatch, XApiError, redact

API_BASE = "https://api.twitter.com/2"
USER_AGENT = "furbybots-xapi/0.1"
DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class XUser:
    id: str
    name: str
    username: str


class XClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        *,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._secrets = [api_key, api_secret, access_token, access_token_secret]
        self._timeout = timeout
        self.session = session or requests.Session()
        self.session.auth = OAuth1(
            api_key,
            client_secret=api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        self.session.headers.setdefault("User-Agent", USER_AGENT)

    def get_me(self) -> XUser:
        payload = self._request(
            "GET",
            f"{API_BASE}/users/me",
            params={"user.fields": "id,name,username"},
        )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise XApiError(200, "GET /2/users/me did not return a user.")
        username = str(data.get("username") or "").lstrip("@")
        user_id = str(data.get("id") or "")
        if not username or not user_id:
            raise XApiError(200, "GET /2/users/me did not return a username.")
        return XUser(id=user_id, name=str(data.get("name") or ""), username=username)

    def require_user(self, expected_username: str) -> XUser:
        """Return the signed-in user, or refuse when the username differs."""
        expected = expected_username.lstrip("@")
        me = self.get_me()
        if me.username.lower() != expected.lower():
            raise AccountMismatch(expected, me.username)
        return me

    def create_tweet(self, text: str, *, in_reply_to: str | None = None) -> str:
        """Publish ``text``. Pass ``in_reply_to`` to reply to a post id."""
        body: dict[str, object] = {"text": text}
        if in_reply_to:
            body["reply"] = {"in_reply_to_tweet_id": str(in_reply_to)}
        payload = self._request("POST", f"{API_BASE}/tweets", json=body)
        data = payload.get("data")
        if not isinstance(data, dict) or not data.get("id"):
            raise XApiError(200, "POST /2/tweets did not return a post id.")
        return str(data["id"])

    def _request(self, method: str, url: str, **kwargs: object) -> dict:
        try:
            response = self.session.request(
                method,
                url,
                timeout=self._timeout,
                allow_redirects=False,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise XApiError(0, f"Could not reach X ({exc.__class__.__name__}).") from exc
        if 300 <= response.status_code < 400:
            raise XApiError(
                response.status_code,
                "X redirected this request instead of answering it.",
            )
        if response.status_code >= 400:
            raise self._http_error(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise XApiError(
                response.status_code,
                "X returned a response that was not JSON." + _detail(response, self._secrets),
            ) from exc
        if not isinstance(payload, dict):
            raise XApiError(response.status_code, "X returned an unexpected response.")
        return payload

    def _http_error(self, response: requests.Response) -> XApiError:
        detail = _detail(response, self._secrets)
        status = response.status_code
        if status == 429:
            reset = response.headers.get("x-rate-limit-reset", "")
            wait = (
                f" The limit resets at unix time {reset}."
                if reset
                else " Wait and try again later."
            )
            return XApiError(429, "X rate limited this request." + wait + detail)
        if status == 401:
            return XApiError(
                401,
                "X rejected these credentials. Check X_API_KEY, X_API_SECRET, "
                "and this account's access token. Run the auth helper again if "
                "the token is old." + detail,
            )
        if status == 403:
            return XApiError(
                403,
                "X refused this request. Confirm the app permission is Read and "
                "write, then run the auth helper again so this account issues a "
                "new token. Changing the permission does not update old tokens."
                + detail,
            )
        return XApiError(status, f"X returned HTTP {status}." + detail)


def _detail(response: requests.Response, secrets: list[str]) -> str:
    text = (response.text or "").replace("\n", " ").strip()
    text = redact(text, secrets)
    if len(text) > 240:
        text = text[:240] + "..."
    if not text:
        return ""
    return f" X said: {text}"
