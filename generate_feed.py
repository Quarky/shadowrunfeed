#!/usr/bin/env python3
import copy
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SOURCE = "https://anchor.fm/s/dac0dc50/podcast/rss"
OUTPUT = Path("feed.xml")
PUBLIC_FEED = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/feed.xml"

KEEP = (
    "Season 2 Episode 20 - Kami-Kaze",
    "Season 2 Episode 22 - Blood, Sweat & Stairs",
    "Season 2 Episode 23 - Directory Resistance",
    "Season 2 Episode 24 - Oh Bee-Have",
    "Season 2 Episode 25 - Traumatic Irony",
    "Season 2 Episode 26 - Emergency Boom",
)

# Preserve the common podcast namespaces with readable prefixes.
ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
ET.register_namespace("content", "http://purl.org/rss/1.0/modules/content/")
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("podcast", "https://podcastindex.org/namespace/1.0")

req = urllib.request.Request(
    SOURCE,
    headers={"User-Agent": "shadowrunfeed/1.0 (+https://github.com/Quarky/shadowrunfeed)"},
)
with urllib.request.urlopen(req, timeout=45) as r:
    data = r.read()

root = ET.fromstring(data)
channel = root.find("channel")
if channel is None:
    raise RuntimeError("Upstream RSS has no channel element")

items = list(channel.findall("item"))
kept = []
for item in items:
    title = (item.findtext("title") or "").strip()
    if any(marker in title for marker in KEEP):
        kept.append(item)

if len(kept) != len(KEEP):
    found = [(i.findtext("title") or "").strip() for i in kept]
    missing = [marker for marker in KEEP if not any(marker in title for title in found)]
    raise RuntimeError(f"Expected {len(KEEP)} Arcology episodes, found {len(kept)}. Missing: {missing}")

for item in items:
    channel.remove(item)

# Oldest first in the XML so this behaves like a compact story playlist.
kept.sort(key=lambda i: next((n for n, marker in enumerate(KEEP) if marker in (i.findtext("title") or "")), 999))
for item in kept:
    channel.append(item)

title = channel.find("title")
if title is not None:
    title.text = "SINless — Renraku Arcology Arc"

desc = channel.find("description")
if desc is not None:
    desc.text = (
        "A filtered fan playlist of the SINless Shadowrun actual-play episodes covering "
        "the Renraku Arcology storyline. Audio and episode metadata remain hosted by "
        "and credited to the original publisher, Critical Hits."
    )

link = channel.find("link")
if link is not None:
    link.text = "https://github.com/Quarky/shadowrunfeed"

# Remove upstream Atom self links, if present, and add one for the filtered feed.
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

tree = ET.ElementTree(root)
ET.indent(tree, space="  ")
tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
print(f"Wrote {OUTPUT} with {len(kept)} episodes")
# Workflow trigger marker
