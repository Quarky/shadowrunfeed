#!/usr/bin/env python3
"""Build an independent, audio-only Lancer actual-play discovery feed.

The audio files stay on original publisher servers. No YouTube ripping,
rehosting, spoken-content modification, or synthetic episode inventions.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime
from html import unescape
import copy
from ranking import priority_order, publication_marker
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PUBLIC = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/feed.xml"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)
EXTERNAL = {
    "rppr": {
        "name": "RPPR — Lancer",
        "url": "https://actualplay.roleplayingpublicradio.com/category/systems/lancer/feed/",
        "note": "Long, mostly intact tabletop sessions with tactical encounters and audible rules adjudication.",
        "pattern": r"^Lancer:\s*(?:Solstice Rain|The Siege of Vermeer)\b",
        "minimum": 3,
    },
    "ccrpg": {
        "name": "CCRPG — Compelling Compiling",
        "url": "https://feeds.captivate.fm/ccrpg/",
        "note": "Natural virtual tabletop conversation, checks, mechs, tactical decisions and campaign continuity.",
        "pattern": r"^Lancer (?:Gig|Ruse|War)\s*[-–]\s*Episode\s+\d+\b",
        "minimum": 150,
    },
    "vertigo": {
        "name": "House of Bob — Vertigo",
        "url": "https://feeds.megaphone.fm/houseofbob",
        "note": "A complete LL0-starting Lancer campaign with memorable combat, but more editing/music than the other sources.",
        "pattern": r"^Vertigo Chapter\s+\d+\s*\[\s*Lancer\s*\]",
        "minimum": 16,
    },
    "rfd": {
        "name": "Roll for Distraction — Lancer",
        "url": "https://rollfordistraction.podbean.com/feed.xml",
        "note": "Complete Lancer campaign seasons C3 and C8; more joking and a tighter edit than the top picks.",
        "pattern": r"^C(?:3|8)E\d+\s*\|\s*Lancer\s*\|",
        "minimum": 21,
    },
}
# These fixed completed campaigns interleave in short blocks; new CCRPG
# recordings arrive at the end, preserving GUIDs and earlier position dates.
BLOCK_ORDER = ("rppr", "ccrpg", "vertigo", "rfd")
ANCHOR = datetime(2026, 10, 1, tzinfo=timezone.utc)

def get_channel(url: str) -> ET.Element:
    req = urllib.request.Request(url, headers={
        "User-Agent": "TableLancerRSS/1.0 (https://github.com/Quarky/shadowrunfeed)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=45) as res:
        data = res.read(16_000_001)
    if len(data) > 16_000_000:
        raise ValueError(f"Publisher RSS exceeds size cap: {url}")
    root = ET.fromstring(data)
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError(f"Not an RSS channel: {url}")
    return channel

def text(parent: ET.Element, name: str, value: str) -> None:
    ET.SubElement(parent, name).text = value

def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()

def episode_order(source: str, title: str) -> tuple[int, int, str]:
    if source == "ccrpg":
        m = re.search(r"Lancer\s+(Gig|Ruse|War)\s*[-–]\s*Episode\s+(\d+)", title, re.I)
        return ({"gig": 1, "ruse": 2, "war": 3}[m[1].lower()], int(m[2]), title)
    if source == "rfd":
        m = re.search(r"C(\d+)E(\d+)", title, re.I)
        return (int(m[1]), int(m[2]), title)
    if source == "vertigo":
        m = re.search(r"Chapter\s+(\d+)", title, re.I)
        return (1, int(m[1]), title)
    if "Siege of Vermeer" in title:
        return (0, 1, title)
    if "Part 1" in title:
        return (1, 1, title)
    return (1, 2, title)

def media_length(url: str) -> int:
    """Resolve a publisher's zero enclosure length without guessing byte sizes."""
    try:
        headers = {"User-Agent": "TableLancerRSS/1.0"}
        for method in ("HEAD", "GET"):
            req = urllib.request.Request(
                url, headers={**headers, **({"Range": "bytes=0-0"} if method == "GET" else {})},
                method=method)
            with urllib.request.urlopen(req, timeout=12) as res:
                cr = res.headers.get("Content-Range", "")
                match = re.search(r"/(\d+)\s*$", cr)
                if match and int(match[1]) > 0:
                    return int(match[1])
                length = int(res.headers.get("Content-Length") or 0)
                if res.status == 200 and length > 0:
                    return length
    except (OSError, ValueError, urllib.error.HTTPError):
        pass
    return 0

def valid_items(source: str, channel: ET.Element):
    spec = EXTERNAL[source]
    pattern = re.compile(spec["pattern"], re.I)
    parsed = []
    rejected = []
    for src_item in channel.findall("item"):
        title = normalize_title(src_item.findtext("title", ""))
        if not pattern.search(title):
            continue
        raw_guid = (src_item.findtext("guid") or src_item.findtext("link") or "").strip()
        enc = src_item.find("enclosure")
        if enc is None or not raw_guid:
            rejected.append(f"{title}: missing publisher GUID or audio enclosure")
            continue
        url = (enc.get("url") or "").strip()
        if source == "rppr" and url.startswith("http://media.blubrry.com/"):
            url = "https://" + url[7:]
        if not url.startswith("https://") or (enc.get("type") or "").lower() not in (
            "audio/mpeg", "audio/mp3", "audio/x-m4a", "audio/mp4", "audio/m4a"):
            rejected.append(f"{title}: no supported HTTPS source audio")
            continue
        raw_len = int(enc.get("length") or 0)
        parsed.append({
            "source": source, "title": title, "item": src_item,
            "guid": raw_guid, "url": url, "bytes": raw_len,
            "duration": src_item.findtext(f"{{{ITUNES}}}duration", ""),
            "key": episode_order(source, title),
        })
    parsed.sort(key=lambda x: x["key"])
    # If the original RSS has a zero-byte enclosure (common with ad-insertion
    # services), probe its actual media response. Never fabricate media bytes.
    unknown = [x for x in parsed if x["bytes"] <= 0]
    if unknown:
        with ThreadPoolExecutor(max_workers=5) as pool:
            sizes = list(pool.map(lambda item: media_length(item["url"]), unknown))
        for item, size in zip(unknown, sizes):
            item["bytes"] = size
    selected = []
    for entry in parsed:
        if entry["bytes"] <= 0:
            rejected.append(f"{entry['title']}: publisher did not supply a positive byte length")
        else:
            selected.append(entry)
    return selected, rejected, len(parsed)

def assemble(queues: dict[str, list[dict]]) -> list[dict]:
    positions = {k: 0 for k in BLOCK_ORDER}
    output = []
    while any(positions[k] < len(queues[k]) for k in BLOCK_ORDER):
        for k in BLOCK_ORDER:
            stop = min(positions[k] + 2, len(queues[k]))
            output.extend(queues[k][positions[k]:stop])
            positions[k] = stop
    return output

def build():
    queues, rejected, source_counts = {}, {}, {}
    for source, spec in EXTERNAL.items():
        channel = get_channel(spec["url"])
        queues[source], rejected[source], discovered = valid_items(source, channel)
        source_counts[source] = {
            "publisher_title": channel.findtext("title"),
            "found": discovered, "included": len(queues[source]),
            "excluded_reasons": rejected[source],
            "source_url": spec["url"]
        }
        # Always require an unbroken list of matched publisher episodes.
        # A missing source or a newly broken feed cannot silently replace
        # previously published playable recordings.
        if discovered < spec["minimum"]:
            raise ValueError(f"{source}: only {discovered} found, expected >= {spec['minimum']}")
        if source != "vertigo" and len(queues[source]) < spec["minimum"]:
            raise ValueError(f"{source}: verified playable audio count fell below expected")
    original_playlist = assemble(queues)
    playlist = priority_order(original_playlist)
    ids = [hashlib.sha256((x["source"] + "|" + x["guid"]).encode()).hexdigest() for x in playlist]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate publisher GUID in curated selection")
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    text(channel, "title", "LANCER | At the Table — Actual Plays & Combat")
    text(channel, "link", "https://github.com/Quarky/shadowrunfeed/tree/main/lancer")
    description = (
        "Independent curated Lancer actual-play podcast: natural table conversation, dice, "
        "pilot choices, tactical rules, mech combat and campaign continuity. "
        "Unmodified publisher-hosted audio; not affiliated with any featured creators or Massif Press. "
        "Original episode dates are stated in descriptions. Episodes are ranked by a "
        "publisher-synopsis gameplay-fit index (NOT a measured percentage of audio playtime). "
        "The RSS publication dates are stable rank markers, not original air dates.")
    text(channel, "description", description)
    text(channel, "language", "en")
    text(channel, "lastBuildDate", format_datetime(datetime.now(timezone.utc)))
    text(channel, f"{{{ITUNES}}}author", "Independent Lancer actual-play listening collection")
    text(channel, f"{{{ITUNES}}}summary", description)
    text(channel, f"{{{ITUNES}}}explicit", "yes")
    text(channel, f"{{{ITUNES}}}type", "serial")
    ET.SubElement(channel, f"{{{ITUNES}}}category", {"text": "Leisure"})
    ET.SubElement(channel, f"{{{ATOM}}}link", {
        "href": PUBLIC, "rel": "self", "type": "application/rss+xml"})
    for number, entry in enumerate(playlist, 1):
        src, spec = entry["source"], EXTERNAL[entry["source"]]
        item = ET.SubElement(channel, "item")
        text(item, "title", f"{spec['name']} | {entry['title']}")
        text(item, "link", entry["item"].findtext("link") or spec["url"])
        text(item, "guid", f"lancer-playlist:{ids[number-1]}")
        item.find("guid").set("isPermaLink", "false")
        original_date = entry["item"].findtext("pubDate", "")
        raw_description = entry["item"].findtext("description", "")
        summary = normalize_title(re.sub(r"<[^>]*>", " ", raw_description))[:550]
        evidence = entry["fit"]
        signals = ", ".join(s["name"] for s in evidence["evidence"]) or "no specific gameplay terms in publisher synopsis"
        text(item, "description", f"GAMEPLAY PRIORITY INDEX {evidence['fit_index_0_to_100']}/100 — "
             f"metadata-based ranking, not a measured percentage of audio runtime. "
             f"Evidence: {signals}. Original producer: {spec['name']}. {spec['note']} "
             f"Original release: {original_date or 'publisher date unlisted'}. "
             f"Original episode: {summary}  Publisher: {spec['url']}")
        text(item, "pubDate", format_datetime(publication_marker(entry)))
        text(item, f"{{{ITUNES}}}author", spec["name"])
        text(item, f"{{{ITUNES}}}explicit", "yes")
        text(item, f"{{{ITUNES}}}episode", str(number))
        if entry["duration"]:
            text(item, f"{{{ITUNES}}}duration", entry["duration"])
        content_type = (entry["item"].find("enclosure").get("type") or "audio/mpeg").lower()
        ET.SubElement(item, "enclosure", {
            "url": entry["url"], "length": str(entry["bytes"]), "type": content_type})
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    reread = ET.fromstring(xml).find("channel").findall("item")
    if len(reread) != len(playlist):
        raise AssertionError("RSS item count differs after serialization")
    if len(playlist) < 170:
        raise ValueError("Too few verified source episodes to replace existing published RSS")

    # Preserve an independent chronological alternative. Both feeds reference
    # exactly the same publisher MP3s and deterministic, stable item GUIDs.
    chronological_root = copy.deepcopy(root)
    chrono_channel = chronological_root.find("channel")
    item_by_guid = {item.findtext("guid"): item for item in chrono_channel.findall("item")}
    for item in list(chrono_channel.findall("item")):
        chrono_channel.remove(item)
    for position, entry in enumerate(original_playlist, 1):
        stable_guid = "lancer-playlist:" + hashlib.sha256(
            (entry["source"] + "|" + entry["guid"]).encode()).hexdigest()
        item = item_by_guid[stable_guid]
        item.find("pubDate").text = format_datetime(
            ANCHOR + timedelta(minutes=len(original_playlist) - position))
        chrono_channel.append(item)
    chrono_channel.find("title").text = "LANCER | At the Table — Campaign Order"
    for atom in chrono_channel.findall(f"{{{ATOM}}}link"):
        atom.set("href", PUBLIC.replace("/feed.xml", "/story-order.xml"))
    chronological_xml = ET.tostring(
        chronological_root, encoding="utf-8", xml_declaration=True)
    if len(ET.fromstring(chronological_xml).find("channel").findall("item")) != len(playlist):
        raise AssertionError("Chronological alternative lost source episodes")
    (ROOT / "story-order.xml").write_bytes(chronological_xml)
    status = {
        "result": "generated_and_xml_validated",
        "total_playable_episodes": len(playlist),
        "source_counts": source_counts,
        "original_audio_hosts_only": True,
        "playlist_order_markers_not_original_dates": True,
        "ranking": {
            "sort": "descending metadata gameplay-fit index",
            "score_is_playtime_percentage": False,
            "actual_play_runtime_percentage_measured": False,
            "source": "publisher show descriptions with transparent keyword signals and editorial source baselines",
            "chronological_alternative": PUBLIC.replace("/feed.xml", "/story-order.xml"),
            "top_20": [
                {
                    "source": e["source"],
                    "title": e["title"],
                    "fit_index_0_to_100": e["fit"]["fit_index_0_to_100"],
                    "evidence": e["fit"]["evidence"],
                }
                for e in playlist[:20]
            ],
        },
        "sha256": hashlib.sha256(xml).hexdigest(),
        "feed_url": PUBLIC,
        "note": "Source enclosures (not audio bytes) verified in RSS. Podcast-app import and individual playback are separate checks.",
    }
    (ROOT / "feed.xml").write_bytes(xml)
    (ROOT / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(playlist),
                      "per_source": {k: v["included"] for k, v in source_counts.items()},
                      "excluded": {k: len(v) for k, v in rejected.items()}}, indent=2))

if __name__ == "__main__":
    build()
