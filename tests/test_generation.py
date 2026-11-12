"""Post rules: length, the crown, and no @mentions."""

import json
import random
from pathlib import Path

import pytest

from furbybots.queen.catalog import BUNDLED
from furbybots.queen.compose import render_template
from furbybots.queen.generate import generate_post
from furbybots.queen.history import PostHistory
from furbybots.queen.voice import (
    FORMATS,
    HASHTAG_RE,
    TAG_PROBABILITY,
    accept_model_text,
    validate_post,
    InvalidPost,
)

REALM_NAMES = (
    "Furbyland",
    "Upper New Furbland",
    "Pillow Palace",
    "Cushion Kingdom",
    "Lower Blanketshire",
    "Snackshire",
    "Sir Wigglebottom of Snackshire",
    "Her Majesty",
    "The Crown",
)


def test_bundled_posts_follow_the_rules():
    assert len(BUNDLED) >= 12
    formats = set()
    tagged = []
    for post in BUNDLED:
        validate_post(post.text)
        assert post.text.endswith("👑")
        assert "@" not in post.text
        assert len(post.text) <= 280
        assert post.format_name in FORMATS
        formats.add(post.format_name)
        if "#" in post.text:
            tagged.append(post.text)
    assert formats == set(FORMATS)
    assert len(tagged) == 2
    blob = "\n".join(post.text for post in BUNDLED)
    for name in REALM_NAMES:
        assert name in blob


def test_templates_stay_short_crowned_and_unmentioned():
    assert TAG_PROBABILITY <= 0.2
    rng = random.Random(0)
    seen = set()
    formats = []
    previous = None
    for _ in range(200):
        text, format_name = render_template(rng, avoid_format=previous)
        validate_post(text)
        assert text.endswith("👑")
        assert "@" not in text
        assert len(text) <= 280
        tags = HASHTAG_RE.findall(text)
        assert len(tags) <= 1
        if tags:
            assert tags[0].lower() in {"#furby", "#nugget"}
        seen.add(text)
        formats.append(format_name)
        previous = format_name
    assert len(seen) > 40
    assert all(left != right for left, right in zip(formats, formats[1:]))
    tagged = [text for text in seen if "#" in text]
    assert tagged
    assert len(tagged) / len(seen) < 0.35


def test_rejects_mentions_extra_tags_and_length():
    with pytest.raises(InvalidPost, match="@"):
        validate_post(
            "Royal Decree: Hello @friend from Furbyland. The Crown waves. 👑"
        )
    with pytest.raises(InvalidPost, match="👑"):
        validate_post("Royal Decree: Hello from Furbyland. The Crown waves.")
    with pytest.raises(InvalidPost, match="hashtag"):
        validate_post(
            "Royal Decree: Furbyland cheers. The Crown allows #furby and #nugget. 👑"
        )
    with pytest.raises(InvalidPost, match="hashtag"):
        validate_post("Royal Decree: Furbyland cheers. The Crown waves. #news 👑")
    long = "Royal Decree: " + ("Furbyland naps. The Crown waits. " * 20) + "👑"
    assert len(long) > 280
    with pytest.raises(InvalidPost, match="280"):
        validate_post(long)


def test_mention_from_a_model_is_removed_or_discarded():
    text = accept_model_text(
        "Royal Decree: Hello @friend from Furbyland. The Crown waves. 👑"
    )
    validate_post(text)
    assert text.endswith("👑")
    assert "@" not in text
    assert len(text) <= 280


def test_history_prevents_repeats(tmp_path: Path):
    history = PostHistory(tmp_path / "queen_posted.json")
    rng = random.Random(1)
    first = generate_post(history, rng=rng)
    history.add(first.text, first.format_name, "1")
    second = generate_post(history, rng=random.Random(1))
    assert second.text != first.text
    assert second.text.endswith("👑")
    assert "@" not in second.text
    assert second.format_name != first.format_name


def test_used_bundled_posts_fall_through_to_a_template(tmp_path: Path):
    history = PostHistory(tmp_path / "queen_posted.json")
    for post in BUNDLED:
        history.add(post.text, post.format_name, None)
    generated = generate_post(history, rng=random.Random(2))
    assert generated.source == "template"
    assert generated.text not in {post.text for post in BUNDLED}
    validate_post(generated.text)


def test_valid_model_text_is_used(tmp_path: Path):
    text = (
        "Royal Decree: Furbyland grants an extra pillow at Pillow Palace. "
        "The Crown signs it with a yawn. 👑"
    )
    validate_post(text)

    class Writer:
        def write(self, *, avoid, last_format):
            return text

    history = PostHistory(tmp_path / "queen_posted.json")
    post = generate_post(history, rng=random.Random(0), writer=Writer())
    assert post.text == text
    assert post.source == "llm"
    assert post.text.endswith("👑")
    assert "@" not in post.text


def test_empty_model_text_falls_back(tmp_path: Path):
    class Writer:
        def write(self, *, avoid, last_format):
            return "   "

    history = PostHistory(tmp_path / "queen_posted.json")
    post = generate_post(history, rng=random.Random(0), writer=Writer())
    assert post.source in {"bundled", "template"}
    validate_post(post.text)
    assert post.text.endswith("👑")
    assert "@" not in post.text


def test_repeated_model_text_is_not_used_again(tmp_path: Path):
    text = BUNDLED[0].text

    class Writer:
        def write(self, *, avoid, last_format):
            return text

    history = PostHistory(tmp_path / "queen_posted.json")
    history.add(text, BUNDLED[0].format_name, "1")
    post = generate_post(history, rng=random.Random(0), writer=Writer())
    assert post.text != text
    assert "@" not in post.text
    assert post.text.endswith("👑")


def test_history_file_round_trip(tmp_path: Path):
    path = tmp_path / "queen_posted.json"
    history = PostHistory(path)
    history.add("Royal Decree: Furbyland rests. The Crown approves. 👑", "Royal Decree", "9")
    again = PostHistory(path)
    assert again.texts() == {"Royal Decree: Furbyland rests. The Crown approves. 👑"}
    assert again.last_format() == "Royal Decree"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["posts"][0]["tweet_id"] == "9"
