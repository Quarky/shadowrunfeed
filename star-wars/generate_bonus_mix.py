#!/usr/bin/env python3
"""Build the twenty publisher-hosted scripted-fiction and tabletop inspiration picks.

Public thematic analogies only: no private campaign canon or copied recordings.
Exactly five dramas and five actual plays for each of the two ordered themes.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from generate_learning import HERE, ITUNES, ATOM, url_bytes, verified_episode

CFG = json.loads((HERE / "bonus-20-catalog.json").read_text(encoding="utf-8"))
PUBLIC = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)

def cleaned(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").casefold()).strip()

def publisher_feed(apple_id):
    q = urllib.parse.urlencode({"id": int(apple_id), "entity": "podcast", "country": "us"})
    lookup = json.loads(url_bytes("https://itunes.apple.com/lookup?" + q))
    results = [r for r in lookup.get("results", []) if r.get("collectionId") == int(apple_id) and r.get("feedUrl")]
    if len(results) != 1:
        raise ValueError("Publisher feed unavailable in iTunes lookup: " + str(apple_id))
    rss = results[0]["feedUrl"]
    feed = ET.fromstring(url_bytes(rss))
    channel = feed.find("channel")
    if feed.tag != "rss" or channel is None:
        raise ValueError("Publisher did not return RSS: " + str(apple_id))
    return rss, channel.findall("item")

def match(row, rss, items):
    terms = [cleaned(term) for term in row["terms"]]
    candidates = []
    excluded = (" trailer ", " teaser ", " preview ", " behind the scenes ", " interview ",
                " discussion ", " episode recap ", " bonus episode ", " character creation ",
                " behind the mic ", " announcement ", " cast chat ", " director commentary ", " commentary on ", " commentary ",
                " behind the scenes ", " q and a ", " recap ", " making of ")
    for item in items:
        title = item.findtext("title") or ""
        normalized = " " + cleaned(title) + " "
        if any(stop in normalized for stop in excluded):
            continue
        found = [(n, term) for n,term in enumerate(terms) if term and (" " + term + " ") in normalized]
        if found:
            best = min(n for n,_ in found)
            candidates.append((best, -max(len(t) for _,t in found), len(title), item))
    candidates.sort(key=lambda x: x[:3])
    for _,_,_,item in candidates[:12]:
        verified = verified_episode(item)
        if verified is not None:
            return verified
    sample = [i.findtext("title") for i in items[:8]]
    raise ValueError("No source-verified playable title matched " + repr(row["terms"]) + "; feed samples=" + repr(sample)[:350])

def put(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = str(value)
    return el

def build():
    entries = CFG["entries"]
    if len(entries) != 20 or len({r["show"] for r in entries}) != 20:
        raise RuntimeError("Require exactly twenty distinct audio programs")
    if [r["kind"] for r in entries] != ["DRAMA", "ACTUAL_PLAY"] * 10:
        raise RuntimeError("Require exactly ten dramas alternating with ten actual plays")
    if [r["theme"] for r in entries] != ["moraband"] * 10 + ["shard-moon"] * 10:
        raise RuntimeError("Require ten Moraband, then ten Shard Moon selections")
    root = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(root, "channel")
    put(ch, "title", "Star Wars RPG — Moraband and Shard Moon Dramatic Listening")
    put(ch, "link", "https://github.com/Quarky/shadowrunfeed/tree/main/star-wars")
    put(ch, "language", "en")
    put(ch, "description", "Twenty distinct non-Star-Wars scripted dramas and RPG actual plays: 10 Moraband-like ancient mysteries, then 10 Shard Moon-like remote scientific and survival stories, five of each format per theme. Cross-genre inspiration, not Star Wars lore.")
    put(ch, f"{{{ITUNES}}}author", "Independent RPG Listening Index")
    put(ch, f"{{{ITUNES}}}type", "episodic")
    ET.SubElement(ch, f"{{{ITUNES}}}image", {"href": PUBLIC + "cover.png"})
    ET.SubElement(ch, f"{{{ATOM}}}link", {"href": PUBLIC + "bonus-20.xml", "rel": "self", "type": "application/rss+xml"})
    feeds = {}
    rows = []
    used_media = set()
    for n, row in enumerate(entries, 1):
        rss_items = feeds.get(row["apple_id"])
        if rss_items is None:
            rss_items = publisher_feed(row["apple_id"])
            feeds[row["apple_id"]] = rss_items
        rss, items = rss_items
        original = match(row, rss, items)
        enc = original.find("enclosure")
        url = enc.get("url")
        # Ignore time-limited CDN access signatures when ensuring identity.
        parsed = urllib.parse.urlsplit(url)
        identity = parsed.netloc.casefold() + urllib.parse.unquote(parsed.path).casefold()
        if identity in used_media:
            raise RuntimeError("Repeated publisher recording: " + row["show"])
        used_media.add(identity)
        title = original.findtext("title") or ""
        item = ET.SubElement(ch, "item")
        put(item, "title", f"{n:02d} · CROSS-GENRE {row['kind']} · [{row['show']}] {title}")
        digest = hashlib.sha256((str(row["apple_id"]) + "|" + cleaned(title)).encode()).hexdigest()
        guid = put(item, "guid", "urn:sw-bonus-20:" + digest)
        guid.set("isPermaLink", "false")
        page = original.findtext("link") or rss
        put(item, "link", page)
        desc = (original.findtext("description") or "")[:350]
        publication = original.findtext("pubDate") or ""
        put(item, "description", "NON-STAR-WARS CROSS-GENRE " + row["kind"] + ". " + row["learning"] + " Not Star Wars canon. Original release: " + publication + ". Publisher synopsis: " + desc)
        put(item, "pubDate", publication or "Mon, 01 Jan 2024 00:00:00 +0000")
        ET.SubElement(item, "enclosure", {"url": url, "length": enc.get("length"), "type": enc.get("type") or "audio/mpeg"})
        duration = original.findtext(f"{{{ITUNES}}}duration")
        if duration:
            put(item, f"{{{ITUNES}}}duration", duration)
        src = put(item, "source", row["show"])
        src.set("url", rss)
        rows.append({"selection": n, "theme": row["theme"], "kind": row["kind"],
                     "show": row["show"], "episode": title, "episode_url": page,
                     "publisher_rss": rss, "publisher_audio_url": url,
                     "creative_use": row["learning"], "star_wars_setting": False,
                     "original_publication": publication})
    if len(rows) != 20 or len(used_media) != 20:
        raise RuntimeError("Selection count or unique audio mismatch")
    ET.indent(root, space="  ")
    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.fromstring(xml)
    report = {"state":"published","generated_utc":datetime.now(timezone.utc).isoformat(),
              "count":20,"moraband_count":10,"shard_moon_count":10,"drama_count":10,
              "actual_play_count":10,"unique_productions":20,
              "all_cross_genre":True,"original_recordings_rehosted":False,"warnings":[]}
    notes = ["# Twenty new Moraband → Shard Moon audio stories and actual plays", "",
             "These twenty recordings follow the existing ninety episodes of the originally subscribed Star Wars RPG feed. Ten scripted fiction dramas and ten tabletop actual plays from twenty different productions. First ten: ancient Sith/occult-ruins analogies; next ten: isolated-world science, alien ecology, facilities and survival. Every addition is **cross-genre inspiration, not Star Wars canon**. The private adventure's specific plot and secrets are not represented as source-show claims.", "",
             "| Position in new group | Theme | Kind | Playable episode | Creative use |",
             "| ---: | --- | --- | --- | --- |"]
    for row in rows:
        title = row["episode"].replace("|","–")
        notes.append(f'| {row["selection"]} | {row["theme"]} | {row["kind"]} | [{title}]({row["episode_url"]}) — {row["show"]} | {row["creative_use"]} |')
    notes += ["", "**Original audio is never copied or hosted by this project.** Each RSS enclosure remains the original publisher's recording.", ""]
    output = {
        "bonus-20.xml": xml,
        "bonus-20-episodes.json": (json.dumps({"generated_utc":report["generated_utc"],"episodes":rows},indent=2,ensure_ascii=False)+"\n").encode(),
        "bonus-20-episodes.md": "\n".join(notes).encode(),
        "bonus-20-status.json": (json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode(),
    }
    for name, content in output.items():
        path=HERE/name
        temp=path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(path)
    print("VERIFIED: twenty distinct publisher-hosted recordings (10 dramas, 10 actual plays)")

if __name__ == "__main__":
    build()
