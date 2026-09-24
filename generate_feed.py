#!/usr/bin/env python3
import copy
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from email.utils import parsedate_to_datetime

OUTPUT = Path("feed.xml")
PUBLIC_FEED = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/feed.xml"

SOURCES = [
    {
        "name": "SINless",
        "url": "https://anchor.fm/s/dac0dc50/podcast/rss",
        "markers": (
            "Season 2 Episode 20 - Kami-Kaze",
            "Season 2 Episode 22 - Blood, Sweat & Stairs",
            "Season 2 Episode 23 - Directory Resistance",
            "Season 2 Episode 24 - Oh Bee-Have",
            "Season 2 Episode 25 - Traumatic Irony",
            "Season 2 Episode 26 - Emergency Boom",
        ),
    },
    {
        "name": "Acceptable Losses",
        "url": "https://rss.buzzsprout.com/2533607.rss",
        "markers": (
            "Shadowrun's Most Horrifying Disaster: The Renraku Arcology",
        ),
    },
    {
        "name": "Neo-Anarchist Podcast",
        "url": "https://neo-anarchist.libsyn.com/rss",
        "markers": (
            "Episode 30: 2060: Shutdown, Rogue AIs, Or'Zet & Orksploitation",
            "Episode 30: 2060: Shutdown, Rogue AIs, Or’Zet & Orksploitation",
        ),
        "expected": 1,
    },
]

ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/")
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("podcast", "https://podcastindex.org/namespace/1.0")

def fetch_xml(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "shadowrunfeed/2.0 (+https://github.com/Quarky/shadowrunfeed)"},
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return ET.fromstring(r.read())

def pub_ts(item):
    text = (item.findtext("pubDate") or "").strip()
    try:
        return parsedate_to_datetime(text).timestamp()
    except Exception:
        return 0

base_root = None
all_items = []
seen_guids = set()

for source in SOURCES:
    root = fetch_xml(source["url"])
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError(f'{source["name"]} RSS has no channel element')

    if base_root is None:
        base_root = root
        base_channel = channel
        for item in list(base_channel.findall("item")):
            base_channel.remove(item)

    matched = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        if any(marker in title for marker in source["markers"]):
            matched.append(copy.deepcopy(item))

    expected = source.get("expected", len(source["markers"]))
    if len(matched) != expected:
        titles = [(i.findtext("title") or "").strip() for i in channel.findall("item")]
        raise RuntimeError(
            f'{source["name"]}: expected {expected} matching episode(s), found {len(matched)}. '
            f'Markers: {source["markers"]}'
        )

    for item in matched:
        guid = (item.findtext("guid") or item.findtext("link") or item.findtext("title") or "").strip()
        if guid in seen_guids:
            continue
        seen_guids.add(guid)
        all_items.append(item)

if base_root is None:
    raise RuntimeError("No RSS sources loaded")

channel = base_root.find("channel")
title = channel.find("title")
if title is not None:
    title.text = "Shadowrun — Renraku Arcology Shutdown Audio Collection"

desc = channel.find("description")
if desc is not None:
    desc.text = (
        "A curated audio collection for the Renraku Arcology Shutdown: "
        "SINless actual-play Arcology episodes plus lore/history episodes from "
        "Acceptable Losses and the Neo-Anarchist Podcast. Audio remains hosted "
        "by and credited to the original publishers."
    )

link = channel.find("link")
if link is not None:
    link.text = "https://github.com/Quarky/shadowrunfeed"

all_items.sort(key=pub_ts)
for item in all_items:
    channel.append(item)

ATOM_LINK = "{http://www.w3.org/2005/Atom}link"
for node in list(channel.findall(ATOM_LINK)):
    if node.attrib.get("rel") == "self":
        channel.remove(node)
ET.SubElement(
    channel,
    ATOM_LINK,
    {
        "href": PUBLIC_FEED,
        "rel": "self",
        "type": "application/rss+xml",
    },
)

tree = ET.ElementTree(base_root)
ET.indent(tree, space="  ")
tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
print(f"Wrote {OUTPUT} with {len(all_items)} episodes")
