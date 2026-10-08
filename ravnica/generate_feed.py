#!/usr/bin/env python3
"""Build a separate, Ravnica-only podcast RSS from the original Unspoken Realms RSS.
No copyrighted audio is downloaded or rehosted. Errors leave the existing feed alone.
"""
import copy
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "catalog.json"
OUTPUT = HERE / "feed.xml"
PUBLIC_URL = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/ravnica/feed.xml"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)
ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")

def norm(s):
    return re.sub(r"\\s+", " ", s or "").strip().casefold()

def number_of(title):
    match = re.match(r"^\\s*episode\\s+(\\d+)\\b", title, re.IGNORECASE)
    return int(match.group(1)) if match else None

def get_feed(url):
    request = urllib.request.Request(url, headers={"User-Agent": "RavnicaPodcastCatalog/1.0 (+https://github.com/Quarky/shadowrunfeed)"})
    with urllib.request.urlopen(request, timeout=45) as response:
        root = ET.fromstring(response.read())
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Source is not an RSS feed with a channel")
    return root, channel

def main():
    manifest = json.loads(CATALOG.read_text(encoding="utf-8"))
    source = manifest["podcast_source"]
    errors = []
    for url in (source["rss"], source["alternate_rss"]):
        try:
            root, channel = get_feed(url)
            print(f"Fetched podcast RSS: {url} ({len(channel.findall('item'))} items)")
            break
        except Exception as e:
            errors.append(f"{url}: {type(e).__name__}: {e}")
    else:
        raise RuntimeError("Cannot retrieve publisher RSS. " + " | ".join(errors))

    original_items = channel.findall("item")
    selected = []
    used = set()
    missing = []
    for group in manifest["playlist_order"]:
        for selection in group["episodes"]:
            number = selection["episode_number"]
            candidates = [
                item for item in original_items
                if (number is not None and number_of(item.findtext("title") or "") == number)
                or (number is None and norm(selection.get("feed_match")) in norm(item.findtext("title")))
            ]
            # Guard against source episode-number collisions or mislabeled episodes.
            expected = selection["title"].split("—", 1)[-1].strip()
            expected_norm = norm(expected.replace("’", "'"))
            if number is not None:
                candidates = [it for it in candidates
                              if expected_norm in norm((it.findtext("title") or "").replace("’", "'"))]
            if len(candidates) != 1:
                missing.append(f"{group['id']}: {selection['title']} (matched {len(candidates)})")
                continue
            item = candidates[0]
            guid = (item.findtext("guid") or item.findtext("link") or item.findtext("title") or "").strip()
            enclosure = item.find("enclosure")
            if not guid or not enclosure or not enclosure.get("url", "").startswith("https://"):
                # HTTP URLs were used in older Libsyn RSS; media may be HTTP rather
                # than HTTPS, so allow http:// too, but never accept blank enclosures.
                if not guid or not enclosure or not enclosure.get("url", "").startswith(("https://", "http://")):
                    missing.append(f"{group['id']}: {selection['title']} (missing guid/audio)")
                    continue
            if guid in used:
                missing.append(f"{group['id']}: duplicate guid for {selection['title']}")
                continue
            used.add(guid)
            selected.append(copy.deepcopy(item))
    if missing:
        raise RuntimeError("Publisher RSS lacks required Ravnica recordings; refusing partial feed:\\n - " + "\\n - ".join(missing))
    if len(selected) != 36:
        raise RuntimeError(f"Expected exactly 36 unique episodes; got {len(selected)}")

    for item in list(channel.findall("item")):
        channel.remove(item)
    def settext(tag, value):
        node = channel.find(tag)
        if node is None:
            node = ET.SubElement(channel, tag)
        node.text = value
    settext("title", "Ravnica — Curated Magic Story Audio (Unspoken Realms)")
    settext("link", "https://github.com/Quarky/shadowrunfeed/tree/main/ravnica")
    settext("description", "Thirty-six curated Magic: The Gathering Ravnica audio-fiction recordings from Unspoken Realms. Original audio remains hosted by its creator. Commercial War of the Spark audiobooks are listed separately in the GitHub catalog.")
    settext(f"{{{ITUNES}}}type", "serial")
    for elem in list(channel.findall(f"{{{ATOM}}}link")):
        if elem.get("rel") == "self":
            channel.remove(elem)
    ET.SubElement(channel, f"{{{ATOM}}}link",
                  {"href": PUBLIC_URL, "rel": "self", "type": "application/rss+xml"})
    for item in selected:
        channel.append(item)

    ET.indent(root, space="  ")
    # Parse the serialization before touching the old feed.
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(xml)
    tmp = OUTPUT.with_suffix(".xml.tmp")
    tmp.write_bytes(xml)
    tmp.replace(OUTPUT)
    print(f"Published {OUTPUT}: 36 validated original-creator recordings (zero rehosted audio)")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
