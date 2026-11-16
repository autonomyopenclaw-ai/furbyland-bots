"""Choose one original post: a text provider, then bundled lines, then a template."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from furbybots.queen.catalog import BUNDLED
from furbybots.queen.compose import render_template
from furbybots.queen.history import PostHistory
from furbybots.queen.voice import accept_model_text, detect_format


@dataclass(frozen=True)
class GeneratedPost:
    text: str
    format_name: str
    source: str


class TextWriter(Protocol):
    """Anything with ``write(avoid=..., last_format=...)`` can supply the line."""

    def write(self, *, avoid: list[str], last_format: str | None) -> str:
        """Return one post."""


def generate_post(
    history: PostHistory,
    *,
    rng: random.Random | None = None,
    writer: TextWriter | None = None,
) -> GeneratedPost:
    chooser = rng or random.Random(datetime.now(timezone.utc).date().isoformat())
    seen = history.texts()
    last_format = history.last_format()
    if writer is not None:
        try:
            raw = writer.write(avoid=list(seen), last_format=last_format)
            text = accept_model_text(raw)
            if text not in seen:
                return GeneratedPost(text, detect_format(text), "llm")
        except Exception as exc:
            # A provider failure must not stop the daily post.
            print(
                f"Text provider was not used ({exc}). A local post will be used instead.",
                file=sys.stderr,
            )
    bundled = _pick_bundled(seen, last_format, chooser)
    if bundled is not None:
        return bundled
    for _ in range(60):
        text, format_name = render_template(chooser, avoid_format=last_format)
        if text not in seen:
            return GeneratedPost(text, format_name, "template")
    raise RuntimeError("Could not generate a new post that has not already been used.")


def _pick_bundled(
    seen: set[str],
    last_format: str | None,
    rng: random.Random,
) -> GeneratedPost | None:
    unused = [post for post in BUNDLED if post.text not in seen]
    if not unused:
        return None
    preferred = [post for post in unused if post.format_name != last_format]
    choice = rng.choice(preferred or unused)
    return GeneratedPost(choice.text, choice.format_name, "bundled")
