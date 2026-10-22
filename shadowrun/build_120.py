#!/usr/bin/env python3
"""Independent Shadowrun 120-track editorial builder.
Publisher RSS controls audio metadata; no audio is mirrored or invented.
The existing feed.xml/feed-v2.xml files are immutable inputs.
"""
from __future__ import annotations
import collections, datetime as dt, email.utils, hashlib, html, json, re, time, urllib.request, uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "feed-v2.xml"
OUT = ROOT / "feed-v3.xml"
SELECTED = ROOT / "selected.json"
STATUS = ROOT / "status.json"
AT = "http://www.w3.org/2005/Atom"
IT = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("atom", AT)
ET.register_namespace("itunes", IT)
URL = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/shadowrun/feed-v3.xml"
BUILD = dt.datetime(2026, 10, 22, 12, 0, tzinfo=dt.timezone.utc)
SOURCES = {
    "The Program": ("story", "https://feeds.acast.com/public/shows/program", 17),
    "The Strata": ("story", "https://feeds.megaphone.fm/thestrata", 13),
    "The Dex Legacy": ("story", "https://feeds.megaphone.fm/thedexlegacy", 12),
    "Splintered Caravan": ("story", "https://splinteredcaravan.libsyn.com/rss", 8),
    "The Arcology Podcast AP": ("actual_play", "https://arcologypodcast.libsyn.com/rss", 16),
    "Shadowrun Origins": ("actual_play", "https://shadowrunorigins.libsyn.com/rss", 13),
    "Pink Fohawk": ("actual_play", "https://feed.podbean.com/pinkfohawk/feed.xml", 13),
    "Fandible Shadowrun": ("actual_play", "https://fandible.com/category/category-feed-list/shadowrun-feed/feed/", 12),
    "The Arcology Podcast lore": ("lore", "https://arcologypodcast.libsyn.com/rss", 5),
    "Neo-Anarchist Podcast": ("lore", "https://neo-anarchist.libsyn.com/rss", 4),
}
THEMES = {
    "ordinary life": ("worker", "resident", "friend", "family", "neighborhood", "street", "city", "night", "home", "care", "daily", "relationship"),
    "corporate control": ("corporat", "company", "job", "boss", "employee", "contract", "money", "pay", "security", "business", "executive", "office"),
    "matrix and autonomy": ("hacker", "hack", "decker", "matrix", "network", "system", "digital", "program", "artificial", "ai", "computer", "simulation"),
    "lockdown and survival": ("trapped", "surviv", "escape", "lock", "isolation", "prison", "siege", "shelter", "emergency", "door", "security"),
    "trust and resistance": ("resistan", "betray", "secret", "trust", "rebel", "conspir", "team", "crew", "ally", "choice", "loyal"),
    "surveillance and uncertain truth": ("monitor", "camera", "watch", "truth", "lie", "evidence", "identit", "myster", "memory", "spy", "detect"),
}
BLOCK = re.compile(r"(?i)(trailer|teaser|promo|preview|recap|outro|Q&A|behind the scenes|directors? commentary|announc|introducing:|presenting:|bonus|sponsor|interview|livestream|decompiling|show notes|after dark|\[intro\]|patreon exclusive|soundtrack|season finale discussion)")
SKIP = re.compile(r"(?i)(subscribe|follow us|follow the show|check out our|our patreon|support (?:the show|us)|learn more about your ad choices|written by|directed by|produced by|cast and crew|credits:)")
KEYWORD_LORE = re.compile(r"(?i)(shadowrun|2060|2059|matrix|deus|arcology|renraku|corporat|deck|cyberware|rigger|security|ai\b|technomanc|virtual|magic|ethic)")
def textnode(n, tag): return (n.findtext(tag) or "").strip()
def duration(raw):
    s = (raw or "").strip()
    if s.isdigit(): return int(s)
    try:
        parts = [int(i) for i in s.split(":")]
        if len(parts) == 3: return parts[0]*3600+parts[1]*60+parts[2]
        if len(parts) == 2: return parts[0]*60+parts[1]
    except ValueError: pass
    return 0
def fetch(url):
    error = None
    for trial in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"ShadowrunCampaignCurator/3.0 (publisher-linked catalog)"})
            with urllib.request.urlopen(req, timeout=35) as r:
                raw = r.read(12000000)
                if not raw: raise ValueError("empty RSS")
                root = ET.fromstring(raw)
                channel = root.find("channel")
                if channel is None: raise ValueError("not RSS2")
                return channel
        except Exception as exc:
            error = repr(exc)
            time.sleep(trial + 1)
    raise RuntimeError("publisher RSS unavailable " + url + ": " + str(error))
def plain(raw):
    p = re.sub(r"<[^>]+>", " ", html.unescape(raw or ""))
    p = re.sub(r"\s+", " ", p).strip()
    p = SKIP.split(p, 1)[0]
    return p[:850].strip()
def classify(title, summary):
    src = (title + " " + summary[:500]).lower()
    counts = [(sum(bool(re.search(re.escape(word), src)) for word in words), name) for name, words in THEMES.items()]
    counts.sort(reverse=True)
    return counts[0][1], counts[0][0]
def parse(channel, publisher, role):
    out = []
    for n in channel.findall("item"):
        title = textnode(n, "title")
        desc = plain(textnode(n, "description") or textnode(n, "{http://purl.org/rss/1.0/modules/content/}encoded"))
        e = n.find("enclosure")
        if e is None or not title: continue
        link = textnode(n, "link")
        media_url = (e.get("url") or "").strip()
        mime = (e.get("type") or "").lower()
        try: length = int(e.get("length") or "0")
        except ValueError: continue
        secs = duration(textnode(n, "{"+IT+"}duration"))
        guid = textnode(n, "guid")
        pub = textnode(n, "pubDate")
        try: timestamp = email.utils.parsedate_to_datetime(pub).timestamp()
        except Exception: timestamp = 0
        if not media_url.startswith("https://") or length <= 0 or not mime.startswith("audio/"): continue
        theme, hits = classify(title, desc)
        out.append({
            "publisher":publisher,"role":role,"title":title,"summary":desc,
            "source_link":link or media_url,"source_guid":guid or media_url,
            "audio_url":media_url,"audio_length":length,"audio_type":mime,
            "duration":textnode(n, "{"+IT+"}duration"),"seconds":secs,
            "source_published":pub,"published_epoch":timestamp,
            "theme":theme,"keyword_matches":hits,
            "transcript_status":"publisher_metadata_only",
            "editorial_basis":"Publisher episode synopsis and title; NOT a full transcript review",
        })
    return out
def choose(candidates, publisher, count, role, used_urls):
    # Mainline serialized works begin early and preserve intra-show chronology.
    # Lore instead ranks topic relevance, never adds generic talks as Arcology history.
    lst = [dict(x) for x in candidates if x["audio_url"] not in used_urls]
    if role == "actual_play" and publisher == "The Arcology Podcast AP":
        lst = [e for e in lst if "actual play" in e["title"].lower() and not BLOCK.search(e["title"])]
    elif publisher == "The Arcology Podcast lore":
        lst = [e for e in lst if "actual play" not in e["title"].lower()
               and KEYWORD_LORE.search(e["title"] + " " + e["summary"]) and not BLOCK.search(e["title"])]
    elif publisher == "Neo-Anarchist Podcast":
        lst = [e for e in lst if KEYWORD_LORE.search(e["title"] + " " + e["summary"]) and not BLOCK.search(e["title"])]
    elif publisher == "Pink Fohawk":
        lst = [e for e in lst if re.search(r"(?i)(^s[12]\b|season [12]|pink fohawk)",e["title"]) and not BLOCK.search(e["title"])]
    else:
        lst = [e for e in lst if not BLOCK.search(e["title"])]
    min_seconds = 900 if role == "story" else 1500 if role == "actual_play" else 600
    # Duration sometimes missing from a publisher's RSS; keep it explicitly unknown.
    lst = [e for e in lst if not e["seconds"] or e["seconds"] >= min_seconds]
    if role == "lore":
        lst.sort(key=lambda e:(-e["keyword_matches"],-e["published_epoch"],e["title"]))
    else:
        lst.sort(key=lambda e:(e["published_epoch"] or 1e12, e["title"]))
    if len(lst) < count:
        raise RuntimeError(f"Not enough eligible genuine audio for {publisher}: need {count}, got {len(lst)}")
    result = lst[:count]
    for e in result:
        if e["audio_url"] in used_urls: raise RuntimeError("duplicate audio enclosure " + e["title"])
        used_urls.add(e["audio_url"])
        e["review_status"] = "publisher_metadata_selected_not_transcript_validated"
        e["duration_exception"] = bool(e["seconds"] and e["seconds"] < 1800)
    return result
def weave(arrays):
    queues = [list(x) for x in arrays]
    result = []
    while any(queues):
        for q in queues:
            if q: result.append(q.pop(0))
    return result
def eput(node,name,value):
    child=ET.SubElement(node,name)
    child.text=str(value)
    return child
def rationale(e):
    topic=e["theme"]
    desc=e["summary"]
    # Public text is intentionally publisher-synopsis-grounded; no private campaign lore.
    summary = desc[:300].rsplit(" ", 1)[0].rstrip(".,;: ") if len(desc)>300 else desc
    statement = (f"Selected as {e['role'].replace('_',' ')} from {e['publisher']}, "
                 f"connecting {topic} to life inside a powerful, tightly controlled urban institution. "
                 f"The episode's published premise is: {summary}." if summary else
                 f"Selected for its {topic} perspective and the source series' cyberpunk storytelling.")
    focus = {
        "ordinary life":"Notice social routines, familiar places, minor obligations, and how ordinary relationships make later disruption matter.",
        "corporate control":"Notice job hierarchies, contractual leverage, personnel decisions, and consequences felt by workers rather than just executives.",
        "matrix and autonomy":"Notice who controls digital infrastructure, who trusts its outputs, and how characters respond to uncertain machine intentions.",
        "lockdown and survival":"Notice containment decisions, infrastructure dependencies, fears about exits, and the choices available to people caught inside.",
        "trust and resistance":"Notice alliances and broken promises, how decisions have interpersonal costs, and the difference between agency and compliance.",
        "surveillance and uncertain truth":"Notice what each witness knows, what systems record, and where evidence, inference and personal belief part ways."
    }[topic]
    if e["duration_exception"]: focus += " This is a deliberate under-30-minute exception, not a full-length recording."
    focus += " Evidence level: publisher synopsis and episode metadata; no full recording transcript has been audited."
    return statement,focus
def main():
    old_bytes = BASE.read_bytes()
    old_hash = hashlib.sha256(old_bytes).hexdigest()
    base_channel = ET.fromstring(old_bytes).find("channel")
    if base_channel is None: raise RuntimeError("Missing legacy source RSS")
    older = parse(base_channel,"Legacy Shadowrun","actual_play")
    sinless = [e for e in older if "SINless" in e["title"] and "Season 2" in e["title"]]
    neo = [e for e in older if "Episode 30:" in e["title"] and "Shutdown" in e["title"]]
    if len(sinless)!=6 or len(neo)!=1: raise RuntimeError(f"Legacy preservation gate: SINless {len(sinless)}, Neo {len(neo)}")
    used = set()
    for e in sinless + neo: used.add(e["audio_url"])
    for e in sinless + neo:
        e["publisher"] = "SINless" if e in sinless else "Neo-Anarchist Podcast"
        e["role"] = "actual_play" if e in sinless else "lore"
        e["review_status"] = "legacy_preserved_publisher_metadata"
        e["duration_exception"] = bool(e["seconds"] and e["seconds"]<1800)
    channels = {}
    for title,(role,url,need) in SOURCES.items():
        if url not in channels: channels[url] = fetch(url)
        print("RSS", title, url, "items", len(channels[url].findall("item")), flush=True)
    story_groups=[];play_groups=[];lore_groups=[]
    for title,(role,url,count) in SOURCES.items():
        candidates = parse(channels[url],title,role)
        items=choose(candidates,title,count,role,used)
        print("SELECT",role,title,len(items),flush=True)
        (story_groups if role=="story" else play_groups if role=="actual_play" else lore_groups).append(items)
    stories=weave(story_groups)
    plays=weave([[sinless[i] for i in range(6)]] + play_groups)
    lore=weave([[neo[0]]] + lore_groups)
    if list(map(len,[stories,plays,lore]))!=[50,60,10]:
        raise RuntimeError("120 weaving quotas not satisfied")
    sequence=[]
    for a,b in zip(stories[:10],plays[:10]): sequence.extend([a,b])
    for a,b in zip(lore,plays[10:20]): sequence.extend([a,b])
    for a,b in zip(plays[20:],stories[10:]): sequence.extend([a,b])
    if len(sequence)!=120 or len({x["audio_url"] for x in sequence})!=120:
        raise RuntimeError("Missing or duplicate episode")
    root=ET.Element("rss",version="2.0");channel=ET.SubElement(root,"channel")
    title="Shadowrun Shutdown - 120 Story, Actual Play and Lore Recordings"
    eput(channel,"title",title)
    eput(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/shadowrun")
    eput(channel,"description","A separate 120-entry Shadowrun and cyberpunk listening anthology. Publisher-hosted media and episode-specific listening notes; no content from this podcast is campaign canon. Existing Shadowrun subscription is preserved.")
    eput(channel,"language","en-us")
    eput(channel,"{"+IT+"}author","Shadowrun Shutdown Listening Catalog")
    eput(channel,"{"+IT+"}summary","Cyberpunk fiction, Shadowrun actual plays and context about network power, corporate everyday life, containment and resistance.")
    eput(channel,"{"+IT+"}explicit","true")
    eput(channel,"{"+IT+"}type","episodic")
    ET.SubElement(channel,"{"+IT+"}category",text="Leisure")
    ET.SubElement(channel,"{"+AT+"}link",rel="self",href=URL,type="application/rss+xml")
    eput(channel,"lastBuildDate",email.utils.format_datetime(BUILD,usegmt=True))
    for n,e in enumerate(sequence,1):
        why,focus=rationale(e);e["position"]=n;e["public_reason"]=why;e["public_focus"]=focus
        node=ET.SubElement(channel,"item")
        eput(node,"title",f"{n:03d} - {e['role'].replace('_',' ').upper()} - {e['publisher']} - {e['title']}")
        eput(node,"link",e["source_link"])
        eput(node,"description",f"WHY SELECTED: {why}\n\nLISTENING FOCUS: {focus}")
        guid=eput(node,"guid","urn:uuid:"+str(uuid.uuid5(uuid.NAMESPACE_URL,"shadowrun:120:v3:"+e["audio_url"])))
        guid.set("isPermaLink","false")
        eput(node,"pubDate",email.utils.format_datetime(BUILD-dt.timedelta(minutes=n),usegmt=True))
        ET.SubElement(node,"enclosure",url=e["audio_url"],length=str(e["audio_length"]),type=e["audio_type"])
        eput(node,"{"+IT+"}episode",n)
        eput(node,"{"+IT+"}episodeType","full")
        if e["duration"]:eput(node,"{"+IT+"}duration",e["duration"])
    payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    # Re-parse the actual written format, not just intermediate dictionaries.
    check=ET.fromstring(payload).find("channel").findall("item")
    if len(check)!=120 or len({x.findtext("guid") for x in check})!=120:raise RuntimeError("Invalid final RSS")
    if BASE.read_bytes()!=old_bytes:raise RuntimeError("Legacy feed mutated")
    OUT.write_bytes(payload)
    SELECTED.write_text(json.dumps(sequence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    report={"edition":"Shadowrun V3 120","state":"source_metadata_curation_published_candidate",
      "total":120,"roles":{"story":50,"actual_play":60,"lore":10},
      "source_count":len({e["publisher"] for e in sequence}),
      "full_transcripts_examined":0,"publisher_metadata_only":120,
      "below_30_minutes":sum(x["duration_exception"] for x in sequence),
      "unknown_duration":sum(not x["seconds"] for x in sequence),
      "baseline_feed_sha256_unchanged":old_hash,
      "external_Podbean_import_tested":False,
      "note":"Publisher metadata audit is NOT a completed transcript-first scene audit; future transcript passes must revise selection."}
    STATUS.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("VALID RSS 120",report["roles"],"publishers",report["source_count"],"short",report["below_30_minutes"])
if __name__ == "__main__": main()
