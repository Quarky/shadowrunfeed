#!/usr/bin/env python3
"""Publish the expanded playlist at the ORIGINAL Star Wars podcast RSS URLs.

The first custom Podbean subscription was to feed-v2.xml, not learning-feed-v2.xml.
Preserve the original channel identity and all 16 old GUIDs while prepending
the 20 specially curated recordings. The separate legacy sampler remains the
publisher-verified source archive. Audio is never downloaded or copied.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
import copy
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ATOM="http://www.w3.org/2005/Atom"
ITUNES="http://www.itunes.com/dtds/podcast-1.0.dtd"
URLBASE="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/"
ET.register_namespace("atom",ATOM)
ET.register_namespace("itunes",ITUNES)

def audio_identity(url):
    """Ignore expiring CDN query signatures and Libsyn/Megaphone host aliases."""
    parts=urllib.parse.urlsplit(url)
    host=parts.netloc.casefold().replace("dcs-cached.megaphone.fm","dcs-spotify.megaphone.fm")
    raw_path=urllib.parse.unquote(parts.path)
    path=raw_path.replace("/secure/","/").casefold()
    return host+path

def item_audio(item):
    enc=item.find("enclosure")
    if enc is None or not enc.get("url","").startswith("https://"):
        raise ValueError("RSS item has no publisher-hosted HTTPS audio")
    if int(enc.get("length","0"))<1:
        raise ValueError("RSS audio size is missing")
    return enc.get("url")

def read_feed(path):
    root=ET.parse(path).getroot()
    channel=root.find("channel")
    if root.tag!="rss" or channel is None:
        raise ValueError("Not an RSS 2.0 publisher index: "+str(path))
    items=channel.findall("item")
    if not items:raise ValueError("RSS feed has no original episodes: "+str(path))
    return root,channel,items

def atomic(path, data):
    temp=path.with_suffix(path.suffix+".tmp")
    temp.write_bytes(data)
    temp.replace(path)

def build():
    # Old subscriber identities must come from the original subscriber sampler.
    original_root,_,legacy=read_feed(HERE/"sampler-v2.xml")
    current_root,_,ranked=read_feed(HERE/"learning-feed-v2.xml")
    status=json.loads((HERE/"learning-status.json").read_text(encoding="utf-8"))
    if status.get("state")!="published" or status.get("featured_prefix")!=20:
        raise ValueError("Featured ranked collection has not been validated")
    if len(ranked)!=status["episodes"] or len(ranked)<40:
        raise ValueError("Ranked collection count is inconsistent with its manifest")
    if len(legacy)<15:raise ValueError("Original listener sampler is missing episodes")
    ident_legacy={}
    for episode in legacy:
        key=audio_identity(item_audio(episode))
        guid=episode.find("guid")
        if key in ident_legacy or guid is None or not guid.text:
            raise ValueError("Original subscriber GUID identity is ambiguous")
        ident_legacy[key]=episode
    combined=[]
    seen=set()
    old_guids_kept=set()
    for item in ranked:
        key=audio_identity(item_audio(item))
        if key in seen:raise ValueError("Duplicated audio in ranked source")
        seen.add(key)
        new=copy.deepcopy(item)
        previous=ident_legacy.get(key)
        if previous is not None:
            # Keep GUID identity from the RSS originally supplied to Podbean.
            guid_prev=previous.find("guid")
            guid_current=new.find("guid")
            if guid_current is None:guid_current=ET.SubElement(new,"guid")
            guid_current.text=guid_prev.text
            guid_current.attrib.clear()
            guid_current.attrib.update(guid_prev.attrib)
            old_guids_kept.add(guid_prev.text)
        combined.append(new)
    legacy_extra=0
    for item in legacy:
        key=audio_identity(item_audio(item))
        if key not in seen:
            extra=copy.deepcopy(item)
            guid=extra.find("guid")
            old_guids_kept.add(guid.text)
            combined.append(extra)
            seen.add(key)
            legacy_extra+=1
    # Append the previously published twenty actual-play recordings only
    # after all original ranked + sampler items. Never change old episode IDs.
    expansion_status=json.loads((HERE/"expansion-status.json").read_text(encoding="utf-8"))
    if expansion_status.get("state")!="published" or expansion_status.get("count")!=20:
        raise ValueError("Previously published 20-episode expansion not verified")
    _,_,expansion_items=read_feed(HERE/"expansion.xml")
    expansion_rows=json.loads((HERE/"expansion-episodes.json").read_text(encoding="utf-8"))["episodes"]
    if len(expansion_items)!=20 or len(expansion_rows)!=20:
        raise ValueError("Expansion RSS and exact-title playlist disagree")
    old_count=len(combined)
    for index,item in enumerate(expansion_items):
        row=expansion_rows[index]
        if row["new_selection"]!=index+1:
            raise ValueError("Expansion episode order mismatch")
        if index<10 and row["theme"]!="remote-complex":
            raise ValueError("First ten expansion selections must be remote-complex")
        if index>=10 and row["theme"]!="sith-ruins":
            raise ValueError("Last ten expansion selections must be Sith-ruins themed")
        key=audio_identity(item_audio(item))
        if key in seen:
            raise ValueError("New actual-play selection already in original podcast: "+row["episode"])
        seen.add(key)
        combined.append(copy.deepcopy(item))
    if len(combined)!=old_count+20:raise ValueError("Podcast expansion did not retain exactly 20 earlier tracks")

    # Ten Moraband-inspired then ten Shard Moon-inspired cross-genre recordings.
    # The format alternates scripted fiction with real tabletop actual play.
    bonus_status=json.loads((HERE/"bonus-20-status.json").read_text(encoding="utf-8"))
    if bonus_status.get("state")!="published" or bonus_status.get("count")!=20 or bonus_status.get("drama_count")!=10 or bonus_status.get("actual_play_count")!=10:
        raise ValueError("20-title scripted fiction and actual-play bonus was not verified")
    _,_,bonus_items=read_feed(HERE/"bonus-20.xml")
    bonus_rows=json.loads((HERE/"bonus-20-episodes.json").read_text(encoding="utf-8"))["episodes"]
    if len(bonus_items)!=20 or len(bonus_rows)!=20:
        raise ValueError("Twenty verified bonus entries are required")
    for index,item in enumerate(bonus_items):
        row=bonus_rows[index]
        if row["selection"]!=index+1 or row["theme"]!=("moraband" if index<10 else "shard-moon"):
            raise ValueError("Unexpected themed bonus order")
        if row["kind"]!=("DRAMA" if index%2==0 else "ACTUAL_PLAY"):
            raise ValueError("The format distribution is not half dramas, half actual plays")
        key=audio_identity(item_audio(item))
        if key in seen:raise ValueError("Bonus publisher recording repeats previous audio: "+row["episode"])
        seen.add(key)
        combined.append(copy.deepcopy(item))
    if len(combined)!=old_count+40:
        raise ValueError("Combined expansion failed to append 20 new bonus episodes")
    expected_guids={x.findtext("guid") for x in legacy}
    if old_guids_kept!=expected_guids:
        raise ValueError("Original subscription episode GUIDs were lost")
    if len({x.findtext("guid") for x in combined})!=len(combined):
        raise ValueError("Duplicate GUIDs in original subscribed feed")
    if len(combined)!=len(seen):
        raise ValueError("Repeated audio after legacy+ranked integration")
    expected_roles=["CROSS-GENRE INSPIRATION","ACTUAL_PLAY"]*5+["LORE","STORY"]*5
    for index,role in enumerate(expected_roles):
        if role not in (combined[index].findtext("title") or ""):
            raise ValueError(f"Themed episode order is broken at position {index+1}")
    if len(combined)<status["episodes"]:
        raise ValueError("New ranked episodes were unexpectedly lost")
    # Preserve the original show title, image, author, rating and category tags.
    legacy_channel=original_root.find("channel")
    for item in legacy:legacy_channel.remove(item)
    description=legacy_channel.find("description")
    if description is not None:
        description.text=("Original Star Wars FFG/D6 sampler expanded with a 20-episode "
            "frontier audio-drama and actual-play opening, followed by the complete ranked "
            "Star Wars lore/story selection and retained original sampler episodes, "
            "then twenty previous actual plays themed around remote research complexes " 
            "and ancient Sith ruins; twenty NEW non-Star-Wars fiction and actual-play recordings then follow, Moraband mysteries first and Shard Moon research-survival second. External science-fiction drama and actual play " 
            "are cross-genre inspiration, not Star Wars canon. "
            "All recordings remain on their publishers' servers.")
    summary=legacy_channel.find(f"{{{ITUNES}}}summary")
    if summary is not None:summary.text=description.text
    for n,item in enumerate(combined,1):
        # Retain stable source episode GUIDs while using publication order as a
        # deterministic RSS sorting key (the real dates remain in source notes).
        published=item.find("pubDate")
        old_date=published.text if published is not None else ""
        if published is None:published=ET.SubElement(item,"pubDate")
        published.text=format_datetime(datetime(2026,10,17,18,0,tzinfo=timezone.utc)-timedelta(minutes=n))
        if n>status["episodes"]:
            desc=item.find("description")
            if desc is not None:
                desc.text=(desc.text or "")+f" Original source release date: {old_date}."
        legacy_channel.append(item)
    result={}
    for filename in ("feed-v2.xml","feed.xml"):
        root=copy.deepcopy(original_root)
        channel=root.find("channel")
        atom=channel.find(f"{{{ATOM}}}link")
        if atom is None:atom=ET.SubElement(channel,f"{{{ATOM}}}link")
        atom.set("href",URLBASE+filename)
        atom.set("rel","self")
        atom.set("type","application/rss+xml")
        ET.indent(root,space="  ")
        payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
        # Validate BEFORE touching either subscribed file.
        ET.fromstring(payload)
        result[filename]=payload
    report={
        "state":"published",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "subscription_urls":[URLBASE+"feed-v2.xml",URLBASE+"feed.xml"],
        "episode_count":len(combined),
        "special_prefix":20,
        "previous_episode_count":old_count,
        "new_actual_plays":20,
        "new_groups":[{"section":"remote-complex","start":old_count+1,"end":old_count+10},
                      {"section":"ancient-sith-ruins","start":old_count+11,"end":old_count+20},
                      {"section":"moraband-new-fiction-and-play","start":old_count+21,"end":old_count+30},
                      {"section":"shard-moon-new-fiction-and-play","start":old_count+31,"end":old_count+40}],
        "new_unique_productions":expansion_status["new_publisher_programs"] + bonus_status["unique_productions"],
        "bonus_episodes":20,
        "bonus_drama_count":10,
        "bonus_actual_play_count":10,
        "ranked_source_entries":len(ranked),
        "legacy_original_count":len(legacy),
        "original_subscriber_guids_preserved":len(expected_guids),
        "legacy_unique_appended":legacy_extra,
        "duplicates_removed":len(legacy)-legacy_extra,
        "all_new_audio_owned_by_publishers":True,
        "old_sampler_source":"sampler-v2.xml",
        "ranked_source":"learning-feed-v2.xml",
        "warnings":[]
    }
    result["subscriber-status.json"]=(json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    for filename,payload in result.items():
        atomic(HERE/filename,payload)
    print("PASS: refreshed ORIGINAL Star Wars RSS",report)

if __name__=="__main__":
    build()
