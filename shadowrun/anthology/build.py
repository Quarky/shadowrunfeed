#!/usr/bin/env python3
"""Build the Shadowrun anthology from ORIGINAL publisher RSS, failing closed on missing media.

Independent of root feed-v2.xml and the Anomaly feeds. No files from any other
campaign are used as episodes. Requires Pillow for the original cover image.
"""
from __future__ import annotations
import collections
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
POLICY = json.loads((HERE / "policy.json").read_text(encoding="utf-8"))
IT = "http://www.itunes.com/dtds/podcast-1.0.dtd"
AT = "http://www.w3.org/2005/Atom"
DC = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("itunes", IT)
ET.register_namespace("atom", AT)
U = POLICY["subscription"]
STAMP = dt.datetime(2026, 10, 22, 11, 0, tzinfo=dt.timezone.utc)
IGNORE = re.compile(r"\b(trailer|teaser|preview|patreon|bonus|q\s*&\s*a|re-cap|recap|announcement|introducing:|after dark|behind the scenes|outtakes|blooper|promo|advertisement|feed drop|sneak peek|transcript only|production update|introduction|studio update|special announcement|sixth edition box set)\b", re.I)
PROMO = re.compile(r"(?i)\b(?:support us on|support the show|follow us on|find us on|follow the show|our patreon|join our discord|check out our|sponsored by|advertising inquiries|credits:|learn more about your ad choices|click here to)\b")
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
cache = {}
report = {"source_fetch": {}, "source_inventory": {}, "short_exceptions": [],
          "transcripts_examined_full": 0, "audio_playback_tested": False,
          "podbean_import_tested": False, "edition": "anthology_v1"}

def clean(value: str, n=500) -> str:
    s = html.unescape(TAG.sub(" ", value or ""))
    s = re.sub(r"https?://\S+", "", s)
    s = PROMO.split(s, 1)[0]
    return WS.sub(" ", s).strip()[:n]

def sec(value: str) -> int:
    if not value:
        return 0
    value = value.strip()
    try:
        if value.isdigit():
            return int(value)
        parts = [int(x) for x in value.split(":")]
        if len(parts) == 2:
            return parts[0]*60 + parts[1]
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
    except (TypeError, ValueError):
        pass
    return 0

def date(value):
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return dt.datetime(1970,1,1,tzinfo=dt.timezone.utc)

def fetch(feed):
    if feed not in cache:
        req = urllib.request.Request(feed, headers={
            "User-Agent":"ShadowrunPodcastAnthology/1.0 (+https://github.com/Quarky/shadowrunfeed)",
            "Accept":"application/rss+xml, application/xml, text/xml, */*"})
        error = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=50) as response:
                    body = response.read(32_000_000)
                channel = ET.fromstring(body).find("channel")
                if channel is None:
                    raise ValueError("Not a podcast RSS2 channel")
                cache[feed] = channel.findall("item")
                report["source_fetch"][feed] = {"ok":True,"items":len(cache[feed])}
                break
            except Exception as exc:
                error = exc
        if feed not in cache:
            report["source_fetch"][feed] = {"ok":False,"error":str(error)[:250]}
            cache[feed] = []
    return cache[feed]

def probe_original_audio_length(url):
    """Obtain length from original-host HTTP response, not an estimate."""
    options=[url]
    # Podtrac prefixes in official Megaphone enclosures often publish
    # length="0". Request the underlying publisher-hosted Megaphone MP3
    # headers without changing the enclosure URL distributed to listeners.
    direct=re.search(r"(traffic\.megaphone\.fm/[A-Za-z0-9_-]+\.mp3)",url)
    if direct:
        options.insert(0,"https://"+direct.group(1))
    for target in options:
        for method in ("HEAD","GET"):
            headers={"User-Agent":"ShadowrunPodcastAnthology/1.0"}
            if method=="GET":
                headers["Range"]="bytes=0-0"
            try:
                req=urllib.request.Request(target,headers=headers,method=method)
                with urllib.request.urlopen(req,timeout=18) as response:
                    content_range=response.headers.get("Content-Range","")
                    match=re.search(r"/(\d+)$",content_range)
                    if match and int(match.group(1))>0:
                        return int(match.group(1))
                    length=int(response.headers.get("Content-Length") or 0)
                    if length>100000:
                        return length
                    if method=="GET":
                        response.read(1)
            except Exception:
                pass
    return 0

def make_record(item, publisher, feed, role, pinned=False):
    title = clean(item.findtext("title") or "",250)
    e = item.find("enclosure")
    if not title or e is None:
        return None
    url = html.unescape(e.attrib.get("url") or "").strip()
    mime = (e.attrib.get("type") or "").lower().strip()
    try:
        size = int(e.attrib.get("length") or "0")
    except ValueError:
        size = 0
    if size<=0 and "traffic.megaphone.fm/" in url:
        size=probe_original_audio_length(url)
    if not url.startswith("https://") or size <= 0 or not mime.startswith("audio/"):
        return None
    published = date(item.findtext("pubDate") or "")
    if published > STAMP:
        return None
    duration = (item.findtext("{"+IT+"}duration") or "").strip()
    intro = (item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "")
    summary = clean(intro, 540)
    if not pinned and IGNORE.search(title):
        return None
    if not pinned and len(title)<5:
        return None
    rec = {
        "publisher":publisher, "title":title,"role":role,
        "url":url, "size":size, "mime":mime,
        "publisher_link":(item.findtext("link") or url).strip(),
        "publisher_guid":(item.findtext("guid") or "").strip(),
        "publisher_rss":feed, "original_date":published.isoformat(),
        "duration":duration, "seconds":sec(duration),
        "publisher_summary":summary, "evidence":"publisher_metadata_only",
        "pinned_baseline":pinned
    }
    return rec

def baseline():
    # Read the previously published Arcology-only edition, unchanged.
    channel = ET.parse(ROOT / "feed-v2.xml").getroot().find("channel")
    got = {"actual_play":[], "lore":[]}
    for item in channel.findall("item"):
        name = item.findtext("title") or ""
        if "SINless" in name and "Season 2 Episode" in name:
            role,publisher,original_feed = "actual_play","SINless","https://github.com/Quarky/shadowrunfeed/blob/main/feed-v2.xml"
        elif "2060: Shutdown" in name:
            role,publisher,original_feed = "lore","Neo-Anarchist Podcast","https://neo-anarchist.libsyn.com/rss"
        elif "Acceptable Losses" in name or "Horrifying Disaster" in name or "Renraku Arcology" in name:
            role,publisher,original_feed = "lore","Acceptable Losses","https://rss.buzzsprout.com/2533607.rss"
        else:
            continue
        obj=make_record(item,publisher,original_feed,role,pinned=True)
        if not obj:
            raise ValueError("Baseline item is missing an HTTPS positive-length enclosure: "+name)
        got[role].append(obj)
    if len(got["actual_play"])!=6 or len(got["lore"])!=2:
        raise ValueError("Preserved Shadowrun baseline must be 6 SINless AP plus 2 lore; got "+repr({k:len(v) for k,v in got.items()}))
    return got

def fit_score(item, role):
    txt = (item["title"]+" "+item["publisher_summary"]).lower()
    kws = sum(2 if keyword in txt else 0 for theme in POLICY["themes"] for keyword in theme["keywords"])
    if role=="lore" and re.search(r"\b(renraku|arcology|shutdown|matrix|seattle|205[0-9]|2060|corporat|cyberware|security)\b",txt):
        kws += 12
    if item["seconds"] >= 3600:
        kws += 4
    elif item["seconds"] >= 1800:
        kws += 2
    elif item["seconds"] and item["seconds"] < 600:
        kws -= 4
    if not item["publisher_summary"]:
        kws -= 10
    return kws

def gather(role, selected):
    sources = POLICY["source_policy"][role]
    all_pools = []
    for spec in sources:
        records=[]
        raw_items=fetch(spec["rss"])
        if spec["key"]=="strata":
            raw_items=sorted(raw_items,key=lambda x:date(x.findtext("pubDate") or ""))
        for item in raw_items:
            rec=make_record(item,spec["name"],spec["rss"],role)
            if not rec:
                continue
            title=rec["title"].lower()
            if "include" in spec:
                pat=spec["include"]
                target=title if role=="actual_play" else (title+" "+rec["publisher_summary"].lower())
                if not re.search(pat,target,re.I):
                    continue
            if "exclude" in spec and re.search(spec["exclude"],title,re.I):
                continue
            if spec["key"]=="origins" and not re.search(r"shadowrun origins:\s*episode\s*\d+", rec["title"], re.I):
                # Do not misclassify a rulebook/product special as the next
                # chapter of an actual-play serial. Retain genuine short AP.
                continue
            if spec["key"]=="neo":
                year=re.search(r"\b(20\d\d)[a-z]?:", title)
                if year and int(year.group(1))>2061:
                    continue
            if spec["key"]=="arcology_lore" and re.search(r"syrinscape|gencon|boxed set|character optimization|product review|kickstarter|podcast meetup|meet and greet|game review|dice bag",title,re.I):
                continue
            records.append(rec)
            if spec["key"]=="strata" and len(records)>=spec["target"]+5:
                # Oldest complete story arc first; avoid probing an entire
                # 160-track syndicated feed for metadata-only discovery.
                break
        if spec["sort"]=="relevance":
            records.sort(key=lambda x:(-fit_score(x,role),x["original_date"],x["title"]))
        else:
            records.sort(key=lambda x:(x["original_date"],x["title"]))
        report["source_inventory"][spec["key"]] = {"candidate_episodes":len(records),"target":spec["target"],"role":role}
        if not records:
            report.setdefault("empty_source_samples", {})[spec["key"]] = [
                {"title":(i.findtext("title") or "")[:100],
                 "pubDate":i.findtext("pubDate"),
                 "duration":i.findtext("{"+IT+"}duration"),
                 "enclosure":(i.find("enclosure").attrib if i.find("enclosure") is not None else None)}
                for i in fetch(spec["rss"])[:3]
            ]
        all_pools.append((spec,records))
    used_urls={x["url"] for x in selected}
    used_guids={x["publisher_guid"] for x in selected if x["publisher_guid"]}
    candidates=collections.defaultdict(list)
    for spec,records in all_pools:
        candidates[spec["key"]]=[r for r in records if r["url"] not in used_urls and (not r["publisher_guid"] or r["publisher_guid"] not in used_guids)]
    chosen = []
    def take(spec,records,n):
        count=0
        for rec in records:
            if count>=n:
                break
            if rec["url"] in used_urls or (rec["publisher_guid"] and rec["publisher_guid"] in used_guids):
                continue
            used_urls.add(rec["url"])
            if rec["publisher_guid"]: used_guids.add(rec["publisher_guid"])
            chosen.append(rec)
            count+=1
        return count
    # Use 30+ minute episodes preferentially while honoring per-publisher quotas;
    # short stories can enter as explicit exceptions if no longer choices exist.
    for spec,records in all_pools:
        if spec["sort"]=="chronological" and spec["key"] in ("strata","cosmiko","ink","origins","arcology","fohawk"):
            # Never jump into a serial's later chapter merely because it exceeds
            # a duration threshold; maintain episode chronology for listeners.
            n=take(spec,records,spec["target"])
        else:
            longer=[x for x in records if x["seconds"]>=1800]
            shorter=[x for x in records if 0<x["seconds"]<1800]
            unknown=[x for x in records if x["seconds"]==0]
            n=take(spec,longer,spec["target"])
            if n<spec["target"]: n+=take(spec,shorter,spec["target"]-n)
            if n<spec["target"]: n+=take(spec,unknown,spec["target"]-n)
    # Fill shortfalls with already-audited publisher RSS items; never fabricate
    # a "120-track" result by duplicating enclosures.
    needed=POLICY["roles"][role]-len(selected)-len(chosen)
    if needed>0:
        rest=sorted((x for spec,rs in all_pools for x in rs if x["url"] not in used_urls),key=lambda x:-fit_score(x,role))
        take({"key":"fill"},rest,needed)
    return chosen

def reorder(items):
    # Keep each publisher's own narrative order and weave publishers,
    # instead of presenting an entire long serial before changing voices.
    groups=collections.defaultdict(collections.deque)
    for e in items:
        groups[e["publisher"]].append(e)
    result=[]
    previous=None
    while any(groups.values()):
        choices=[(name,group) for name,group in groups.items() if group]
        name,group=max(choices,key=lambda pair:(pair[0]!=previous,len(pair[1]),pair[0]))
        result.append(group.popleft())
        previous=name
    return result

def theme_for(e):
    combined=(e["title"]+" "+e["publisher_summary"]).lower()
    scores=[sum(1 for word in t["keywords"] if word in combined) for t in POLICY["themes"]]
    best=max(range(len(scores)),key=lambda i:scores[i])
    return POLICY["themes"][best]["id"], POLICY["themes"][best]["label"],scores[best]

def explain(e):
    theme,label,matches=theme_for(e)
    e["theme"]=theme
    if e["seconds"] and e["seconds"]<1800:
        report["short_exceptions"].append({"slot":e["slot"],"publisher":e["publisher"],"title":e["title"],"minutes":round(e["seconds"]/60,1)})
    specificity = "The publisher synopsis includes elements relevant to this listening theme." if matches else "The thematic link is a curator's broad comparison, not a claim about the recording's exact scenes."
    role_focus={
        "story":"Listen to how individuals speak, negotiate and make choices inside a larger system, and how ordinary routines acquire dramatic pressure.",
        "actual_play":"Listen for how the GM presents a lived-in environment, how player decisions affect bystanders, and how obstacles develop without dictating character choices.",
        "lore":"Listen for institutions, technology and competing historical perspectives; this publisher's setting details are reference material, not this campaign's established events."
    }[e["role"]]
    synopsis=e["publisher_summary"] or "No usable publisher synopsis was available; the original episode title and audio metadata were confirmed."
    why=("Selected from "+e["publisher"]+" for the anthology's "+label+" strand. "+
         specificity+" "+role_focus)
    if e["seconds"] and e["seconds"]<1800:
        why+=" This is shorter than the normal thirty-minute preference and is retained as a documented short-form exception."
    if e["pinned_baseline"]:
        why+=" This recording belongs to the preserved eight-episode Arcology listening baseline."
    e["why"]=why
    e["focus"]="Publisher episode description: "+synopsis[:440]+"."
    return ("WHY SELECTED: "+why+"\n\nWHAT TO LISTEN FOR: "+e["focus"]+
            "\n\nEVIDENCE: Original publisher RSS title, synopsis and HTTPS enclosure only. "+
            "No complete transcript or full audio playback has been examined for this selection. "+
            "Outside fiction is not established campaign canon.")

def put(p,tag,text):
    node=ET.SubElement(p,tag)
    node.text=str(text)
    return node

def draw_cover():
    im=Image.new("RGB",(1400,1400),(10,17,28))
    d=ImageDraw.Draw(im)
    for y in range(1400):
        shade=int(10+22*y/1400)
        d.line((0,y,1400,y),fill=(8,shade,27+int(18*y/1400)))
    for x in range(50,1400,90):
        d.line((x,0,x,1400),fill=(22,52,60),width=2)
    for y in range(50,1400,90):
        d.line((0,y,1400,y),fill=(22,52,60),width=2)
    d.rounded_rectangle((82,110,1318,1288),radius=38,outline=(43,211,198),width=12)
    d.rectangle((130,310,1270,319),fill=(237,98,72))
    d.rectangle((130,1102,1270,1111),fill=(237,98,72))
    fonts=["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    def font(size):
        for path in fonts:
            try:return ImageFont.truetype(path,size)
            except OSError:pass
        return ImageFont.load_default()
    d.text((140,420),"SHADOWRUN",font=font(115),fill=(233,247,247))
    d.text((140,590),"ARCOLOGY",font=font(100),fill=(43,211,198))
    d.text((140,735),"SHUTDOWN",font=font(111),fill=(43,211,198))
    d.text((140,990),"STORIES  /  ACTUAL PLAY  /  LORE",font=font(36),fill=(233,247,247))
    path=HERE/"cover.png"
    im.save(path,optimize=True)
    return path

def write(selected):
    if len(selected)!=120:
        raise ValueError("Insufficient legitimate publisher recordings: "+str(len(selected))+"/120")
    actual = collections.Counter(e["role"] for e in selected)
    if dict(actual)!=POLICY["roles"]:
        raise ValueError("Unexpected role count "+repr(dict(actual)))
    if len({e["url"] for e in selected})!=120:
        raise ValueError("Duplicate media enclosures")
    if len({e["publisher_guid"] for e in selected if e["publisher_guid"]})!=len([e for e in selected if e["publisher_guid"]]):
        raise ValueError("Duplicate original publisher GUIDs")
    for e in selected:
        if e["size"]<=0 or not e["url"].startswith("https://") or not e["mime"].startswith("audio/"):
            raise ValueError("Bad enclosure: "+e["title"])
    root=ET.Element("rss",{"version":"2.0"})
    ch=ET.SubElement(root,"channel")
    title="Shadowrun Arcology Shutdown — Story, Actual Play and Lore"
    put(ch,"title",title)
    put(ch,"link","https://github.com/Quarky/shadowrunfeed/tree/main/shadowrun/anthology")
    put(ch,"description","Independent 120-episode publisher-hosted inspiration anthology: original science-fiction stories, Shadowrun actual play, and setting lore. The eight-track Arcology collection remains available at its original address.")
    put(ch,"language","en")
    put(ch,"{"+IT+"}author","Shadowrun Curated Listening Catalog")
    put(ch,"{"+IT+"}summary","Original-publisher science-fiction stories, Shadowrun actual plays and setting lore for a lived-in arcology campaign.")
    put(ch,"{"+IT+"}explicit","true")
    put(ch,"{"+IT+"}type","episodic")
    ET.SubElement(ch,"{"+IT+"}category",{"text":"Leisure"})
    imageurl="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/shadowrun/anthology/cover.png"
    img=ET.SubElement(ch,"image")
    put(img,"url",imageurl)
    put(img,"title",title)
    put(img,"link","https://github.com/Quarky/shadowrunfeed/tree/main/shadowrun/anthology")
    ET.SubElement(ch,"{"+IT+"}image",{"href":imageurl})
    ET.SubElement(ch,"{"+AT+"}link",{"href":U,"rel":"self","type":"application/rss+xml"})
    put(ch,"lastBuildDate",email.utils.format_datetime(STAMP,usegmt=True))
    for n,e in enumerate(selected,1):
        e["slot"]=n
        el=ET.SubElement(ch,"item")
        put(el,"title",f"{n:03d} - {e['role'].replace('_',' ').upper()} - {e['publisher']} - {e['title']}")
        put(el,"link",e["publisher_link"])
        put(el,"description",explain(e))
        guid=put(el,"guid","urn:uuid:"+str(uuid.uuid5(uuid.NAMESPACE_URL,"shadowrun:anthology:v1:"+e["url"])))
        guid.attrib["isPermaLink"]="false"
        put(el,"pubDate",email.utils.format_datetime(STAMP-dt.timedelta(minutes=n),usegmt=True))
        ET.SubElement(el,"enclosure",{"url":e["url"],"length":str(e["size"]),"type":e["mime"]})
        put(el,"{"+IT+"}episode",n)
        put(el,"{"+IT+"}episodeType","full")
        if e["seconds"]:put(el,"{"+IT+"}duration",e["duration"])
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    parsed=ET.fromstring(xml)
    if len(parsed.find("channel").findall("item"))!=120:
        raise ValueError("RSS round-trip item count mismatch")
    path=HERE/"feed-v1.xml"
    path.write_bytes(xml)
    (HERE/"selected.json").write_text(json.dumps(selected,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    draw_cover()
    report.update({"state":"publisher_rss_metadata_validated","total":120,"roles":dict(actual),
     "pinned_baseline":sum(e["pinned_baseline"] for e in selected),
     "publisher_count":len({e["publisher"] for e in selected}),
     "publisher_rss_enclosures_validated":120,
     "over_30_min":sum(e["seconds"]>=1800 for e in selected),
     "over_60_min":sum(e["seconds"]>=3600 for e in selected),
     "unknown_duration":sum(e["seconds"]==0 for e in selected),
     "feed_sha256":hashlib.sha256(xml).hexdigest()})
    (HERE/"status.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PASS: built 120 real publisher-enclosed episodes from",report["publisher_count"],"publishers")

def main():
    old=baseline()
    plays=old["actual_play"]+gather("actual_play",old["actual_play"])
    lore=old["lore"]+gather("lore",old["lore"])
    stories=gather("story",[])
    required=POLICY["roles"]
    if len(plays)<required["actual_play"] or len(stories)<required["story"] or len(lore)<required["lore"]:
        raise ValueError("Not enough publisher items: "+repr({"story":len(stories),"actual_play":len(plays),"lore":len(lore)})+" inventories="+repr(report["source_inventory"]))
    # Return only the target number, after all duplicate/media checks.
    plays=reorder(plays)[:60]
    lore=reorder(lore)[:10]
    stories=reorder(stories)[:50]
    out=[]
    for a,b in zip(stories[:10],plays[:10]):out.extend((a,b))
    for a,b in zip(lore,plays[10:20]):out.extend((a,b))
    for a,b in zip(plays[20:],stories[10:]):out.extend((a,b))
    roles=[e["role"] for e in out]
    expected=[x for block in POLICY["mix"] for x in block["pattern"]*((block["range"][1]-block["range"][0]+1)//2)]
    if roles!=expected:
        raise ValueError("Role interleaving mismatch")
    write(out)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        report["state"]="blocked"
        report["error"]=str(exc)
        (HERE/"build-diagnostic.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print("BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(1)
    else:
        (HERE/"build-diagnostic.json").write_text(json.dumps({"state":"passed","total":120},indent=2)+"\n")
