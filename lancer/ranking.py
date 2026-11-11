"""Transparent episode-synopsis ranking for the Lancer listening feed.

This is a fit INDEX, never a percentage of audio runtime. Real gameplay time
shares need time-coded transcripts or listening, not RSS descriptions.
"""
from __future__ import annotations
import re
from html import unescape

BASE_INDEX = {"ccrpg": 76, "rppr": 76, "rfd": 64, "vertigo": 56}
SOURCE_TIE = {"ccrpg": 4, "rppr": 3, "rfd": 2, "vertigo": 1}
# These source baselines are editorial preferences, not measured performance.
# We prioritize sustained, low-production play over edited storytelling.
TRIGGERS = {
    "combat_or_rolls": (
        r"\b(fight(?:ing)?|battle|combat|attacks?|shoot(?:ing)?|firefight|"
        r"ambush|siege|skirmish|under fire|under attack|duel|"
        r"enemy forces|hostile forces|robots attack|weapons fire)\b",
        11,
    ),
    "tactical_play": (
        r"\b(mechs?|tactics?|defend|defense|hold the line|"
        r"weapons?|maneuver|breach|assault|hack(?:ing)?|"
        r"roll(?:ing)?|initiative|rounds?|overcharge|"
        r"stabilize|tech attack|structure damage)\b",
        6,
    ),
    "in_character_play": (
        r"\b(rescue|search|investigat\w*|explor\w*|negotia\w*|"
        r"question(?:ing)?|infiltrat\w*|confront\w*|talk(?:ing)?|"
        r"discover|mission|evacuat\w*|escape|"
        r"survivors?|take a stand|take a risk|choose)\b",
        5,
    ),
    "active_situation": (
        r"\b(trap|danger|pursu\w*|chase|"
        r"surrounded|collaps\w*|under siege|"
        r"outnumbered|enemies|opponents)\b",
        3,
    ),
    "mostly_preparation": (
        r"\b(character creation|level(?:ing)? up|upgrade time|"
        r"build crafting|shopping episode|downtime only|"
        r"debrief|interlude|epilogue|recap episode|"
        r"q[& ]a|behind the scenes|retrospective)\b",
        -13,
    ),
}
CREDITS_START = re.compile(
    r"(?:The Crew of the|First our Lancer Pilots|"
    r"Featuring:|Album Art:|Episode Artwork|"
    r"Support the Show:|Need More Bob|"
    r"Music by:|Intro and Outro music|"
    r"Patreon\s*\||Follow us on)",
    re.IGNORECASE,
)

def synopsis(entry: dict) -> str:
    raw = entry["item"].findtext("description", "")
    if not raw:
        return ""
    raw = unescape(raw)
    raw = re.sub(r"<[^>]*>", " ", raw)
    raw = unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = CREDITS_START.split(raw, maxsplit=1)[0]
    return raw[:620]

def fit(entry: dict) -> dict:
    src = entry["source"]
    title = entry["title"]
    scene = synopsis(entry)
    # Synopsis is preferred; title may contain important encounter terms.
    text = (scene + " " + title).casefold()
    index = BASE_INDEX[src]
    signals = []
    for name, (pattern, points) in TRIGGERS.items():
        if re.search(pattern, text, re.I):
            index += points
            signals.append({"name": name, "points": points})
    index = min(100, max(0, index))
    return {
        "fit_index_0_to_100": index,
        "evidence": signals,
        "method": "publisher_synopsis_and_editorial_baseline",
        "measured_actual_play_percent": None,
        "confidence": "low",  # No full timed episode audio/transcript analysis.
        "synopsis": scene[:380],
    }

def priority_order(playlist: list[dict]) -> list[dict]:
    for item in playlist:
        item["fit"] = fit(item)
    return sorted(playlist, key=lambda e: (
        -e["fit"]["fit_index_0_to_100"],
        -SOURCE_TIE[e["source"]],
        e["key"],
        e["guid"],
    ))

def publication_marker(entry: dict):
    """Stable sort date based on fit tier and fixed episode identity.

    Different publisher audio release dates are irrelevant to personalized
    ordering. This field is a sort marker only; original date goes in summary.
    """
    from datetime import datetime, timedelta, timezone
    source = entry["source"]
    tier = entry["fit"]["fit_index_0_to_100"]
    # The source and episode identity keep the sort marker stable across runs.
    episode_key = entry["key"]
    within_day = {
        "ccrpg": 40000,
        "rppr": 30000,
        "rfd": 20000,
        "vertigo": 10000,
    }[source] - (episode_key[0] * 2000 + episode_key[1] * 12)
    within_day = max(0, within_day)
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=tier, seconds=within_day)
