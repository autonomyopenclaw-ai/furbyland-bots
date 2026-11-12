"""Voice rules for posts published as @QueenOfFurbies.

Length is Python's character count. Posts are kept well under 280 because X
weights some emoji as more than one character.
"""

from __future__ import annotations

import re

FORMATS = (
    "Royal Decree",
    "Royal Proclamation",
    "Royal Weather Bulletin",
    "Royal Harvest Report",
    "A Royal Mystery",
    "Royal Tour",
    "Royal Investiture",
)

SIGNATURES = (
    "Her Majesty",
    "The Crown",
    "Furbyland",
    "Upper New Furbland",
    "Pillow Palace",
    "Cushion Kingdom",
    "Lower Blanketshire",
    "Snackshire",
    "Sir Wigglebottom",
)

ALLOWED_TAGS = frozenset({"#furby", "#nugget"})
TAG_PROBABILITY = 0.12
MAX_LENGTH = 280
MIN_LENGTH = 40

MENTION_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]+")
HASHTAG_RE = re.compile(r"#[A-Za-z0-9_]+")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
BLOCKED = (
    "election",
    "senator",
    "congress",
    "parliament",
    "president",
    "democrat",
    "republican",
    "politic",
    "breaking news",
)


class InvalidPost(ValueError):
    """A candidate post breaks the Queen's publishing rules."""


def detect_format(text: str) -> str:
    for name in FORMATS:
        if text.startswith(name + ":"):
            return name
    raise InvalidPost("Refusing this post: it must start with a royal format.")


def validate_post(text: str) -> None:
    """Raise ``InvalidPost`` when ``text`` must not be published."""
    problems: list[str] = []
    if "\n" in text or text != text.strip():
        problems.append("it must be a single line")
    if len(text) > MAX_LENGTH:
        problems.append(f"it is {len(text)} characters, and the limit is {MAX_LENGTH}")
    if len(text) < MIN_LENGTH:
        problems.append("it is too short")
    if not text.endswith("👑"):
        problems.append("it must end with 👑")
    if MENTION_RE.search(text) or "@" in text:
        problems.append("it contains an @mention")
    tags = HASHTAG_RE.findall(text)
    if len(tags) > 1:
        problems.append("it has more than one hashtag")
    elif tags and tags[0].lower() not in ALLOWED_TAGS:
        problems.append("its hashtag must be #furby or #nugget")
    if URL_RE.search(text):
        problems.append("it contains a link")
    lowered = text.lower()
    if any(word in lowered for word in BLOCKED):
        problems.append("it mentions politics or news")
    try:
        detect_format(text)
    except InvalidPost:
        problems.append("it must start with a royal format")
    if not any(name.lower() in lowered for name in SIGNATURES):
        problems.append("it must mention Her Majesty's realm")
    if problems:
        raise InvalidPost("Refusing this post: " + "; ".join(dict.fromkeys(problems)) + ".")


def normalize_text(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    text = " ".join(text.split())
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1].strip()
    return text


def accept_model_text(raw: str) -> str:
    """Return model output when it already fits, or a lightly repaired line."""
    text = normalize_text(raw)
    try:
        validate_post(text)
        return text
    except InvalidPost:
        repaired = _repair(text)
        validate_post(repaired)
        return repaired


def _repair(text: str) -> str:
    text = MENTION_RE.sub("", text)
    tags = HASHTAG_RE.findall(text)
    kept = next((tag for tag in tags if tag.lower() in ALLOWED_TAGS), None)
    text = HASHTAG_RE.sub("", text)
    text = URL_RE.sub("", text)
    text = " ".join(text.split())
    if text.endswith("👑"):
        body = text[:-1].rstrip()
    else:
        body = text.rstrip()
    tag = f" {kept}" if kept else ""
    return f"{body}{tag} 👑".strip()
