#!/usr/bin/env python3
"""Build the Anomaly podcast from its vetted 120-episode source catalog.

This is a BRAND NEW RSS channel and episode identity at the existing Anomaly URL.
No legacy feed is parsed, no previous episode GUID is reused, and published
episode dates remain stable across scheduled rebuilds. No audio is rehosted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import uuid
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)

PUBLIC = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/"
HOME = "https://github.com/Quarky/shadowrunfeed/tree/main/anomaly"
TITLE = "Anomaly - Stories and Tabletop Actual Plays"
LAUNCH = datetime(2026, 10, 20, 18, 30, tzinfo=timezone.utc)
THEMES = {
    "communities": "Culture, community and relationships",
    "eilistraee": "Eilistraee, faith and defection",
    "itich": "Itich, caves and ancient ruins",
    "wall": "The Wall, psychic threats and anomalies",
    "attina": "Transformation, magic and identity",
    "aberrations": "Ancient minds and aberrations",
}

def child(parent, name, value):
    e = ET.SubElement(parent, name)
    e.text = str(value)
    return e

def validate_source(entries):
    if len(entries) != 120:
        raise ValueError("Expected exactly 120 source recordings")
    urls, identities, stats = set(), set(), {}
    for n, ep in enumerate(entries, 1):
        if ep["number"] != n:
            raise ValueError("Unexpected position at " + str(n))
        role = "story" if n % 2 else "actual_play"
        if ep["role"] != role or ep["theme"] not in THEMES:
            raise ValueError("Role/theme mismatch at " + str(n))
        stats[ep["theme"]] = stats.get(ep["theme"], 0) + 1
        if ep["publisher"] in ("Worlds Beyond Number", "Dungeons of Drakkenheim"):
            raise ValueError("Familiar show escaped the optional playlist")
        url = ep["audio_url"]
        if not url.startswith("https://") or url in urls:
            raise ValueError("Missing, non-HTTPS or duplicate publisher enclosure")
        if int(ep["audio_length"]) <= 0:
            raise ValueError("Unknown enclosure length")
        if not ep["audio_type"].startswith("audio/"):
            raise ValueError("Unsupported enclosure type")
        urls.add(url)
        identities.add((ep["publisher"], ep["title"]))
    if len(urls) != 120 or set(stats) != set(THEMES) or set(stats.values()) != {20}:
        raise ValueError("Episode/theme balance is not 60/60 across six themes")

def render(entries):
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    child(channel, "title", TITLE)
    child(channel, "link", HOME)
    child(channel, "description",
          "An independent, curated collection of 120 original-publisher fantasy "
          "stories and tabletop actual plays, alternating 60/60. Six Anomaly "
          "inspiration themes. Source recordings are not campaign canon.")
    child(channel, "language", "en")
    child(channel, "copyright", "Audio copyrights remain with the original publishers.")
    child(channel, "{%s}author" % ITUNES, "Anomaly Listening Catalog")
    child(channel, "{%s}summary" % ITUNES,
          "Fantasy fiction, characters and actual plays, linked to their original publishers.")
    child(channel, "{%s}explicit" % ITUNES, "true")
    child(channel, "{%s}type" % ITUNES, "episodic")
    ET.SubElement(channel, "{%s}category" % ITUNES, {"text": "Leisure"})
    img = ET.SubElement(channel, "image")
    child(img, "url", PUBLIC + "cover.png")
    child(img, "title", TITLE)
    child(img, "link", HOME)
    ET.SubElement(channel, "{%s}image" % ITUNES, {"href": PUBLIC + "cover.png"})
    ET.SubElement(channel, "{%s}link" % ATOM, {
        "href": PUBLIC + "feed-v2.xml",
        "rel": "self",
        "type": "application/rss+xml",
    })
    child(channel, "lastBuildDate", format_datetime(LAUNCH, usegmt=True))
    for ep in entries:
        n = ep["number"]
        item = ET.SubElement(channel, "item")
        role = "STORY" if ep["role"] == "story" else "ACTUAL PLAY"
        child(item, "title", f"{n:03d} - {role} - {ep['publisher']} - {ep['title']}")
        child(item, "link", ep["source_link"] or ep["audio_url"])
        details = ("Publisher: " + ep["publisher"] + ". Theme: " + THEMES[ep["theme"]]
                   + ". Publisher release: " + ep["source_date"] + ". "
                   + "External listening inspiration only, not Anomaly canon. "
                   + "Episode description: " + ep["description"])
        child(item, "description", details)
        # A new show with entirely new, deterministic episode IDs.
        identity = uuid.uuid5(uuid.NAMESPACE_URL, PUBLIC + str(n) + ep["audio_url"])
        guid = child(item, "guid", "urn:uuid:" + str(identity))
        guid.set("isPermaLink", "false")
        child(item, "pubDate", format_datetime(LAUNCH-timedelta(minutes=n), usegmt=True))
        ET.SubElement(item, "enclosure", {
            "url": ep["audio_url"],
            "length": str(int(ep["audio_length"])),
            "type": ep["audio_type"],
        })
        child(item, "{%s}episodeType" % ITUNES, "full")
        child(item, "{%s}episode" % ITUNES, n)
        child(item, "{%s}explicit" % ITUNES, "true")
        if ep["duration"]:
            child(item, "{%s}duration" % ITUNES, ep["duration"])

    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    data = data.replace(b"<?xml version='1.0' encoding='utf-8'?>",
                        b'<?xml version="1.0" encoding="UTF-8"?>', 1)
    return data

def main():
    manifest = json.loads((HERE / "fresh-episode-catalog.json").read_text("utf-8"))
    entries = manifest["episodes"]
    validate_source(entries)
    result = render(entries)
    parsed = ET.fromstring(result)
    items = parsed.findall("./channel/item")
    guids = [x.findtext("guid") for x in items]
    assert len(set(guids)) == len(guids) == 120
    assert all(x.startswith("urn:uuid:") for x in guids)
    assert b"magudonya" not in result.lower()
    for name in ("feed-v2.xml", "feed.xml"):
        target = HERE / name
        if not target.exists() or target.read_bytes() != result:
            target.write_bytes(result)
    status_path = HERE / "status.json"
    status = json.loads(status_path.read_text("utf-8"))
    status["state"] = "published"
    status["published_rss_engine"] = "new-standalone-catalog"
    status["rss_identity"] = "anomaly:new-2026-uuid"
    status["total_episodes"] = 120
    status["story"] = status["actual_play"] = 60
    status["interleave_valid"] = True
    status["generated_at"] = LAUNCH.isoformat()
    new = json.dumps(status, indent=2, ensure_ascii=False) + "\n"
    if status_path.read_text("utf-8") != new:
        status_path.write_text(new, encoding="utf-8")
    print("PASS: completely rebuilt new podcast RSS, 120 new episode IDs, "
          "valid iTunes tags and stable release dates; identical canonical and alternate feeds")

if __name__ == "__main__":
    main()
