#!/usr/bin/env python3
"""Anomaly V3: transcript-evidence-aware publisher RSS build (not a V2 update).

V3 preserves the 120-episode role/theme mix while selectively replacing
reviewed material. A requested swap must resolve to exactly one publisher RSS
item with a real HTTPS audio enclosure, never to a fabricated podcast link.
Third-party stories are creative references, not campaign-played canon.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import html, json, re, sys, uuid
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PUBLIC="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/"
ITUNES="http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM="http://www.w3.org/2005/Atom"
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)
BORN=datetime(2026,10,20,18,30,tzinfo=timezone.utc)

def put(parent,tag,value):
    child=ET.SubElement(parent,tag)
    child.text=str(value or "")
    return child

def norm(value):
    return re.sub(r"[^a-z0-9]+"," ",html.unescape(value).lower()).strip()

def fetch_publisher(feed, expected_title):
    request=Request(feed,headers={
        "User-Agent":"Anomaly V3 editorial source validation/1.0",
        "Accept":"application/rss+xml,application/xml,text/xml,*/*"
    })
    with urlopen(request,timeout=28) as r:
        blob=r.read(24_000_000)
    parsed=ET.fromstring(blob)
    channel=parsed.find("channel")
    if channel is None:
        raise ValueError("No RSS channel at "+feed)
    options=[i for i in channel.findall("item")
             if norm(i.findtext("title") or "") == norm(expected_title)]
    if len(options)!=1:
        raise ValueError("Ambiguous or unavailable episode: "+expected_title+
                         " ("+str(len(options))+" matches)")
    item=options[0]
    encl=item.find("enclosure")
    if encl is None:
        raise ValueError("Selected original recording has no enclosure")
    uri=(encl.get("url") or "").strip()
    size=int(encl.get("length") or 0)
    mime=encl.get("type") or ""
    if urlparse(uri).scheme!="https" or size<1 or not mime.startswith("audio/"):
        raise ValueError("Episode has invalid publisher enclosure: "+expected_title)
    duration=item.findtext("{"+ITUNES+"}duration") or ""
    publisher_link=item.findtext("link") or ""
    original=item.findtext("pubDate") or ""
    description=re.sub(r"<[^>]+>"," ",html.unescape(item.findtext("description") or ""))
    description=re.sub(r"\s+"," ",description).strip()[:900]
    return {
      "title":(item.findtext("title") or "").strip(),
      "source_link":publisher_link if publisher_link.startswith("https://") else uri,
      "audio_url":uri,"audio_length":size,"audio_type":mime,
      "duration":duration,"source_date":original,"description":description,
      "publisher_guid":item.findtext("guid") or uri
    }

def render(source,policy):
    channel_root=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(channel_root,"channel")
    title="Anomaly V3 - Immersive Fantasy Stories and Actual Plays"
    put(channel,"title",title)
    put(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly/v3")
    put(channel,"description",
        "An independently researched collection of 120 fantasy-inspired story and RPG actual-play recordings, "
        "curated for immersive characters, culture, strange magic and worldbuilding. 60/60 interleave "
        "and six themes. Publisher-owned audio; fictional events are not Anomaly campaign canon.")
    put(channel,"language","en")
    put(channel,"copyright","Original recordings copyright their independent publishers.")
    put(channel,"{"+ITUNES+"}author","Anomaly V3 Independent Listening")
    put(channel,"{"+ITUNES+"}summary","Character-forward stories, lore-rich drama and tabletop games.")
    put(channel,"{"+ITUNES+"}explicit","true")
    put(channel,"{"+ITUNES+"}type","episodic")
    ET.SubElement(channel,"{"+ITUNES+"}category",{"text":"Leisure"})
    artwork=ET.SubElement(channel,"image")
    put(artwork,"url",PUBLIC+"cover.png")
    put(artwork,"title",title)
    put(artwork,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly/v3")
    ET.SubElement(channel,"{"+ITUNES+"}image",{"href":PUBLIC+"cover.png"})
    ET.SubElement(channel,"{"+ATOM+"}link",{"href":PUBLIC+"feed-v3.xml","rel":"self","type":"application/rss+xml"})
    put(channel,"lastBuildDate",format_datetime(BORN,usegmt=True))

    for n,ep in enumerate(source,1):
        kind="STORY" if ep["role"]=="story" else "ACTUAL PLAY"
        item=ET.SubElement(channel,"item")
        put(item,"title",f'{n:03d} - {kind} - {ep["publisher"]} - {ep["title"]}')
        put(item,"link",ep["source_link"] or ep["audio_url"])
        insight=ep.get("editorial_evidence") or ""
        desc=("Theme: "+ep["theme"]+". Publisher: "+ep["publisher"]+
              ". Original publication: "+(ep["source_date"] or "not stated")+
              ". Description: "+ep["description"]+
              ". Editorial relevance: "+insight+
              ". Inspiration only; no outside fiction establishes this campaign's world.")
        put(item,"description",desc)
        identity=uuid.uuid5(uuid.NAMESPACE_URL,"anomaly:v3:"+ep["audio_url"])
        g=put(item,"guid","urn:uuid:"+str(identity))
        g.set("isPermaLink","false")
        put(item,"pubDate",format_datetime(BORN-timedelta(minutes=n),usegmt=True))
        ET.SubElement(item,"enclosure",{
            "url":ep["audio_url"],"length":str(ep["audio_length"]),
            "type":ep["audio_type"]
        })
        put(item,"{"+ITUNES+"}episodeType","full")
        put(item,"{"+ITUNES+"}episode",str(n))
        if ep.get("duration"):
            put(item,"{"+ITUNES+"}duration",ep["duration"])

    return ET.tostring(channel_root,encoding="utf-8",xml_declaration=True)

def main():
    config=json.loads((HERE/"selection-policy.json").read_text("utf-8"))
    existing=json.loads((BASE/"fresh-episode-catalog.json").read_text("utf-8"))["episodes"]
    assert len(existing)==120
    assert config["mix"]["story"]==config["mix"]["actual_play"]==60
    assert config["mix"]["lore"]==0 and config["mix"]["interview"]==0
    selected=[dict(e) for e in existing]
    resolved=[]
    for spec in config["replacements"]:
        n=spec["position"]
        original=dict(selected[n-1])
        if original["number"]!=n or original["role"]!=spec["role"] or original["theme"]!=spec["theme"]:
            raise ValueError("Incompatible replacement "+str(n))
        found=fetch_publisher(spec["rss"],spec["title"])
        selected[n-1].update(found)
        selected[n-1]["publisher"]=spec["publisher"]
        selected[n-1]["editorial_evidence"]=spec["evidence"]
        resolved.append({
           "position":n,"replaces":original["publisher"]+" - "+original["title"],
           "selected":spec["publisher"]+" - "+found["title"],
           "publisher_rss":spec["rss"],"publisher_guid":found["publisher_guid"],
           "audio_url":found["audio_url"],"audio_length":found["audio_length"],
           "episode_page":spec["episode_page"],"transcript":spec["transcript"],
           "evaluation":spec["evidence"],"quality":spec["quality"]
        })
    ids=set();enclosures=set();publishers={};theme_roles={}
    for n,ep in enumerate(selected,1):
        expected="story" if n%2 else "actual_play"
        if ep["role"]!=expected or ep["number"]!=n:
            raise ValueError("V3 60/60 alternation failure")
        key=(ep["theme"],ep["role"])
        theme_roles[key]=theme_roles.get(key,0)+1
        if ep["audio_length"]<=0 or not ep["audio_url"].startswith("https://"):
            raise ValueError("Invalid audio enclosure "+str(n))
        if ep["audio_url"] in enclosures:
            raise ValueError("Duplicate original recording URL")
        enclosures.add(ep["audio_url"])
        publishers[ep["publisher"]]=publishers.get(ep["publisher"],0)+1
    assert len(enclosures)==120 and len(publishers)>=29
    assert len(theme_roles)==12 and all(count==10 for count in theme_roles.values())
    assert not any(ep["publisher"] in ("Worlds Beyond Number","Dungeons of Drakkenheim") for ep in selected)
    xml=render(selected,config)
    root=ET.fromstring(xml)
    gs=[e.findtext("guid") for e in root.findall("./channel/item")]
    assert len(gs)==len(set(gs))==120
    assert "magudonya" not in xml.decode("utf-8").lower()
    old=BASE/"feed-v2.xml"
    assert old.exists()
    for path in [BASE/"feed-v3.xml", HERE/"feed-v3.xml"]:
        if not path.exists() or path.read_bytes()!=xml:
            path.write_bytes(xml)
    results={
        "state":"candidate_published",
        "edition":3,"total":120,"story":60,"actual_play":60,
        "lore":0,"interview":0,"themes":{"|".join(key):count for key,count in theme_roles.items()},
        "publisher_count":len(publishers),"publishers":publishers,
        "episode_swaps":resolved,
        "full_publisher_scripts_reviewed_positions":config["audit_requirements"]["full_publisher_scripts_reviewed_in_final_v3"],
        "transcript_reviewed_count":config["audit_requirements"]["transcript_reviewed_final_selection_count"],
        "remaining_transcript_audit_count":config["audit_requirements"]["remaining_final_selection_transcripts_unverified"],
        "meta_note":"Transcript-first V3 pilot, five confirmed final-selection full scripts audited, rest still to audit; no source audio rehosting.",
        "subscription_url":PUBLIC+"feed-v3.xml"
    }
    (HERE/"status.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n","utf-8")
    print("V3 generation PASS:",len(enclosures),"publisher-hosted unique enclosures,",
          len(publishers),"publishers, audited swaps:",len(resolved),flush=True)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("V3 NOT PUBLISHED: "+repr(exc),file=sys.stderr,flush=True)
        raise
