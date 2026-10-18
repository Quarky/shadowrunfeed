#!/usr/bin/env python3
"""Publish a FATHOM-only podcast feed from the official DERELICT RSS.

Exactly 10 Season 1 story episodes. Preserve the publisher's media URLs,
GUIDs, dates and descriptions; never mirror or fabricate recordings.
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
PUBLIC = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fathom/feed.xml"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)

def get_source() -> ET.Element:
    req = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "FathomSeasonRSS/1.0 (+https://github.com/Quarky/shadowrunfeed)",
                 "Accept": "application/rss+xml, application/xml, text/xml"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read(20_000_001)
    if len(body) > 20_000_000:
        raise ValueError("Publisher RSS unexpectedly large")
    root = ET.fromstring(body)
    if root.tag != "rss" or root.find("channel") is None:
        raise ValueError("Publisher response was not a valid RSS channel")
    return root.find("channel")

def episode_number(item: ET.Element) -> int | None:
    title = item.findtext("title", "")
    # Match official "Season 1 - FATHOM - E4 - Pain" and "FATHOM E4 - Pain".
    match = re.search(r"\bFATHOM\b\s*[-:–— ]*\s*(?:E(?:P(?:ISODE)?)?\.?\s*)0?(\d{1,2})\b", title, re.I)
    if not match:
        return None
    number = int(match.group(1))
    return number if 1 <= number <= 10 else None

def settext(parent: ET.Element, tag: str, value: str) -> None:
    ET.SubElement(parent, tag).text = value

def main() -> None:
    source = get_source()
    chosen = {}
    for item in source.findall("item"):
        number = episode_number(item)
        if number is None:
            continue
        enclosure = item.find("enclosure")
        url = enclosure.get("url", "") if enclosure is not None else ""
        guid = item.findtext("guid", "").strip()
        if not url.startswith("https://") or not guid:
            raise ValueError(f"Publisher recording E{number} has no valid GUID/HTTPS audio")
        if number in chosen:
            raise ValueError(f"Publisher RSS has duplicate FATHOM E{number}")
        chosen[number] = item
    if set(chosen) != set(range(1, 11)):
        raise ValueError(f"Expected all 10 FATHOM episodes, found {sorted(chosen)}; keeping previous feed")

    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    settext(channel, "title", "DERELICT — FATHOM | Complete Season 1")
    settext(channel, "link", "https://www.derelictpodcast.com/")
    settext(channel, "description",
            "All 10 episodes of FATHOM, season one of DERELICT, in story order. "
            "Original publisher audio from Night Rocket Productions. "
            "Independent filtered RSS; not an official or affiliated podcast.")
    settext(channel, "language", source.findtext("language") or "en")
    settext(channel, "lastBuildDate", format_datetime(dt.datetime.now(dt.timezone.utc)))
    settext(channel, f"{{{ITUNES}}}author", "Night Rocket Productions")
    settext(channel, f"{{{ITUNES}}}summary",
            "Complete original FATHOM audio drama season (10 story episodes). "
            "Audio hosted by Night Rocket Productions; independent listening index.")
    settext(channel, f"{{{ITUNES}}}explicit", "yes")
    settext(channel, f"{{{ITUNES}}}type", "serial")
    artwork = source.find(f"{{{ITUNES}}}image")
    if artwork is not None and artwork.get("href", "").startswith("https://"):
        channel.append(copy.deepcopy(artwork))
    ET.SubElement(channel, f"{{{ATOM}}}link",
                  {"href": PUBLIC, "rel": "self", "type": "application/rss+xml"})
    status = []
    for number in range(1, 11):
        item = copy.deepcopy(chosen[number])
        # Keep original title, GUID, URL, date, duration, and episode description.
        season = item.find(f"{{{ITUNES}}}season")
        if season is None:
            settext(item, f"{{{ITUNES}}}season", "1")
        ep = item.find(f"{{{ITUNES}}}episode")
        if ep is None:
            settext(item, f"{{{ITUNES}}}episode", str(number))
        channel.append(item)
        status.append({"number": number, "title": item.findtext("title", ""),
                       "guid": item.findtext("guid", "")})
    # Serialize genuine source metadata and audio; never point to downloaded MP3s.
    output = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(output)
    (HERE / "feed.xml").write_bytes(output)
    report = {"state": "published", "source_feed": SOURCE, "feed_url": PUBLIC,
              "episodes": 10, "story_scope": "FATHOM season 1 only",
              "built_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "items": status}
    (HERE / "status.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published FATHOM E1–E10 -> {PUBLIC}")

if __name__ == "__main__":
    main()
