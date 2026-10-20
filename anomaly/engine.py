#!/usr/bin/env python3
"""Anomaly campaign listening RSS: original-publisher enclosures only.

Selects 60 serial fiction episodes and 60 distinct actual plays, 10 pairs per
campaign theme. Does not download, host, modify, or redistribute audio.
"""
from __future__ import annotations
import concurrent.futures as cf
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
THEMES = CATALOG["themes"]
ROOT = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/"
UA = "Mozilla/5.0 (compatible; AnomalyCuratedFeed/1.0)"
ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
ET.register_namespace("itunes", ITUNES)
ET.register_namespace("atom", ATOM)
SKIP = re.compile(r"\b(trailer|preview|teaser|announcement|recap|behind the scenes|bonus content|patreon|feed drop|feed swap|promo|advertis|special announcement|outtakes|season recap|livestream update)\b", re.I)
TAG = re.compile("<[^>]+>")
WORD = re.compile(r"[^a-z0-9]+")
THEME_TERMS = {
  "communities": ["city","town","people","community","market","home","kingdom","village","tavern","inn","festival","family","court","society","guild","relationships"],
  "eilistraee": ["eilistraee","drow","lolth","elf","elves","forest","exile","refugee","faith","divine","goddess","sanctuary","paladin","moon","redemption","priestess"],
  "itich": ["dwarf","forge","mine","underground","cave","burrow","hive","colony","insect","ruins","ancient","tunnel","dungeon","craft","survival"],
  "wall": ["wall","infection","crystal","parasite","fungus","spore","horror","plague","psychic","terrible","nightmare","wound","strange","anomaly","monster","bacteria"],
  "attina": ["magic","transformation","changed","memories","identity","dream","friend","friendship","ritual","transmutation","soul","agency","weave","witch","mage"],
  "aberrations": ["aboleth","mind flayer","illithid","elder brain","deep","void","ancient","psychic","mind","dream","horror","alien","labyrinth","monster","mystery"]
}

def get(url, timeout=18):
    rq = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/json, application/xml, */*"})
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        data = r.read(22_000_000)
    return data

def normal(s):
    return WORD.sub(" ", (s or "").lower()).strip()

def apple_feed(src):
    if not src.get("apple_search"):
        return []
    q = urllib.parse.urlencode({"term": src["apple_search"],"entity":"podcast","limit":"20","country":"us"})
    try:
        result = json.loads(get("https://itunes.apple.com/search?" + q))
    except Exception as e:
        print("Apple search failed", src["id"],str(e)[:100],flush=True)
        return []
    want = set(normal(src["name"]).split())
    aliases = set(normal(src["apple_search"]).split())
    results = []
    for row in result.get("results", []):
        title = normal(row.get("collectionName", ""))
        terms = set(title.split())
        common = max(len(terms & want) / max(len(want),1), len(terms & aliases) / max(len(aliases),1))
        if common >= 0.72 and row.get("feedUrl"):
            results.append(row["feedUrl"])
    return list(dict.fromkeys(results))

def timestamp(episode):
    from email.utils import parsedate_to_datetime
    try:
        d = parsedate_to_datetime(episode.findtext("pubDate") or "")
        return d.timestamp()
    except (ValueError,TypeError,OverflowError):
        return 0.0

def validate_length(enc):
    try:
        n = int(enc.get("length","0"))
        if n > 0:
            return n
    except (ValueError,TypeError):
        pass
    u = enc.get("url","")
    try:
        rq = urllib.request.Request(u, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(rq, timeout=8) as r:
            return int(r.headers.get("Content-Length") or 0)
    except Exception:
        return 0

def entries_from(src, channel):
    result=[]
    for x in channel.findall("item"):
        title=(x.findtext("title") or "").strip()
        if not title or SKIP.search(title):
            continue
        combined = normal(title+" "+(x.findtext("description") or ""))
        required = src.get("required_title", "")
        if required and normal(required) not in combined:
            continue
        enc = x.find("enclosure")
        if enc is None: continue
        url = (enc.get("url") or "").strip()
        if not url.startswith("https://"): continue
        # Defer slow HEAD requests until episodes are actually selected.
        try: length=max(0,int(enc.get("length") or 0))
        except (TypeError, ValueError): length=0
        guid=(x.findtext("guid") or "").strip() or url
        link=(x.findtext("link") or "").strip()
        duration=x.findtext("{%s}duration" % ITUNES) or ""
        d=x.findtext("description") or ""
        description = TAG.sub(" ", html.unescape(d))
        description = re.sub(r"\s+", " ", description)[:850]
        result.append({
            "key":src["id"]+"::"+guid,
            "source":src["id"],"source_name":src["name"],"role":src["role"],
            "title":title,"description":description,"link":link if link.startswith("https://") else "",
            "url":url,"length":length,"mime":enc.get("type") or ("audio/mp4" if ".m4a" in url.lower() else "audio/mpeg"),
            "duration":duration,"original":(x.findtext("pubDate") or "").strip(),
            "stamp":timestamp(x),"guid":guid
        })
    result.sort(key=lambda e:(e["stamp"],e["title"].casefold()))
    seen=set(); distinct=[]
    for e in result:
        if e["url"] in seen: continue
        seen.add(e["url"]); distinct.append(e)
    return distinct

def load(src):
    errors=[]
    urls=src.get("rss_candidates",[])
    # Existing verified publisher RSS is preferred; Apple resolves the rest.
    # Resolve Apple only if configured publisher RSS candidates do not work.
    for batch in (urls, None):
      for url in list(dict.fromkeys(apple_feed(src) if batch is None else batch)):
        try:
            root=ET.fromstring(get(url))
            ch=root.find("channel") if root.tag != "channel" else root
            if ch is None: raise ValueError("missing RSS channel")
            items=entries_from(src,ch)
            if not items: raise ValueError("no qualifying publisher audio enclosures")
            print("%-23s %4d usable (%s)"%(src["id"],len(items),url),flush=True)
            return src,items,url,""
        except Exception as exc:
            errors.append(type(exc).__name__+": "+str(exc)[:120])
    print("UNAVAILABLE",src["id"], "; ".join(errors[:3]),flush=True)
    return src,[],None,"; ".join(errors[:3])

def scored(ep,theme):
    t=normal(ep["title"]+" "+ep["description"][:500])
    return sum((16 if term in normal(ep["title"]) else 3) for term in THEME_TERMS[theme] if normal(term) in t)

def create_cover(path):
    from PIL import Image, ImageDraw, ImageFont
    sz=1500
    im=Image.new("RGB",(sz,sz),(18,25,34))
    d=ImageDraw.Draw(im)
    for offset in range(7):
        p=90+offset*70
        d.rounded_rectangle((p,p,sz-p,sz-p),radius=64,outline=(62+offset*7,100+offset*5,102+offset*3),width=5)
    d.ellipse((545,235,955,645),outline=(220,179,107),width=18)
    d.arc((595,283,905,599),0,300,fill=(220,179,107),width=14)
    d.line((245,1000,1255,1000),fill=(220,179,107),width=8)
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        big=ImageFont.truetype(font,127)
        small=ImageFont.truetype(font,58)
    except OSError:
        big=small=ImageFont.load_default()
    d.rounded_rectangle((75,1040,1425,1420),fill=(18,25,34),radius=20)
    d.text((750,1080),"ANOMALY",font=big,anchor="mt",fill=(238,222,187))
    d.text((750,1270),"STORIES  +  ACTUAL PLAYS",font=small,anchor="mt",fill=(222,179,107))
    im.save(path,format="PNG",optimize=True)

def put(parent,tag,value):
    el=ET.SubElement(parent,tag);el.text=str(value);return el

def make_rss(selected):
    rss=ET.Element("rss",version="2.0")
    channel=ET.SubElement(rss,"channel")
    put(channel,"title",CATALOG["feed_title"])
    put(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly")
    put(channel,"description","A 120-episode, campaign-matched anthology: 60 performed fantasy/horror stories interleaved with 60 tabletop actual plays. Six Anomaly campaign themes. Original publisher audio only; not an official D&D production.")
    put(channel,"language","en")
    put(channel,"copyright","Audio and recordings remain copyright of their original publishers; this is an independent editorial index.")
    put(channel,"{%s}author"%ITUNES,"Anomaly independent listening catalog")
    put(channel,"{%s}summary"%ITUNES,"Character-driven stories and actual plays inspired by the Anomaly campaign.")
    put(channel,"{%s}explicit"%ITUNES,"yes")
    ET.SubElement(channel,"{%s}category"%ITUNES,text="Leisure")
    artwork=ET.SubElement(channel,"image")
    put(artwork,"url",ROOT+"cover.png")
    put(artwork,"title",CATALOG["feed_title"])
    put(artwork,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly")
    ET.SubElement(channel,"{%s}image"%ITUNES,href=ROOT+"cover.png")
    ET.SubElement(channel,"{%s}link"%ATOM,href=ROOT+"feed-v2.xml",rel="self",type="application/rss+xml")
    now=datetime.now(timezone.utc)
    put(channel,"lastBuildDate",format_datetime(now))
    # Current Podbean queues display newer pubDate first. Preserve explicit
    # 01..120 order with reverse synthetic item dates; keep original in description.
    for pos,entry in enumerate(selected,1):
        ep=entry["episode"]; theme=entry["theme"];meta=THEMES[theme]
        item=ET.SubElement(channel,"item")
        group = "STORY" if ep["role"]=="story" else "ACTUAL PLAY"
        put(item,"title",f'{pos:02d} • {group} • [{ep["source_name"]}] {ep["title"]}')
        unique=hashlib.sha256(ep["key"].encode()).hexdigest()
        guid=put(item,"guid","urn:magudonya:1:"+unique);guid.set("isPermaLink","false")
        put(item,"link",ep["link"] or ep["url"])
        put(item,"description",f'Role: {group}. Campaign inspiration: {meta["title"]}. Editorial interpretation: {meta["description"]} Use the fictional/source story only as inspiration, NOT as Anomaly canon. Original publisher: {ep["source_name"]}. Original publication: {ep["original"]}. Source summary: {ep["description"]}')
        put(item,"pubDate",format_datetime(now-timedelta(minutes=pos),usegmt=True))
        ET.SubElement(item,"enclosure",url=ep["url"],length=str(ep["length"]),type=ep["mime"])
        if ep["duration"]: put(item,"{%s}duration"%ITUNES,ep["duration"])
    for filename in ["feed.xml","feed-v2.xml"]:
        ET.ElementTree(rss).write(HERE/filename,encoding="utf-8",xml_declaration=True)
    return rss

def main():
    sources=CATALOG["sources"]
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        bundles=list(pool.map(load,sources))
    by_source={src["id"]:items for src,items,url,err in bundles}
    errors={src["id"]:err for src,items,url,err in bundles if err}
    cursors={src["id"]:0 for src in sources}
    used=set()
    selected=[]
    manifest=[]
    old_lock={}
    lock_path=HERE/"selection-lock.json"
    if lock_path.exists():
        try: old_lock=json.loads(lock_path.read_text(encoding="utf-8"))
        except (ValueError,OSError): pass
    lock_next={}

    for theme in THEMES:
        block={}
        for role in ["story","actual_play"]:
            qualifying=[s for s in sources if s["role"]==role and theme in s["themes"] and by_source[s["id"]]]
            picked=[]
            old_keys=old_lock.get(theme,{}).get(role,[])
            # Pin existing published selection identities across updates.
            for key in old_keys:
                for s in qualifying:
                    for ep in by_source[s["id"]]:
                        if ep["key"]==key and key not in used:
                            picked.append(ep);used.add(key)
                            break
                    if key in used: break
                if len(picked)>=10: break
            quota={s["id"]:0 for s in qualifying}
            for ep in picked: quota[ep["source"]]+=1
            rounds=0
            while len(picked)<10 and rounds<150:
                rounds+=1
                available=[]
                for s in qualifying:
                    pool=by_source[s["id"]]
                    # Do not skip older chapters of a serial simply to match one keyword.
                    cur=cursors[s["id"]]
                    while cur<len(pool) and pool[cur]["key"] in used:
                        cur+=1
                    cursors[s["id"]]=cur
                    if cur>=len(pool): continue
                    max_show=6 if s["id"]=="drow-dracoliches" and theme=="eilistraee" else 4
                    if quota[s["id"]]>=max_show: continue
                    candidate=pool[cur]
                    preference=100 if s["id"]=="drow-dracoliches" and theme=="eilistraee" else 0
                    diversity=-quota[s["id"]]*70
                    relevance=min(30,scored(candidate,theme))
                    available.append((preference+diversity+relevance,s["id"],candidate))
                if not available: break
                available.sort(key=lambda x:(x[0],x[1]),reverse=True)
                _,sid,e=available[0]
                picked.append(e);used.add(e["key"])
                quota[sid]+=1
                cursors[sid]+=1
            if len(picked)!=10:
                raise RuntimeError(f"Not enough verified {role} for theme '{theme}': got {len(picked)} of 10; sources {[(s['id'],len(by_source[s['id']])) for s in qualifying]}")
            block[role]=picked
            lock_next.setdefault(theme,{})[role]=[e["key"] for e in picked]
        for story,play in zip(block["story"],block["actual_play"]):
            selected.append({"theme":theme,"episode":story})
            selected.append({"theme":theme,"episode":play})
    assert len(selected)==120, len(selected)
    assert len(set(x["episode"]["key"] for x in selected))==120
    # Validate original RSS enclosure sizes only for the 120 winners.
    # Some providers omit length in their feeds; HEAD provides actual bytes.
    def selected_length(p):
        e=p["episode"]
        return validate_length(ET.Element("enclosure", {"url":e["url"],"length":str(e["length"])}))
    with cf.ThreadPoolExecutor(max_workers=24) as pool:
        lengths=list(pool.map(selected_length, selected))
    missing=[f'{p["episode"]["source"]}: {p["episode"]["title"]}' for p,n in zip(selected,lengths) if n<1]
    if missing:
        raise RuntimeError("No verifiable audio size for selected episode(s): "+ "; ".join(missing))
    for p,n in zip(selected,lengths):
        p["episode"]["length"]=n
    make_rss(selected)
    create_cover(HERE/"cover.png")
    summary={"generated_at":datetime.now(timezone.utc).isoformat(),"state":"published","total_episodes":len(selected),"story":60,"actual_play":60,"themes":{t:20 for t in THEMES},"available_sources":len(sources)-len(errors),"configured_sources":len(sources),"unavailable_sources":errors,"audio_rehosted":False,"interleave_valid":all((x["episode"]["role"]=="story" if i%2==0 else x["episode"]["role"]=="actual_play") for i,x in enumerate(selected))}
    (HERE/"status.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    (HERE/"selection-lock.json").write_text(json.dumps(lock_next,indent=2,ensure_ascii=False)+"\n")
    (HERE/"episodes.json").write_text(json.dumps([{"number":i,"theme":p["theme"],"role":p["episode"]["role"],"publisher":p["episode"]["source_name"],"title":p["episode"]["title"],"original_date":p["episode"]["original"],"publisher_link":p["episode"]["link"]} for i,p in enumerate(selected,1)],indent=2,ensure_ascii=False)+"\n")
    lines=["# Anomaly — Campaign-Matched 120-Episode Listening Order","","Stories and tabletop actual plays alternate one-for-one. Original chapter order preserved within each series. Themes are editorial inspiration; source events are **not** campaign canon.",""]
    for i,p in enumerate(selected,1):
        ep=p["episode"]; kind="STORY" if ep["role"]=="story" else "ACTUAL PLAY"
        if i%20==1: lines.extend([f'## {THEMES[p["theme"]]["title"]}',"",THEMES[p["theme"]]["description"],""])
        lines.append(f'{i:03d}. **{kind}** — [{ep["title"]}]({ep["link"] or ep["url"]}) — *{ep["source_name"]}*')
    (HERE/"episodes.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="unavailable_sources"},indent=2),flush=True)

if __name__=="__main__":
    try:main()
    except Exception as error:
        print("FEED NOT PUBLISHED:",repr(error),file=sys.stderr,flush=True)
        raise
