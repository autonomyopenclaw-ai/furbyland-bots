"""Optional text providers. A missing key, or a failed call, is not fatal."""

from __future__ import annotations

import os

import requests

from furbybots.xapi.config import PLACEHOLDERS

SYSTEM_PROMPT = """You write a single post for a cozy monarch called the Queen of Furbies.
She calls herself "Her Majesty" or "The Crown". She issues formal, warm, slightly absurd royal announcements about naps, cushions, snacks, blankets, sneeze weather, and knighthoods.

Use these names when they fit: Furbyland, Upper New Furbland, Pillow Palace, the Cushion Kingdom, Lower Blanketshire, Snackshire, Sir Wigglebottom of Snackshire.

Start with exactly one of these labels and a colon:
Royal Decree, Royal Proclamation, Royal Weather Bulletin, Royal Harvest Report, A Royal Mystery, Royal Tour, Royal Investiture.

Rules:
- One post only. No title, no quotes, no preamble.
- Under 260 characters.
- Family-friendly. No politics, news, brands, current events, or links.
- No @mentions.
- End with the crown emoji 👑.
- Use no hashtag, or at most one of #furby or #nugget. Prefer none.
"""

_PROVIDERS = {
    "xai": "https://api.x.ai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}


class LLMWriter:
    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        session: requests.Session | None = None,
        timeout: float = 45,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.session = session or requests.Session()
        self.timeout = timeout

    def write(self, *, avoid: list[str], last_format: str | None) -> str:
        notes = ["Write today's single post."]
        if last_format:
            notes.append(f"The previous format was {last_format}. Choose a different format.")
        if avoid:
            recent = "\n".join(f"- {item}" for item in avoid[-8:])
            notes.append("Do not repeat these posts:\n" + recent)
        response = self.session.post(
            _PROVIDERS[self.provider],
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0.9,
                "max_tokens": 400,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": "\n".join(notes)},
                ],
            },
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"text provider returned HTTP {response.status_code}")
        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("text provider returned an unreadable response") from exc
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(str(part.get("text") or ""))
                else:
                    parts.append(str(part))
            content = "".join(parts)
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("text provider returned an empty post")
        return content


def writer_from_env(session: requests.Session | None = None) -> LLMWriter | None:
    """Use xAI when ``XAI_API_KEY`` is set, otherwise OpenAI."""
    xai = _key("XAI_API_KEY")
    if xai:
        model = os.environ.get("XAI_MODEL", "").strip() or "grok-3"
        return LLMWriter(provider="xai", api_key=xai, model=model, session=session)
    openai = _key("OPENAI_API_KEY")
    if openai:
        model = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
        return LLMWriter(provider="openai", api_key=openai, model=model, session=session)
    return None


def _key(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value in PLACEHOLDERS:
        return ""
    return value
