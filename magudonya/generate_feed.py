#!/usr/bin/env python3
"""Curated Magudonya inspiration RSS, referencing original publisher audio only.

No recorded audio is downloaded, uploaded, modified or rehosted.
Each source is independent. Publication is atomic after aggregate validation.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HOME = Path(__file__).resolve().parent
CONFIG = json.loads((HOME / "catalog.json").read_text(encoding="utf-8"))
PUBLIC = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)
USER_AGENT = "Mozilla/5.0 (compatible; MagudonyaLoreFeed/1.0; +https://github.com/Quarky/shadowrunfeed)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"}

def norm(s):
    return re.sub(r"\s+", " ", (s or "").casefold()).strip()

def read_remote(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read(12_000_000)

def source_urls(source):
    urls = list(source.get("rss_candidates", []))
    if source.get("itunes_id"):
        try:
            endpoint = "https://itunes.apple.com/lookup?id=" + str(source["itunes_id"]) + "&entity=podcast"
            response = json.loads(read_remote(endpoint))
            for result in response.get("results", []):
                u = result.get("feedUrl", "")
                if u and u not in urls:
                    urls.append(u)
        except Exception as exc:
            print(f"  Apple lookup unavailable for {source['id']}: {exc}", file=sys.stderr)
    return urls

def fetch_rss(source):
    problems = []
    for url in source_urls(source):
        try:
            raw = read_remote(url)
            root = ET.fromstring(raw)
            channel = root.find("channel")
            if channel is None or len(channel.findall("item")) == 0:
                raise ValueError("No RSS channel items")
            print(f"Source {source['id']}: {len(channel.findall('item'))} items from {url}")
            return url, channel.findall("item")
        except Exception as exc:
            problems.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError("; ".join(problems) if problems else "No publisher RSS candidates")

def pub_date(item):
    raw = item.findtext("pubDate") or ""
    try:
        return parsedate_to_datetime(raw).timestamp()
    except (ValueError, TypeError, OverflowError):
        return 0.0

def resolved_length(enclosure):
    raw = enclosure.get("length", "")
    try:
        length = int(raw)
        if length > 0:
            return length
    except (TypeError, ValueError):
        pass
    url = enclosure.get("url", "")
    try:
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent":USER_AGENT})
        with urllib.request.urlopen(request, timeout=8) as response:
            n = int(response.headers.get("Content-Length", "0"))
            if n > 0:
                return n
    except Exception:
        pass
    return 0

def classify(title, source):
    t = norm(title)
    if any(norm(x) in t for x in CONFIG["exclude_title_terms"]):
        return []
    hits = [key for key, theme in CONFIG["themes"].items()
            if any(norm(word) in t for word in theme["terms"])]
    if source.get("default_theme") and source["default_theme"] not in hits:
        hits.append(source["default_theme"])
    return hits

def relevant(item, source):
    title = item.findtext("title") or ""
    description = item.findtext("description") or ""
    required = source.get("require_description_term")
    if required and norm(required) not in norm(title + " " + description):
        return None
    themes = classify(title, source)
    if not themes:
        return None
    low = norm(title)
    score = 2 * len(themes)
    for word in CONFIG["spotlight_terms"]:
        if norm(word) in low:
            score += 10
    if required:
        score += 3
    return score, themes

def curated_items(source, originals):
    selections = []
    rejected = {"not_relevant":0, "invalid_audio":0, "duplicated":0}
    seen = set()
    for item in originals:
        match = relevant(item, source)
        if not match:
            rejected["not_relevant"] += 1
            continue
        enc = item.find("enclosure")
        url = enc.get("url", "").strip() if enc is not None else ""
        if not url.startswith("https://") or not item.findtext("title"):
            rejected["invalid_audio"] += 1
            continue
        if url in seen:
            rejected["duplicated"] += 1
            continue
        seen.add(url)
        score, themes = match
        selections.append((score, pub_date(item), item, themes))
    selections.sort(key=lambda z: (z[0], z[1]), reverse=True)
    ready = []
    # Limit provider metadata probes and run HEAD checks in parallel so a
    # publisher that uses zero-length RSS enclosures cannot stall the workflow.
    candidates = selections[:source["limit"] * 3]
    with ThreadPoolExecutor(max_workers=10) as pool:
        lengths = list(pool.map(lambda candidate: resolved_length(candidate[2].find("enclosure")), candidates))
    for (score, publication, item, themes), length in zip(candidates, lengths):
        if len(ready) >= source["limit"]:
            break
        if length < 1:
            rejected["invalid_audio"] += 1
            continue
        ready.append({"score":score,"published":publication,"item":item,
                      "themes":themes,"length":length,"source":source})
    return ready, rejected

def child(parent, name, content):
    el = ET.SubElement(parent, name)
    el.text = str(content)
    return el

def artwork(output):
    from PIL import Image, ImageDraw, ImageFont
    size = 1600
    im = Image.new("RGB", (size,size), (12,21,34))
    d = ImageDraw.Draw(im)
    # Deliberately abstract, original graphic rather than borrowed podcast artwork.
    for i in range(8):
        pad = 105 + 75*i
        d.rounded_rectangle((pad,pad,size-pad,size-pad),radius=85,
                            outline=(48+i*8,91+i*6,103+i*4),width=4)
    d.line([(180,1190),(800,315),(1420,1190)],fill=(205,160,89),width=15)
    d.ellipse((655,450,945,740),outline=(205,160,89),width=15)
    d.line((800,290,800,1160),fill=(205,160,89),width=6)
    font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    try:
        font_path = next(p for p in font_paths if Path(p).exists())
        large=ImageFont.truetype(font_path,118)
        medium=ImageFont.truetype(font_path,56)
    except StopIteration:
        large=ImageFont.load_default()
        medium=ImageFont.load_default()
    # Solid text plate protects readability at podcast-thumbnail sizes.
    d.rounded_rectangle((85,1170,1515,1450),radius=32,fill=(12,21,34))
    d.text((800,1215),"MAGUDONYA",fill=(240,229,195),font=large,anchor="mt")
    d.text((800,1360),"FANTASY LORE LIBRARY",fill=(205,160,89),font=medium,anchor="mt")
    im.save(output,format="PNG",optimize=True)

def build_feed(filename, entries, label):
    root=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(root,"channel")
    child(channel,"title","Magudonya / Anomaly — " + label)
    child(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/magudonya")
    child(channel,"description","Independent curated fantasy worldbuilding inspiration for Magudonya / Anomaly GMs: creatures, culture, deities, planar mysteries and practical encounters. Not original-world canon; publisher-hosted recordings only. Source shows and episode credits retained.")
    child(channel,"language","en")
    child(channel,"copyright","Original episodes and audio remain copyright their respective publishers.")
    child(channel,f"{{{ITUNES}}}author","Magudonya GM listening index (independent curation)")
    child(channel,f"{{{ITUNES}}}summary","Curated links to original fantasy-lore podcast audio; not endorsed by creators.")
    child(channel,f"{{{ITUNES}}}type","episodic")
    ET.SubElement(channel,f"{{{ITUNES}}}image",{"href":PUBLIC+"cover.png"})
    ET.SubElement(channel,f"{{{ATOM}}}link",{"href":PUBLIC+filename,"rel":"self","type":"application/rss+xml"})
    # Podcast apps order by original broadcast dates, with source credit in the title.
    for entry in sorted(entries,key=lambda e:e["published"],reverse=True):
        item = entry["item"]; source = entry["source"]
        title = (item.findtext("title") or "").strip()
        url = item.find("enclosure").get("url")
        entry_id = hashlib.sha256((source["id"]+"\n"+url).encode()).hexdigest()
        dest=ET.SubElement(channel,"item")
        child(dest,"title",f"[{source['title']}] {title}")
        child(dest,"guid","magudonya-"+entry_id).set("isPermaLink","false")
        child(dest,"link",(item.findtext("link") or source["publisher_site"]).strip())
        desc=(item.findtext("description") or "").strip()
        # Keep short publisher show-note excerpt plus clear source credit.
        child(dest,"description",f"From {source['title']} — {source['publisher']}. Themes: {', '.join(entry['themes'])}. Original publisher episode: "+desc[:500])
        original_date=item.findtext("pubDate")
        if original_date:
            child(dest,"pubDate",original_date)
        ET.SubElement(dest,"enclosure",{"url":url,"length":str(entry["length"]),
                                      "type":item.find("enclosure").get("type","audio/mpeg") or "audio/mpeg"})
        for tag in ("duration","explicit"):
            value=item.findtext(f"{{{ITUNES}}}{tag}")
            if value:
                child(dest,f"{{{ITUNES}}}{tag}",value)
        source_xml=child(dest,"source",source["title"])
        source_xml.set("url",entry["source_rss"])
    ET.indent(root,space="  ")
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(xml)
    return xml

def main():
    all_entries=[]
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"state":"building",
            "sources":[],"feeds":{},"publisher_audio_rehosted":False,"warnings":[]}
    for source in CONFIG["sources"]:
        try:
            rss, originals=fetch_rss(source)
            items, skipped=curated_items(source, originals)
            if not items:
                raise ValueError("No suitable episodes with verifiable HTTPS enclosures")
            for entry in items:
                entry["source_rss"]=rss
            all_entries+=items
            report["sources"].append({"id":source["id"],"state":"included",
                                     "source_rss":rss,"episodes":len(items),"skipped":skipped})
        except Exception as exc:
            message=str(exc)
            print(f"WARNING: source {source['id']} omitted: {message}",file=sys.stderr)
            report["sources"].append({"id":source["id"],"state":"unavailable","reason":message[:600]})
            report["warnings"].append("Source skipped: "+source["id"])
    success_sources=sum(1 for s in report["sources"] if s["state"]=="included")
    if success_sources<3 or len(all_entries)<15:
        raise RuntimeError(f"Refusing to publish thin collection: {success_sources} sources; {len(all_entries)} episodes")
    # No duplicate publisher MP3 across source feeds.
    by_enclosure={}
    for entry in all_entries:
        url=entry["item"].find("enclosure").get("url")
        by_enclosure.setdefault(url,entry)
    all_entries=list(by_enclosure.values())
    contents={}
    main=build_feed("feed-v2.xml",all_entries,"Curated Lore & Creature Anthology")
    contents["feed-v2.xml"]=main
    contents["feed.xml"]=build_feed("feed.xml",all_entries,"Curated Lore & Creature Anthology")
    report["feeds"]["feed-v2.xml"]=len(all_entries)
    report["feeds"]["feed.xml"]=len(all_entries)
    for theme, file_name, title in [
        ("creatures","creatures.xml","Creatures & Ecology"),
        ("cultures","cultures.xml","Societies & Settlements"),
        ("magic","magic-planar.xml","Magic, Gods & Planes"),
        ("gm","worldbuilding.xml","Worldbuilding & GM Craft")]:
        selected=[e for e in all_entries if theme in e["themes"]]
        if selected:
            contents[file_name]=build_feed(file_name,selected,title)
            report["feeds"][file_name]=len(selected)
    artwork(HOME/"cover.png")
    for filename,data in contents.items():
        tmp=HOME/(filename+".tmp")
        tmp.write_bytes(data)
        tmp.replace(HOME/filename)
    report["state"]="published"
    report["total_episodes"]=len(all_entries)
    (HOME/"status.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("Published: "+str(report["feeds"])+" using original publisher audio")
if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("FEED BUILD FAILED: "+str(exc),file=sys.stderr)
        raise
