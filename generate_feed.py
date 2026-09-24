#!/usr/bin/env python3
import copy
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from email.utils import parsedate_to_datetime

OUTPUT = Path("feed.xml")
PUBLIC_FEED = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/feed.xml"

SINLESS_MARKERS = (
    "Season 2 Episode 20 - Kami-Kaze",
    "Season 2 Episode 22 - Blood, Sweat & Stairs",
    "Season 2 Episode 23 - Directory Resistance",
    "Season 2 Episode 24 - Oh Bee-Have",
    "Season 2 Episode 25 - Traumatic Irony",
    "Season 2 Episode 26 - Emergency Boom",
)

EXTERNAL_SOURCES = [
    {
        "name": "Acceptable Losses",
        "url": "https://rss.buzzsprout.com/2533607.rss",
        "markers": (
            "Shadowrun's Most Horrifying Disaster: The Renraku Arcology",
        ),
        "expected": 1,
    },
    {
        "name": "Neo-Anarchist Podcast",
        "url": "https://neo-anarchist.libsyn.com/rss",
        "markers": (
            "Episode 30: 2060: Shutdown, Rogue AIs, Or'Zet & Orksploitation",
            "Episode 30: 2060: Shutdown, Rogue AIs, Or’Zet & Orksploitation",
            "2060: Shutdown, Rogue AIs, Or'Zet & Orksploitation",
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
        headers={"User-Agent": "shadowrunfeed/2.1 (+https://github.com/Quarky/shadowrunfeed)"},
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return ET.fromstring(r.read())

def pub_ts(item):
    text = (item.findtext("pubDate") or "").strip()
    try:
        return parsedate_to_datetime(text).timestamp()
    except Exception:
        return 0

if not OUTPUT.exists():
    raise RuntimeError("feed.xml is required as the preserved SINless base feed")

base_root = ET.parse(OUTPUT).getroot()
channel = base_root.find("channel")
if channel is None:
    raise RuntimeError("Existing feed.xml has no channel")

preserved = []
for item in channel.findall("item"):
    title = (item.findtext("title") or "").strip()
    if any(marker in title for marker in SINLESS_MARKERS):
        preserved.append(copy.deepcopy(item))

if len(preserved) != len(SINLESS_MARKERS):
    raise RuntimeError(
        f"Expected {len(SINLESS_MARKERS)} preserved SINless episodes, found {len(preserved)}"
    )

for item in list(channel.findall("item")):
    channel.remove(item)

all_items = preserved[:]
seen_guids = {
    (i.findtext("guid") or i.findtext("link") or i.findtext("title") or "").strip()
    for i in all_items
}

for source in EXTERNAL_SOURCES:
    root = fetch_xml(source["url"])
    src_channel = root.find("channel")
    if src_channel is None:
        raise RuntimeError(f'{source["name"]} RSS has no channel element')

    matched = []
    for item in src_channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        if any(marker in title for marker in source["markers"]):
            matched.append(copy.deepcopy(item))

    if len(matched) != source["expected"]:
        raise RuntimeError(
            f'{source["name"]}: expected {source["expected"]} matching episode(s), found {len(matched)}'
        )

    for item in matched:
        guid = (item.findtext("guid") or item.findtext("link") or item.findtext("title") or "").strip()
        if guid and guid not in seen_guids:
            seen_guids.add(guid)
            all_items.append(item)

title = channel.find("title")
if title is not None:
    title.text = "Shadowrun — Renraku Arcology Shutdown Audio Collection"

desc = channel.find("description")
if desc is not None:
    desc.text = (
        "A curated Renraku Arcology Shutdown audio collection: six SINless actual-play "
        "episodes, the long-form Acceptable Losses lore episode, and Neo-Anarchist Podcast "
        "Episode 30 covering the continuing Shutdown and rogue AIs. Audio remains hosted "
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
    {"href": PUBLIC_FEED, "rel": "self", "type": "application/rss+xml"},
)

tree = ET.ElementTree(base_root)
ET.indent(tree, space="  ")
tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
print(f"Wrote {OUTPUT} with {len(all_items)} episodes")
