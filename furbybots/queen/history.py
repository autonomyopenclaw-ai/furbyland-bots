"""Remember texts that have already been published so they are not repeated."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from furbybots.xapi.errors import ConfigError


def history_path() -> Path:
    root = Path(os.environ.get("FURBYBOTS_DATA_DIR", "data"))
    return root / "queen_posted.json"


class PostHistory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or history_path()
        self.posts: list[dict] = []
        if not self.path.exists():
            return
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"{self.path} is not valid JSON, so posting stopped rather than "
                "risking a repeated line. Fix or remove that file."
            ) from exc
        posts = data.get("posts") if isinstance(data, dict) else None
        if not isinstance(posts, list):
            raise ConfigError(f"{self.path} does not contain a posts list.")
        self.posts = [item for item in posts if isinstance(item, dict)]

    def texts(self) -> set[str]:
        return {str(item["text"]) for item in self.posts if item.get("text")}

    def last_format(self) -> str | None:
        for item in reversed(self.posts):
            name = item.get("format")
            if isinstance(name, str) and name:
                return name
        return None

    def add(self, text: str, format_name: str, tweet_id: str | None) -> None:
        self.posts.append(
            {
                "text": text,
                "format": format_name,
                "tweet_id": tweet_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"posts": self.posts}, indent=2, ensure_ascii=False) + "\n"
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(self.path)
