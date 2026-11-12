"""Template lines used after the bundled posts have all been sent."""

from __future__ import annotations

import random

from furbybots.queen.voice import (
    FORMATS,
    TAG_PROBABILITY,
    InvalidPost,
    detect_format,
    validate_post,
)


def render_template(
    rng: random.Random,
    *,
    avoid_format: str | None = None,
) -> tuple[str, str]:
    """Return ``(text, format)`` for a fresh proclamation."""
    missing = [name for name in FORMATS if name not in _BUILDERS]
    if missing:
        raise RuntimeError("Missing a template for: " + ", ".join(missing))
    choices = [name for name in FORMATS if name != avoid_format] or list(FORMATS)
    format_name = rng.choice(choices)
    last_problem = "template produced nothing"
    for _ in range(20):
        text = _with_optional_tag(rng, _BUILDERS[format_name](rng))
        try:
            validate_post(text)
        except InvalidPost as exc:
            last_problem = str(exc)
            continue
        if detect_format(text) != format_name:
            last_problem = "template format label did not match"
            continue
        return text, format_name
    raise RuntimeError(last_problem)


def _with_optional_tag(rng: random.Random, text: str) -> str:
    if "#" in text or rng.random() >= TAG_PROBABILITY or not text.endswith("👑"):
        return text
    tag = rng.choice(("#furby", "#nugget"))
    candidate = f"{text[:-1].rstrip()} {tag} 👑"
    if len(candidate) > 280:
        return text
    return candidate


def _decree(rng: random.Random) -> str:
    subject = rng.choice(
        (
            "nap hour at Pillow Palace",
            "the afternoon hush in the Cushion Kingdom",
            "biscuit o'clock in Snackshire",
            "blanket duty across Lower Blanketshire",
            "the slow hour in Upper New Furbland",
        )
    )
    order = rng.choice(
        (
            "is extended by one cushion",
            "shall be kept in soft voices",
            "is declared a small triumph",
            "will pause for a kingdom-wide yawn",
            "is entrusted to Sir Wigglebottom of Snackshire",
        )
    )
    closer = rng.choice(
        (
            "The Crown has spoken.",
            "Her Majesty is pleased.",
            "By order of Her Majesty.",
        )
    )
    return f"Royal Decree: Let it be known in Furbyland that {subject} {order}. {closer} 👑"


def _proclamation(rng: random.Random) -> str:
    rule = rng.choice(
        (
            "snacks may be eaten in bed when the weather is sneeze-shaped",
            "every cushion shall be fluffed before dusk",
            "pajamas remain lawful until the sun apologizes",
            "a spare blanket shall stay within arm's reach",
            "quiet voices are the law during biscuit o'clock",
        )
    )
    return (
        "Royal Proclamation: throughout Furbyland, "
        f"{rule}. Her Majesty thanks the Cushion Kingdom. 👑"
    )


def _weather(rng: random.Random) -> str:
    condition = rng.choice(
        (
            "Sneeze weather",
            "A blanket fog",
            "Soft draft season",
            "Sunbeam weather",
            "A crumb-light breeze",
        )
    )
    place = rng.choice(
        (
            "Lower Blanketshire",
            "the Cushion Kingdom",
            "Upper New Furbland",
            "Snackshire",
            "Pillow Palace",
        )
    )
    advice = rng.choice(
        (
            "one extra blanket and a biscuit held in reserve",
            "windows left kindly ajar",
            "no sudden standing",
            "cocoa-colored calm",
            "a nap begun before the draft arrives",
        )
    )
    return f"Royal Weather Bulletin: {condition} over {place}. The Crown advises {advice}. 👑"


def _harvest(rng: random.Random) -> str:
    place = rng.choice(
        (
            "Snackshire",
            "Lower Blanketshire",
            "Upper New Furbland",
            "Pillow Palace",
            "the Cushion Kingdom",
        )
    )
    crop = rng.choice(
        (
            "a fine crop of crackers",
            "three excellent dozes",
            "a basket of sunbeams",
            "extra blankets, neatly folded",
            "a distinguished yawn",
        )
    )
    manner = rng.choice(
        (
            "a napkin and a nod",
            "warm approval",
            "a second helping of quiet",
            "crumbs of praise",
            "a place on the royal schedule, after naps",
        )
    )
    return f"Royal Harvest Report: {place} sends {crop}. Her Majesty receives it with {manner}. 👑"


def _mystery(rng: random.Random) -> str:
    puzzle = rng.choice(
        (
            "Who tucked the smaller blanket at Pillow Palace?",
            "Who moved the throne cushion two inches toward the sun?",
            "Why is the biscuit tin in Snackshire lighter than at dawn?",
            "Where did the spare button of Upper New Furbland go?",
            "Who fluffed only the left side of the royal cushion?",
        )
    )
    theory = rng.choice(
        (
            "a polite draft",
            "Sir Wigglebottom of Snackshire, gently and without confession",
            "the sunbeam, acting alone",
            "a nap that got up and walked",
            "Lower Blanketshire, which denies being awake",
        )
    )
    return f"A Royal Mystery: {puzzle} The Crown's working theory is {theory}. 👑"


def _tour(rng: random.Random) -> str:
    start, end = rng.sample(
        (
            "Pillow Palace",
            "Upper New Furbland",
            "the Cushion Kingdom",
            "Lower Blanketshire",
            "Snackshire",
        ),
        2,
    )
    manner = rng.choice(
        (
            "waving from a very slow cushion",
            "pausing whenever a blanket looks welcoming",
            "greeting everyone who is also lying down",
            "carrying one cracker for diplomacy",
            "reviewing the sneezes with solemn warmth",
        )
    )
    return (
        f"Royal Tour: Her Majesty travels from {start} to {end}, {manner}. "
        "Furbyland cheers softly. 👑"
    )


def _investiture(rng: random.Random) -> str:
    who = rng.choice(
        (
            "the roundest cushion at Pillow Palace",
            "a loyal blanket of Lower Blanketshire",
            "the sunbeam on the east sill of Upper New Furbland",
            "Sir Wigglebottom of Snackshire",
            "the smallest cracker in Snackshire",
        )
    )
    title = rng.choice(
        (
            "Knight of the Nap",
            "Keeper of the Emergency Biscuit",
            "Warden of the Quiet Hour",
            "Steward of the Sunbeam",
            "Guardian of the Spare Blanket",
        )
    )
    reaction = rng.choice(
        (
            "The Cushion Kingdom rustles in approval",
            "Her Majesty nods from her cushion",
            "Furbyland cheers in a whisper",
            "Pillow Palace marks the hour with a yawn",
            "The Crown smiles into a blanket",
        )
    )
    return f"Royal Investiture: The Crown names {who} {title}. {reaction}. 👑"


_BUILDERS = {
    "Royal Decree": _decree,
    "Royal Proclamation": _proclamation,
    "Royal Weather Bulletin": _weather,
    "Royal Harvest Report": _harvest,
    "A Royal Mystery": _mystery,
    "Royal Tour": _tour,
    "Royal Investiture": _investiture,
}
