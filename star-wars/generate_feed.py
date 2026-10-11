#!/usr/bin/env python3
"""Build Star Wars FFG listening feeds from publishers' current public RSS.

Never downloads or republishes MP3 files. A show with no matching publisher
recordings is not published; any previously published XML is left intact.
Requires only Python's standard library.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/Quarky/shadowrunfeed/tree/main/star-wars"
CDN = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)

def get_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "QuarkyStarWarsPodcastIndex/1.0 (+https://github.com/Quarky/shadowrunfeed)"
    })
    with urllib.request.urlopen(request, timeout=40) as response:
        body = response.read(20_000_001)
    if len(body) > 20_000_000:
        raise ValueError("Source RSS exceeds 20 MB")
    return body

def publisher_url(show: dict) -> list[str]:
    feeds = [show["source_feed"]] if show.get("source_feed") else []
    feeds.extend(show.get("fallback_feeds", []))
    if show.get("apple_podcast_id") and not feeds:
        ident = int(show["apple_podcast_id"])
        query = urllib.parse.urlencode({"id": ident, "entity": "podcast", "country": "us"})
        payload = json.loads(get_bytes("https://itunes.apple.com/lookup?" + query))
        matches = [r for r in payload.get("results", []) if r.get("collectionId") == ident]
        if not matches or not matches[0].get("feedUrl"):
            raise ValueError(f"Apple lookup for podcast {ident} has no official feedUrl")
        feeds.insert(0, matches[0]["feedUrl"])
    return list(dict.fromkeys(feeds))

def extend_paged_archive(channel: ET.Element, url: str, show: dict) -> int:
    """Discover older public WordPress RSS pages without inventing episodes."""
    if show["id"] != "dice-for-brains" or "diceforbrains.com/feed/podcast" not in url:
        return 0
    def key(item):
        enclosure = item.find("enclosure")
        return item.findtext("guid") or (enclosure.get("url") if enclosure is not None else item.findtext("link"))
    seen = {key(item) for item in channel.findall("item")}
    total = 0
    for page in range(2, 26):
        parts = urllib.parse.urlsplit(url)
        query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != "paged"]
        query.append(("paged", str(page)))
        page_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(query), parts.fragment))
        try:
            archive = ET.fromstring(get_bytes(page_url)).find("channel")
            if archive is None:
                break
            new_items = []
            for item in archive.findall("item"):
                identifier = key(item)
                if identifier and identifier not in seen:
                    seen.add(identifier)
                    new_items.append(item)
            if not new_items:
                break
            for item in new_items:
                channel.append(copy.deepcopy(item))
            total += len(new_items)
        except (OSError, ET.ParseError, ValueError) as error:
            print(f"Publisher archive page {page} unavailable: {error}", file=sys.stderr)
            break
    return total

def read_source(show: dict) -> tuple[ET.Element, str]:
    failures = []
    for url in publisher_url(show):
        try:
            root = ET.fromstring(get_bytes(url))
            channel = root.find("channel")
            if root.tag != "rss" or channel is None:
                raise ValueError("Response is not an RSS 2.0 channel")
            if not channel.findall("item"):
                raise ValueError("Publisher RSS contains no episodes")
            extra = extend_paged_archive(channel, url, show)
            if extra:
                print(f"Extended publisher archive by {extra} episodes")
            return channel, url
        except (ValueError, OSError, ET.ParseError, urllib.error.URLError) as error:
            failures.append(f"{url}: {type(error).__name__}: {error}")
    raise RuntimeError(" | ".join(failures) if failures else "No publisher feed")

def date_of(item: ET.Element) -> dt.datetime | None:
    try:
        timestamp = parsedate_to_datetime(item.findtext("pubDate", "") or "")
        return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None

def select_items(channel: ET.Element, show: dict) -> list[ET.Element]:
    rules = show["selection"]
    filtered = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        enclosure = item.find("enclosure")
        audio = enclosure.get("url", "") if enclosure is not None else ""
        if not title or not audio.startswith(("https://", "http://")):
            continue
        if re.search(rules.get("exclude", "(?!)"), title):
            continue
        if rules["mode"] == "title_regex" and not re.search(rules["include"], title):
            continue
        if rules["mode"] == "before_date":
            released = date_of(item)
            if released is None or released.date() >= dt.date.fromisoformat(rules["cutoff"]):
                continue
        filtered.append(item)
    # Repeated GUIDs or enclosures are almost always a broken publisher feed.
    found = set()
    unique = []
    for item in filtered:
        key = item.findtext("guid") or item.find("enclosure").get("url")
        if key not in found:
            found.add(key)
            unique.append(item)
    if not unique:
        raise ValueError("No matching Star Wars episodes with valid publisher audio")
    return unique

def titled(item: ET.Element) -> str:
    return (item.findtext("title") or "").strip()

def clone_item(item: ET.Element, show: dict, combined: bool) -> ET.Element:
    result = copy.deepcopy(item)
    original_id = item.findtext("guid") or item.find("enclosure").get("url")
    fingerprint = hashlib.sha256((show["id"] + "|" + original_id).encode("utf-8")).hexdigest()
    guid = result.find("guid")
    if guid is None:
        guid = ET.SubElement(result, "guid")
    guid.text = "urn:quarky:starwars:" + fingerprint
    guid.set("isPermaLink", "false")
    if combined:
        new_title = show["title"] + " — " + titled(item)
        result.find("title").text = new_title
        itunes_title = result.find(f"{{{ITUNES}}}title")
        if itunes_title is not None:
            itunes_title.text = new_title
        for tag in (f"{{{ITUNES}}}episode", f"{{{ITUNES}}}season"):
            for elem in result.findall(tag):
                result.remove(elem)
        desc = result.find("description")
        if desc is None:
            desc = ET.SubElement(result, "description")
        desc.text = "Original publisher: " + show["title"] + ". " + (desc.text or "")
    return result

def make_feed(title: str, description: str, filename: str, entries: list[tuple[dict, ET.Element]], source_channel: ET.Element | None = None) -> bytes:
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    def put(name: str, value: str) -> None:
        ET.SubElement(channel, name).text = value
    put("title", title)
    put("link", REPO)
    put("language", "en")
    put("description", description)
    put(f"{{{ITUNES}}}author", "Independent Quarky listening catalog (not affiliated with the creators)")
    put(f"{{{ITUNES}}}summary", description)
    put(f"{{{ITUNES}}}type", "episodic")
    put(f"{{{ITUNES}}}explicit", "yes")
    ET.SubElement(channel, f"{{{ITUNES}}}category", {"text": "Leisure"})
    ET.SubElement(channel, f"{{{ATOM}}}link", {
        "href": CDN + "/" + filename, "rel": "self", "type": "application/rss+xml"
    })
    if source_channel is not None:
        image = source_channel.find("image/url")
        if image is not None and image.text and image.text.startswith("https://"):
            picture = ET.SubElement(channel, "image")
            ET.SubElement(picture, "url").text = image.text
            ET.SubElement(picture, "title").text = title
            ET.SubElement(picture, "link").text = REPO
            ET.SubElement(channel, f"{{{ITUNES}}}image", {"href": image.text})
    combined = filename == "feed.xml"
    # Podcast apps typically display newest entries first.
    entries = sorted(entries, key=lambda record: date_of(record[1]) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True)
    for show, item in entries:
        channel.append(clone_item(item, show, combined))
    ET.indent(root, space="  ")
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(data)  # Validate before replacing files.
    return data

def safe_write(path: Path, payload: bytes) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(payload)
    temp.replace(path)

def featured(episodes: list[ET.Element], highlights: list[str]) -> list[ET.Element]:
    chosen = []
    ids = set()
    for needle in highlights:
        options = [x for x in episodes if needle.casefold() in titled(x).casefold()]
        if len(options) == 1:
            entry = options[0]
            key = entry.findtext("guid") or entry.find("enclosure").get("url")
            if key not in ids:
                chosen.append(entry)
                ids.add(key)
    # If the nominated recording isn't currently in publisher RSS, prefer the
    # earliest available entry point. Do NOT call it highest-rated.
    if not chosen:
        chosen = sorted(episodes, key=lambda e: date_of(e) or dt.datetime.max.replace(tzinfo=dt.timezone.utc))[:2]
    return chosen[:4]

def main() -> int:
    cfg = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
    report = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "shows": {}, "combined": None}
    all_featured = []
    success = 0
    for show in cfg["shows"]:
        ident = show["id"]
        try:
            channel, source = read_source(show)
            episodes = select_items(channel, show)
            name = ident + ".xml"
            feed = make_feed(
                show["title"] + " — curated Star Wars actual play",
                "Independent filtered listening feed for " + show["title"] + ". Audio, descriptions, and credits originate with the original publisher; no files are copied. NOT an episode-rating list.",
                name,
                [(show, item) for item in episodes],
                channel,
            )
            safe_write(HERE / name, feed)
            favorite = featured(episodes, show.get("highlight_titles", []))
            all_featured.extend((show, item) for item in favorite)
            report["shows"][ident] = {"status": "published", "items": len(episodes), "featured": [titled(i) for i in favorite], "source": source, "file": name}
            success += 1
            print(f"{ident}: published {len(episodes)} episodes from {source}")
        except Exception as exc:
            report["shows"][ident] = {"status": "unavailable", "error": str(exc), "note": "Existing RSS file, if any, is retained unchanged."}
            print(f"WARNING {ident}: {exc}", file=sys.stderr)
    if all_featured:
        combined = make_feed(
            "Star Wars FFG — curated actual-play sampler",
            "An independently curated discovery sampler of audience-favorite Star Wars RPG shows. Episode picks are editorial or limited community signals, NOT a validated highest-rated episode chart. Original publishers host all audio.",
            "feed.xml", all_featured,
        )
        safe_write(HERE / "feed.xml", combined)
        report["combined"] = {"status": "published", "items": len(all_featured), "shows": success, "file": "feed.xml"}
        print(f"Combined sampler: {len(all_featured)} episodes from {success} shows")
    else:
        report["combined"] = {"status": "unavailable", "reason": "No usable original publisher audio"}
    safe_write(HERE / "status.json", (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return 0 if success > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
