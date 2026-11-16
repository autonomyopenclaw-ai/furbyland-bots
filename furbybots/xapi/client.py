"""User-context client for X API v2.

Endpoints used here are ``GET /2/users/me``, ``GET /2/tweets/search/recent``,
and ``POST /2/tweets``. ``create_tweet`` accepts ``in_reply_to`` so a bot can
reply in a thread. ``search_recent`` reads one page and does not page further.
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

    def search_recent(self, query: str, *, max_results: int = 10) -> list[SearchPost]:
        """Return one page of recent posts. ``max_results`` is kept between 10 and 100."""
        bounded = min(100, max(10, max_results))
        payload = self._request(
            "GET",
            f"{API_BASE}/tweets/search/recent",
            params={
                "query": query,
                "max_results": bounded,
                "tweet.fields": (
                    "id,text,author_id,created_at,public_metrics,"
                    "referenced_tweets,possibly_sensitive"
                ),
                "expansions": "author_id",
                "user.fields": "id,username",
            },
        )
        return _parse_search(payload)

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
            raise self._http_error(response, url)
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

    def _http_error(self, response: requests.Response, url: str) -> XApiError:
        detail = _detail(response, self._secrets)
        status = response.status_code
        searching = "/tweets/search/" in url
        if status == 429 and searching:
            reset = response.headers.get("x-rate-limit-reset", "")
            wait = (
                f" The limit resets at unix time {reset}."
                if reset
                else " Wait and try again later."
            )
            return XApiError(
                429,
                "Recent search was rate limited (HTTP 429)."
                + wait
                + " Nothing was posted."
                + detail,
            )
        if status == 403 and searching:
            return XApiError(
                403,
                "Recent search refused this request (HTTP 403). "
                "GET /2/tweets/search/recent needs to be available on this "
                "app's X API plan. Nothing was posted."
                + detail,
            )
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


@dataclass(frozen=True)
class SearchPost:
    id: str
    text: str
    author_id: str
    username: str
    created_at: str = ""
    like_count: int = 0
    retweet: bool = False
    reply: bool = False
    sensitive: bool = False


def _parse_search(payload: dict) -> list[SearchPost]:
    rows = payload.get("data") or []
    if not isinstance(rows, list):
        return []
    users: dict[str, str] = {}
    includes = payload.get("includes")
    if isinstance(includes, dict):
        listed = includes.get("users") or []
        if isinstance(listed, list):
            for user in listed:
                if isinstance(user, dict) and user.get("id"):
                    users[str(user["id"])] = str(user.get("username") or "").lstrip("@")
    posts: list[SearchPost] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        post_id = str(row.get("id") or "")
        text = str(row.get("text") or "")
        if not post_id or not text:
            continue
        author_id = str(row.get("author_id") or "")
        metrics = row.get("public_metrics") if isinstance(row.get("public_metrics"), dict) else {}
        try:
            likes = int(metrics.get("like_count") or 0)
        except (TypeError, ValueError):
            likes = 0
        kinds: set[str] = set()
        refs = row.get("referenced_tweets") or []
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict) and ref.get("type"):
                    kinds.add(str(ref["type"]))
        posts.append(
            SearchPost(
                id=post_id,
                text=text,
                author_id=author_id,
                username=users.get(author_id, ""),
                created_at=str(row.get("created_at") or ""),
                like_count=likes,
                retweet="retweeted" in kinds or text.startswith("RT @"),
                reply="replied_to" in kinds,
                sensitive=bool(row.get("possibly_sensitive")),
            )
        )
    return posts


def _detail(response: requests.Response, secrets: list[str]) -> str:
    text = (response.text or "").replace("\n", " ").strip()
    text = redact(text, secrets)
    if len(text) > 240:
        text = text[:240] + "..."
    if not text:
        return ""
    return f" X said: {text}"
