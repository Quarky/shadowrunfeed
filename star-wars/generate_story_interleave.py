#!/usr/bin/env python3
"""Verify thirty sequential original fiction episodes for interleaving.

Pairs with the independent actual-play playlist at publication time.
Never copy, host, or synthesize audio. All titles are original publisher RSS.
"""
from __future__ import annotations
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from generate_learning import HERE,ITUNES,ATOM,url_bytes,verified_episode

CONFIG=json.loads((HERE/"interleave-fiction-catalog.json").read_text(encoding="utf-8"))
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)
NUMBER_WORDS=["one","two","three","four","five","six","seven","eight","nine","ten"]

def look_up(show):
    import urllib.parse
    args=urllib.parse.urlencode({"id":int(show["apple_id"]),"entity":"podcast","country":"us"})
    details=json.loads(url_bytes("https://itunes.apple.com/lookup?"+args))
    results=[v for v in details.get("results",[]) if v.get("collectionId")==int(show["apple_id"]) and v.get("feedUrl")]
    if len(results)!=1:raise ValueError("No unique publisher RSS found via Apple Podcasts")
    rss=results[0]["feedUrl"]
    root=ET.fromstring(url_bytes(rss))
    channel=root.find("channel")
    if root.tag!="rss" or channel is None:raise ValueError("Not a publisher RSS feed")
    return rss,channel.findall("item")

def normalized(s):
    return re.sub(r"\s+"," ",(s or "").casefold().replace("’","'")).strip()

def date(item):
    try:
        d=parsedate_to_datetime(item.findtext("pubDate") or "")
        return d.timestamp()
    except Exception:return 0

def valid_title(title):
    low=normalized(title)
    return not any(bad in low for bad in (
        "trailer","teaser","bonus content","announcement","behind the scenes",
        "preview","coming soon","interview","reaction","review","recap",
        "episode review","season trailer","cast interview","technical difficulties",
        "sneak peek","support the show","producer note","promo","livestream"))

def expected_chapter(source,chapter,item):
    title=normalized(item.findtext("title"))
    if not title or not valid_title(title):return False
    season=item.findtext(f"{{{ITUNES}}}season")
    episode=item.findtext(f"{{{ITUNES}}}episode")
    if source=="fathom":
        match=re.search(r"\bfathom[\s:\-]*e0?(\d+)\b",title)
        return bool(match and int(match.group(1))==chapter)
    if source=="station":
        match=re.search(r"\bs1e0?(\d+)\b",title)
        return bool(match and int(match.group(1))==chapter)
    if source=="among":
        match=re.search(r"\bs1e0?(\d+)\b",title)
        return bool(match and int(match.group(1))==chapter)
    if source=="legacy":
        word=NUMBER_WORDS[chapter-1]
        # Exact word form. Stops matching "Episode One Hundred" by accident.
        return bool(re.search(r"\bepisode "+word+r"\b(?=\s*[:\-]|$)",title))
    if source=="crusade":
        return bool(re.search(r"\bepisode\s+0?"+str(chapter)+r"\b(?=\s*[:\-]|$)",title))
    if source=="deca":
        if season=="1" and episode and episode.isdigit():
            return int(episode)==chapter
        # Season one was released before the later season; no incidental
        # "season 2 episode 1" substitution.
        if date(item)>datetime(2023,1,1,tzinfo=timezone.utc).timestamp():return False
        match=re.search(r"^(?:episode\s*)?(\d+)\s*[:\-\.]\s*",title)
        return bool(match and int(match.group(1))==chapter)
    if source=="orphans":
        if season=="1" and episode and episode.isdigit():
            return int(episode)==chapter
        if date(item)>datetime(2019,1,1,tzinfo=timezone.utc).timestamp():return False
        match=re.search(r"(?:\bs1e|\bseason\s*1[\s:\-]*episode\s*|\bepisode\s*)(\d+)\b",title)
        return bool(match and int(match.group(1))==chapter)
    raise ValueError("Unknown publisher chapter selector "+source)

def select(source,chapter,items):
    possible=[it for it in items if expected_chapter(source,chapter,it)]
    if len(possible)!=1:
        samples=[(it.findtext("title") or "")[:130]+
                  " [S="+str(it.findtext(f"{{{ITUNES}}}season"))+", E="+
                  str(it.findtext(f"{{{ITUNES}}}episode"))+"]" for it in items[:14]]
        raise ValueError(f"Required chapter {chapter}, got {len(possible)} exact title matches; RSS samples: "+repr(samples))
    original=possible[0]
    verified=verified_episode(original)
    if verified is None:raise ValueError("Original publisher chapter has no verified playable HTTPS enclosure")
    return verified

def save(name,content):
    path=HERE/name
    tmp=HERE/(name+".tmp")
    tmp.write_bytes(content)
    tmp.replace(path)

def main():
    sources={s["id"]:s for s in CONFIG["sources"]}
    feeds={}
    diagnostics=[]
    for sid,s in sources.items():
        try:
            rss,items=look_up(s)
            feeds[sid]=(rss,items)
            print("STORY SOURCE",sid,len(items))
        except Exception as err:
            diagnostics.append({"id":sid,"reason":str(err)[:1000]})
    out=[]
    for segment in CONFIG["segments"]:
        for entry in segment["order"]:
            sid=entry["show"];ch=entry["chapter"]
            if sid not in feeds:
                diagnostics.append({"source":sid,"chapter":ch,"reason":"Publisher source unavailable"})
                continue
            try:
                item=select(sid,ch,feeds[sid][1])
                out.append((segment["group"],sources[sid],entry,item,feeds[sid][0]))
                print("STORY SELECTED",segment["group"],sid,ch,item.findtext("title"))
            except Exception as err:
                diagnostics.append({"source":sid,"chapter":ch,"reason":str(err)[:1600]})
    if diagnostics:print("STORY VERIFICATION BLOCKERS:",json.dumps(diagnostics,indent=2))
    if len(out)!=30 or diagnostics:
        raise RuntimeError("Refusing incomplete publisher story/audio-drama series: "+str(len(out))+"/30 validated")
    if any(group!="remote-complex" for group,_,_,_,_ in out[:20]):raise ValueError("Remote facility stories not grouped first")
    if any(group!="sith-ruins" for group,_,_,_,_ in out[20:]):raise ValueError("Star Wars Sith fan-fiction not grouped last")
    used=set();book={}
    for group,source,episode,item,rss in out:
        key=item.find("enclosure").get("url").split("?")[0]
        if key in used:raise ValueError("Duplicate original publisher recording")
        used.add(key)
        book.setdefault(source["id"],[]).append(episode["chapter"])
    for sid,chapters in book.items():
        if chapters!=list(range(chapters[0],chapters[0]+len(chapters))):
            raise ValueError("Nonconsecutive publisher fiction chapters "+sid+": "+str(chapters))
    root=ET.Element("rss",{"version":"2.0"})
    chan=ET.SubElement(root,"channel")
    def put(container,tag,value):
        e=ET.SubElement(container,tag);e.text=str(value);return e
    put(chan,"title","Star Wars RPG — Original Fiction Interleaved with Actual Play")
    put(chan,"link","https://github.com/Quarky/shadowrunfeed/tree/main/star-wars")
    put(chan,"description","Thirty original fiction episodes for pairing with thirty actual-play episodes. First twenty: isolated facilities and alien environments; then ten: Star Wars community audio drama and dark-side intrigue. Publisher audio only.")
    put(chan,"language","en")
    ET.SubElement(chan,f"{{{ITUNES}}}image",{"href":"https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/cover.png"})
    ET.SubElement(chan,f"{{{ATOM}}}link",{"href":"https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/story-interleave.xml","rel":"self","type":"application/rss+xml"})
    episodes=[]
    for n,(group,show,ch,item,rss) in enumerate(out,1):
        orig_title=item.findtext("title") or ""
        it=ET.SubElement(chan,"item")
        type_="STAR WARS FAN AUDIO DRAMA" if group=="sith-ruins" else "CROSS-GENRE SCI-FI STORY"
        put(it,"title",f"{n:02d} · {type_} · [{show['title']}] {orig_title}")
        uid=hashlib.sha256((show["id"]+"|chapter-"+str(ch["chapter"])).encode()).hexdigest()
        guid=put(it,"guid","urn:sw-original-fiction:"+uid);guid.set("isPermaLink","false")
        link=item.findtext("link") or rss
        put(it,"link",link)
        description=(item.findtext("description") or "")[:400]
        put(it,"description",f"{type_}. Original scripted fiction, not actual play or lore commentary. Use: {show['focus']}. Original publisher date: {item.findtext('pubDate') or 'unknown'}. Original notes: {description}")
        put(it,"pubDate",item.findtext("pubDate") or "Mon, 01 Jan 2024 00:00:00 +0000")
        enc=item.find("enclosure")
        ET.SubElement(it,"enclosure",{"url":enc.get("url"),"length":enc.get("length"),"type":enc.get("type") or "audio/mpeg"})
        duration=item.findtext(f"{{{ITUNES}}}duration")
        if duration:put(it,f"{{{ITUNES}}}duration",duration)
        src=put(it,"source",show["title"]);src.set("url",rss)
        episodes.append({"fiction_order":n,"theme":group,"source_id":show["id"],"show":show["title"],
            "chapter":ch["chapter"],"title":orig_title,"url":link,"audio_url":enc.get("url"),
            "star_wars_fan_fiction":group=="sith-ruins","creative_use":show["focus"]})
    ET.indent(root,space="  ")
    payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(payload)
    status={"state":"published","generated_utc":datetime.now(timezone.utc).isoformat(),
        "fiction_episodes":30,"facility_fiction":20,"ancient_force_fiction":10,
        "source_count":len(book),"fan_fiction_count":10,"copyrighted_audio_mirrored":False,
        "warnings":[]}
    lines=["# Original science-fiction and Star Wars community dramas — interleaving companion","",
        "These thirty publisher-hosted, original fiction episodes are paired one-for-one with the newly selected actual plays in the **original Podbean subscription**. All scripts and recordings remain with their original creators.",
        "","The first twenty story chapters portray scientific isolation, archaeological facilities, emergency conditions, alien ruins and character consequences. The final ten are **unofficial Star Wars fan audio dramas** portraying Sith, relics, loyalty, Force traditions and risky artifacts.",
        "","| Story # | Genre | Original publisher chapter | Creative use |",
        "| ---: | --- | --- | --- |"]
    for row in episodes:
        lines.append(f'| {row["fiction_order"]} | {"Star Wars fan story" if row["star_wars_fan_fiction"] else "Other sci-fi fiction"} | [{row["title"].replace("|","–")}]({row["url"]}) — {row["show"]} | {row["creative_use"]} |')
    lines+=["","No official Lucasfilm affiliation is implied. These are community-created works; the RSS points to original publisher recordings, not an unauthorized copy.",""]
    save("story-interleave.xml",payload)
    save("story-interleave-episodes.json",(json.dumps({"episodes":episodes},indent=2,ensure_ascii=False)+"\n").encode())
    save("story-interleave-episodes.md","\n".join(lines).encode())
    save("story-interleave-status.json",(json.dumps(status,indent=2)+"\n").encode())
    print("VERIFIED original publisher fiction:",len(episodes),"across",len(book),"shows")

if __name__=="__main__":
    main()
