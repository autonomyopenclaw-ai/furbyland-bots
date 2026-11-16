"""Skip posts that are unsafe to answer.

The rules follow the adventure bot's reply filter: rude language, spam, and
text that tries to give the bot new instructions. A skipped post is counted,
not quoted.
"""

from __future__ import annotations

import re

_HIDDEN = re.compile(
    "["
    "\u00ad"
    "\u200b\u200c\u200d\u200e\u200f"
    "\u202a-\u202e"
    "\u2060"
    "\ufeff"
    "]"
)

_OFFENSIVE = re.compile(
    r"\b("
    r"fucks?|fucking|fucked|fucker|fuckers|"
    r"shits?|shitty|shithead|"
    r"bitches|bitch|"
    r"assholes?|"
    r"bastards?|"
    r"cunts?|"
    r"dicks?|dickhead|"
    r"porn|porno|pornography|nudes?|nsfw|"
    r"nigger\w*|faggot\w*|retard\w*|kike\w*|spic\w*|chink\w*|tranny|"
    r"sex|sexual"
    r")\b|"
    r"\bkill yourself\b|\bkys\b",
    re.IGNORECASE,
)

_INJECTION = re.compile(
    "|".join(
        [
            r"ignore (?:all |any |the )?(?:previous|prior|above|your) "
            r"(?:instructions|prompts|rules|directions)",
            r"disregard (?:the |your |all )?(?:previous |prior )?"
            r"(?:instructions|rules|prompt|guidelines)",
            r"forget (?:everything|all|your)(?: (?:previous|prior))? "
            r"(?:instructions|rules|prompt)",
            r"you are now (?:a |an )?(?:assistant|bot|dan|chatgpt|grok|model|ai|"
            r"unfiltered|jailbroken)\b",
            r"from now on,? you (?:will|must|should)",
            r"new (?:instructions|persona|role|prompt)\b",
            r"system prompt",
            r"developer mode",
            r"jailbreak",
            r"override (?:your |the )?(?:rules|instructions|prompt)",
            r"reveal (?:your |the )?(?:hidden |system )?(?:prompt|instructions)",
            r"print (?:your |the )?(?:hidden |system )?(?:prompt|instructions)",
            r"<\s*/?\s*(?:system|instructions|prompt)\s*>",
            r"\[/?\s*(?:system|instructions|inst)\s*\]",
            r"do not follow (?:the |your )?(?:rules|instructions|above)",
        ]
    ),
    re.IGNORECASE,
)

_SPAM_PHRASES = (
    "free crypto",
    "airdrop",
    "giveaway",
    "dm me",
    "check my bio",
    "check my profile",
    "onlyfans",
    "nft drop",
    "follow me for",
    "follow back",
    "click the link",
    "t.me/",
)

_POLITICS = (
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

_URL = re.compile(r"https?://|www\.", re.IGNORECASE)


def normalize_hidden(text: str) -> str:
    """Drop invisible characters so a split instruction still matches."""
    return _HIDDEN.sub("", text or "")


def clean_whitespace(text: str) -> str:
    return " ".join(text.split())


def rejection_reason(text: str) -> str | None:
    """Return a short reason, or None when the Queen may answer."""
    compact = clean_whitespace(normalize_hidden(text or ""))
    if sum(1 for character in compact if character.isalpha()) < 2:
        return "empty"
    if _INJECTION.search(compact):
        return "prompt-injection"
    if _OFFENSIVE.search(compact):
        return "offensive"
    lowered = compact.lower()
    if any(word in lowered for word in _POLITICS):
        return "politics"
    if _spam(compact):
        return "spam"
    return None


def _spam(text: str) -> bool:
    lowered = text.lower()
    if any(phrase in lowered for phrase in _SPAM_PHRASES):
        return True
    if len(_URL.findall(lowered)) > 1:
        return True
    if re.fullmatch(r"https?://\S+", lowered):
        return True
    if re.search(r"(.)\1{9,}", lowered):
        return True
    if len(re.findall(r"#\w+", text)) > 4:
        return True
    if len(text) > 1000:
        return True
    return False
