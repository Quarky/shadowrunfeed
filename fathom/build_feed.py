#!/usr/bin/env python3
"""Publish an independent story-only DERELICT feed: FATHOM S1 + DERELICT S2.

Keep the established fathom/feed.xml subscriber URL. Preserve an optional
FATHOM-only season1.xml. Every recording, GUID, date, image and description
is copied from the publisher's live RSS; no media is mirrored or invented.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = "https://feeds.megaphone.fm/SBP4341397353"
BASE_URL = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fathom/"
PUBLIC = BASE_URL + "feed.xml"
SEASON1_PUBLIC = BASE_URL + "season1.xml"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)

# Publisher names genuine story chapters "Season 2 - DERELICT - E6- ...".
# Promotional updates may claim itunes:episodeType=full, so use the title too.
STORY_TITLE = re.compile(
    r"^\s*Season\s+([12])\s*[-–—]\s*(FATHOM|DERELICT)"
    r"\s*[-–—]\s*E\s*0?(\d{1,2})\s*[-–—]",
    re.IGNORECASE,
)


def get_source() -> ET.Element:
    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "FathomDerelictStoryRSS/2.0 (+https://github.com/Quarky/shadowrunfeed)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(20_000_001)
    if len(body) > 20_000_000:
        raise ValueError("Publisher RSS unexpectedly large")
    root = ET.fromstring(body)
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError("Publisher response is not a valid RSS channel")
    return channel


def story_key(item: ET.Element) -> tuple[int, int] | None:
    title = item.findtext("title", "")
    match = STORY_TITLE.match(title)
    if not match:
        return None
    season, series, number = int(match[1]), match[2].upper(), int(match[3])
    if (season, series) not in ((1, "FATHOM"), (2, "DERELICT")):
        return None
    return (season, number) if 1 <= number <= 10 else None


def settext(parent: ET.Element, name: str, value: str) -> None:
    ET.SubElement(parent, name).text = value


def read_previous_season1_guids() -> dict[int, str]:
    """Prevent silently breaking existing FATHOM subscriber history."""
    old = HERE / "feed.xml"
    if not old.exists():
        return {}
    channel = ET.parse(old).getroot().find("channel")
    if channel is None:
        raise ValueError("Existing feed is not valid RSS")
    return {
        key[1]: item.findtext("guid", "").strip()
        for item in channel.findall("item")
        if (key := story_key(item)) is not None and key[0] == 1
    }


def make_feed(
    source: ET.Element,
    items: list[tuple[tuple[int, int], ET.Element]],
    title: str,
    description: str,
    public_url: str,
    built_at: dt.datetime,
) -> bytes:
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    settext(channel, "title", title)
    settext(channel, "link", "https://www.derelictpodcast.com/")
    settext(channel, "description", description)
    settext(channel, "language", source.findtext("language") or "en-us")
    settext(channel, "lastBuildDate", format_datetime(built_at))
    settext(channel, f"{{{ITUNES}}}author", "Night Rocket Productions")
    settext(channel, f"{{{ITUNES}}}summary", description)
    settext(channel, f"{{{ITUNES}}}explicit", "yes")
    settext(channel, f"{{{ITUNES}}}type", "serial")
    artwork = source.find(f"{{{ITUNES}}}image")
    if artwork is not None and artwork.get("href", "").startswith("https://"):
        channel.append(copy.deepcopy(artwork))
    ET.SubElement(
        channel,
        f"{{{ATOM}}}link",
        {"href": public_url, "rel": "self", "type": "application/rss+xml"},
    )
    for (season, number), original in items:
        item = copy.deepcopy(original)
        for tag, value in ((f"{{{ITUNES}}}season", season),
                           (f"{{{ITUNES}}}episode", number)):
            element = item.find(tag)
            if element is None:
                settext(item, tag, str(value))
            else:
                element.text = str(value)
        channel.append(item)
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    assert len(ET.fromstring(xml).find("channel").findall("item")) == len(items)
    return xml


def main() -> None:
    source = get_source()
    chosen: dict[tuple[int, int], ET.Element] = {}
    guids: set[str] = set()
    for item in source.findall("item"):
        key = story_key(item)
        if key is None:
            continue
        enclosure = item.find("enclosure")
        url = enclosure.get("url", "") if enclosure is not None else ""
        guid = item.findtext("guid", "").strip()
        if not guid or not url.startswith("https://"):
            raise ValueError(f"Publisher chapter {key} lacks GUID or HTTPS audio")
        if enclosure is None or enclosure.get("type", "") not in ("audio/mpeg", "audio/mp3"):
            raise ValueError(f"Publisher chapter {key} has no supported MP3 enclosure")
        if key in chosen or guid in guids:
            raise ValueError(f"Duplicate story chapter or GUID: {key}")
        chosen[key] = item
        guids.add(guid)

    expected = [(season, number) for season in (1, 2) for number in range(1, 11)]
    if set(chosen) != set(expected):
        raise ValueError(
            f"Expected all 20 FATHOM/DERELICT story chapters; "
            f"found {sorted(chosen)}. Previous published feed retained."
        )
    previous = read_previous_season1_guids()
    for number, old_guid in previous.items():
        if chosen[1, number].findtext("guid", "").strip() != old_guid:
            raise ValueError(f"FATHOM E{number} GUID changed; preserving subscribers")

    story = [(key, chosen[key]) for key in expected]
    season1 = story[:10]
    now = dt.datetime.now(dt.timezone.utc)
    disclaimer = ("Original publisher-hosted audio from Night Rocket Productions. "
                  "Independent filtered RSS; not an official or affiliated podcast.")
    combined_xml = make_feed(
        source, story, "DERELICT | FATHOM + DERELICT | Complete Seasons 1–2",
        "The complete 20-episode story in narrative order: FATHOM (Season 1) "
        "followed by DERELICT (Season 2). " + disclaimer,
        PUBLIC, now,
    )
    season1_xml = make_feed(
        source, season1, "DERELICT — FATHOM | Complete Season 1",
        "All ten original FATHOM story episodes (DERELICT Season 1). " + disclaimer,
        SEASON1_PUBLIC, now,
    )
    report = {
        "state": "published",
        "source_feed": SOURCE,
        "feed_url": PUBLIC,
        "season1_only_feed_url": SEASON1_PUBLIC,
        "episodes": 20,
        "season1_episodes": 10,
        "season2_episodes": 10,
        "story_scope": "FATHOM S1 E1-E10, then DERELICT S2 E1-E10; story episodes only",
        "built_at": now.isoformat(),
        "items": [
            {"season": season, "number": number, "title": item.findtext("title", ""),
             "guid": item.findtext("guid", "").strip()}
            for (season, number), item in story
        ],
    }
    # Construct and validate every output before replacing any old file.
    artifacts = {
        "feed.xml": combined_xml,
        "season1.xml": season1_xml,
        "status.json": (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    }
    for name, content in artifacts.items():
        temporary = HERE / (name + ".tmp")
        temporary.write_bytes(content)
    for name in artifacts:
        (HERE / (name + ".tmp")).replace(HERE / name)
    print(f"Published {len(story)} story chapters -> {PUBLIC}")
    print(f"Preserved FATHOM-only subscription -> {SEASON1_PUBLIC}")


if __name__ == "__main__":
    main()
