"""Transparent episode-synopsis ranking for the Lancer listening feed.

This is a fit INDEX, never a percentage of audio runtime. Real gameplay time
shares need time-coded transcripts or listening, not RSS descriptions.
"""
from __future__ import annotations
import re
import json
from pathlib import Path
from html import unescape

REVIEW_FILE = Path(__file__).resolve().parent / "reviewed-episode-evidence.json"

def load_reviewed_evidence():
    data = json.loads(REVIEW_FILE.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    records = {(r["source"], r["exact_title"]): r for r in data["reviewed"]}
    assert len(records) == len(data["reviewed"]), "Duplicate transcript-reviewed episode"
    for r in records.values():
        assert r["captions_endpoint_verified"] is True
        assert 0 <= int(r["editorial_fit_index"]) <= 100
        assert r["measured_gameplay_percent"] is None, "No unsupported playtime fraction"
        assert r["time_segments"], "Reviewed score requires caption time evidence"
    return records

REVIEWED = load_reviewed_evidence()

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
    # A blurb cannot justify a very high priority rank. Cap unknown cases
    # until a real caption/timed-session check is available.
    review = REVIEWED.get((src, title))
    if review is not None:
        index = int(review["editorial_fit_index"])
        method = "timed_caption_samples_plus_editorial_pacing_judgement"
        confidence = review["review_confidence"]
        signals.append({"name": "checked_caption_timeline_and_pacing", "points": 0})
        if review.get("user_feedback"):
            signals.append({"name": "direct_listener_pacing_feedback", "points": 0})
    else:
        index = min(index, 79)
        method = "publisher_synopsis_only_provisional"
        confidence = "low_unreviewed"
    return {
        "fit_index_0_to_100": index,
        "evidence": signals,
        "method": method,
        "measured_actual_play_percent": None,
        "confidence": confidence,
        "synopsis": scene[:380],
        "review_evidence": (
            {
                "video_url": review["video_url"],
                "captions_url": review["captions_url"],
                "verdict": review["verdict"],
                "caption_end_seconds": review["caption_end_seconds"],
                "time_segments": review["time_segments"],
            }
            if review else None
        ),
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
        "ccrpg": 60000,
        "rppr": 44000,
        "rfd": 34000,
        "vertigo": 12000,
    }[source] - (episode_key[0] * 1500 + episode_key[1] * 5)
    within_day = max(0, within_day)
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=tier, seconds=within_day)
