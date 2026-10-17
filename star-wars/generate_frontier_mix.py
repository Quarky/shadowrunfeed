#!/usr/bin/env python3
"""Independent 20-episode Star Wars RPG inspiration mix.

Ten scene-oriented dramatized/actual-play episodes followed by five familiar
lore/story pairs. All enclosures are verified publisher-provided URLs. Audio,
private campaign names, and any commercial audiobooks are NEVER hosted here.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

from generate_learning import (HERE, PUBLIC, REPO, ITUNES, ATOM, original_date,
                               url_bytes, verified_episode)

CONFIG=json.loads((HERE/"frontier-mix-catalog.json").read_text(encoding="utf-8"))
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)

def normalized(text):
    return re.sub(r"\s+"," ",(text or "").casefold().replace("’","'")).strip()

def publisher_drama_pilot(show):
    query=urllib.parse.urlencode({"id":int(show["apple_id"]),"entity":"podcast","country":"us"})
    lookup=json.loads(url_bytes("https://itunes.apple.com/lookup?"+query))
    rows=[x for x in lookup.get("results",[]) if x.get("collectionId")==show["apple_id"] and x.get("feedUrl")]
    if len(rows)!=1:raise ValueError("No unique podcast lookup RSS")
    rss=rows[0]["feedUrl"]
    feed=ET.fromstring(url_bytes(rss))
    channel=feed.find("channel")
    if feed.tag!="rss" or channel is None:
        raise ValueError("Publisher URL did not return RSS")
    items=channel.findall("item")
    if not items:raise ValueError("Publisher RSS has no episodes")
    def trailer(x):
        t=normalized(x.findtext("title"))
        return (x.findtext(f"{{{ITUNES}}}episodeType") or "").casefold()=="trailer" or any(
            term in t for term in ("trailer","teaser","preview","coming soon","announcement","reintroduction"))
    items=[x for x in items if not trailer(x)]
    def check_title(x):
        t=normalized(x.findtext("title"))
        priority=[]
        for ix,fragment in enumerate(show["pilot_fragments"]):
            search=normalized(fragment)
            if search in t and (not re.search(r"\bepisode 1\d\b",t) or re.search(r"\bepisode 1\b",t)):
                priority.append((len(show["pilot_fragments"])-ix)*10+min(20,len(search)))
        # Prefer explicit iTunes season 1 episode 1 ONLY when there is no
        # better title match.
        itunes_season=x.findtext(f"{{{ITUNES}}}season")
        itunes_ep=x.findtext(f"{{{ITUNES}}}episode")
        if itunes_season=="1" and itunes_ep=="1":priority.append(30)
        if not priority:return None
        return max(priority)
    candidates=sorted(((check_title(x),x) for x in items),key=lambda x:x[0] or 0,reverse=True)
    candidates=[x for priority,x in candidates if priority is not None]
    if not candidates:raise ValueError("No verified first chapter in publisher RSS")
    failures=[]
    for candidate in candidates[:7]:
        checked=verified_episode(candidate)
        if checked is None:
            failures.append(candidate.findtext("title") or "?")
            continue
        return {"source_id":show["id"],"source":{"title":show["title"],"why":show["motive"],
                "publisher_site":show["page"],"kind":"cross-genre audio drama"},
                "item":checked,"rss":rss,"title":checked.findtext("title") or "",
                "role":"DRAMA","score":80.0,"themes":["environment","investigation","character"],
                "chap":1,"date":original_date(checked)}
    raise ValueError("First chapter(s) lack valid publisher audio: "+", ".join(failures))

def original_entry(row,by_url,role,purpose):
    uri=row.get("publisher_audio_url")
    if uri not in by_url:raise ValueError("Existing verified episode missing from its original published RSS")
    item=copy.deepcopy(by_url[uri])
    title=row["episode"]
    el=item.find("title")
    if el is None:el=ET.SubElement(item,"title")
    el.text=title
    d=item.find("pubDate")
    if d is None:d=ET.SubElement(item,"pubDate")
    d.text=row.get("original_date") or ""
    source_el=item.find("source")
    publisher_rss=source_el.get("url") if source_el is not None else PUBLIC+"learning-feed-v2.xml"
    rating=(dict(stars=row["show_rating_us"],count=row["show_rating_count_us"]) if
            row.get("show_rating_us") is not None and row.get("show_rating_count_us") is not None else None)
    return {"source_id":row["source_id"],
            "source":{"title":row["show"],"why":purpose or row.get("inspiration",""),
                      "kind":"Star Wars RPG original actual play or lore",
                      "rating":rating},
            "item":item,"rss":publisher_rss,"title":title,"role":role,
            "score":row["editorial_score"],"themes":row.get("themes",[]),
            "chap":row.get("story_chapter"),"date":original_date(item)}

def load_verified_previous():
    status=json.loads((HERE/"learning-status.json").read_text(encoding="utf-8"))
    if status.get("state")!="published" or status.get("pairs",0)<5:
        raise RuntimeError("The ordinary lore/story feed has not been verified")
    rows=json.loads((HERE/"learning-episodes.json").read_text(encoding="utf-8"))["episodes"]
    root=ET.parse(HERE/"learning-feed-v2.xml").getroot()
    channel=root.find("channel")
    if channel is None:raise RuntimeError("Original published RSS is invalid")
    mapping={}
    for item in channel.findall("item"):
        enclosure=item.find("enclosure")
        if enclosure is not None and enclosure.get("url"):
            mapping[enclosure.get("url")]=item
    return rows,mapping

def select_original_actual_plays(rows,by_url):
    output=[]
    for request in CONFIG["actual_plays"]:
        found=[r for r in rows if r["kind"]=="STORY" and r["source_id"]==request["arc"]
               and r["story_chapter"]==request["chapter"]]
        if len(found)!=1:
            raise ValueError("Need exactly one source-verified first chapter for "+request["arc"])
        output.append(original_entry(found[0],by_url,"ACTUAL_PLAY",request["purpose"]))
    if len(output)!=5:raise RuntimeError("Five unique actual plays required")
    return output

def select_followup_pairs(rows,by_url,already_used):
    # Select 5 consecutive lore and story pairs from the existing published
    # playlist; avoid repeating any audio in the themed ten. Since the opening
    # five normal pairs are one intact arc, the story chapters remain complete.
    out=[]
    for n in range(0,len(rows)-1,2):
        lore,story=rows[n:n+2]
        if lore["kind"]!="LORE" or story["kind"]!="STORY":
            raise ValueError("Existing ranked feed violates expected pairing")
        if any(r["publisher_audio_url"] in already_used for r in (lore,story)):
            continue
        # Subsequent story arc continuation is preserved: only start at chapter
        # 1, then advance by one chapter until five pairs are chosen.
        if out:
            last=out[-1]
            if story["source_id"]!=last["source_id"] or story["story_chapter"]!=last["chap"]+1:
                continue
        elif story["story_chapter"]!=1:
            continue
        out.append(original_entry(lore,by_url,"LORE","Conventional world lore and character context"))
        out.append(original_entry(story,by_url,"STORY","Consecutive character-driven actual play"))
        if len(out)==10:break
    if len(out)!=10:raise RuntimeError("Five normal pairs with contiguous story chapters not available")
    return out

def xml_feed(entries):
    root=ET.Element("rss",{"version":"2.0"})
    ch=ET.SubElement(root,"channel")
    def put(parent,tag,value):
        el=ET.SubElement(parent,tag);el.text=str(value);return el
    put(ch,"title","Star Wars RPG — Frontier Mystery, Audio Drama & Actual Play")
    put(ch,"link",REPO)
    put(ch,"description","General space-opera RPG inspiration: first five audio dramas alternating with five Star Wars actual plays, then five lore/story pairs. Cross-genre non-Star-Wars fiction is explicitly labeled. Publisher-hosted audio only.")
    put(ch,"language","en")
    put(ch,"copyright","Original recordings and book adaptations remain copyrighted by their original publishers.")
    put(ch,f"{{{ITUNES}}}author","Independent RPG Audio Listening Index")
    put(ch,f"{{{ITUNES}}}type","episodic")
    put(ch,f"{{{ITUNES}}}summary","Dramatized isolated research outposts, ancient ruins, survival failures, expedition NPCs and Star Wars actual play.")
    ET.SubElement(ch,f"{{{ITUNES}}}image",{"href":PUBLIC+"cover.png"})
    ET.SubElement(ch,f"{{{ATOM}}}link",{"href":PUBLIC+"frontier-mix.xml","rel":"self","type":"application/rss+xml"})
    for n,e in enumerate(entries,1):
        item=ET.SubElement(ch,"item")
        prefix="CROSS-GENRE INSPIRATION" if e["role"]=="DRAMA" else e["role"]
        put(item,"title",f"{n:02d} · {prefix} · [{e['source']['title']}] {e['title']}")
        encl=e["item"].find("enclosure")
        digest=hashlib.sha256((e["source_id"]+"|"+encl.get("url")).encode()).hexdigest()
        guid=put(item,"guid","urn:sw-frontier:"+digest);guid.set("isPermaLink","false")
        link=e["item"].findtext("link") or e["source"].get("publisher_site") or REPO
        put(item,"link",link)
        notes=(e["item"].findtext("description") or "")[:350]
        put(item,"description",f"Role: {e['role']}. {('NON-STAR-WARS FICTION, used for adaptable mood only. ' if e['role']=='DRAMA' else '')}Creative use: {e['source']['why']}. Original date: {e['item'].findtext('pubDate') or 'unknown'}. Publisher: {e['source']['title']}. Original summary: {notes}")
        # Stable synthetic dates enable newest-first players to display the
        # intentional curated sequence; original publication is in notes.
        put(item,"pubDate",format_datetime(datetime(2026,10,17,14,0,tzinfo=timezone.utc)-timedelta(minutes=n)))
        ET.SubElement(item,"enclosure",{"url":encl.get("url"),"length":encl.get("length"),
                                       "type":encl.get("type") or "audio/mpeg"})
        for tag in ("duration","explicit"):
            value=e["item"].findtext(f"{{{ITUNES}}}{tag}")
            if value:put(item,f"{{{ITUNES}}}{tag}",value)
        source=put(item,"source",e["source"]["title"]);source.set("url",e["rss"])
    ET.indent(root,space="  ")
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(xml)
    return xml

def episode_rows(entries):
    rows=[]
    for pos,e in enumerate(entries,1):
        el=e["item"];rating=e["source"].get("rating") or {}
        rows.append({"order":pos,"category":e["role"],"show":e["source"]["title"],
                     "episode":e["title"],"inspiration":e["source"]["why"],
                     "original_date":el.findtext("pubDate"),
                     "episode_page":el.findtext("link") or e["source"].get("publisher_site") or e["rss"],
                     "publisher_audio_url":el.find("enclosure").get("url"),
                     "show_rating_us":rating.get("stars"),"review_count_us":rating.get("count"),
                     "editorial_score":e["score"],"story_chapter":e["chap"],
                     "continuity":"Non-Star-Wars cross-genre inspiration" if e["role"]=="DRAMA" else "Star Wars RPG / setting"})
    return rows

def notes_markdown(rows):
    lines=["# Frontier Mystery — Audio Drama & Star Wars RPG Story Mix","",
          "A public, generic science-fiction idea library. No private adventure identifiers or original campaign lore are included.",
          "",
          "**Tracks 1–10:** Five complete publisher-hosted podcast-drama pilot episodes and five Star Wars live-play campaign openings, alternating DRAMA → ACTUAL PLAY. No lore commentary interrupts these ten tracks.",
          "",
          "**Tracks 11–20:** Five ordinary LORE → STORY pairs, retaining consecutive story chapters and avoiding repeated episodes.",
          "",
          "**Cross-genre warning:** The audio dramas are independent science-fiction or horror fiction, **not** official Star Wars canon. Borrow scene techniques and environmental ideas, not their setting canon.",
          "",
          "| Play | Kind | Publisher-hosted episode | Inspiration |",
          "| ---: | --- | --- | --- |"]
    for row in rows:
        title=row["episode"].replace("|","–")
        why=row["inspiration"].replace("|","–")
        url=row["episode_page"]
        if not url or url.rstrip("/") in ("https://thelorehounds.com","https://www.theswu.com"):
            url=row["publisher_audio_url"]
        lines.append(f'| {row["order"]} | {row["category"]} | [{title}]({url}) — {row["show"]} | {why} |')
    lines+=["","## Commercial official full-cast audio productions (links only; not RSS entries)","",
            "These are legitimate audiobooks/audio dramas. **Paid/book-marketplace recordings are not copied into a public RSS feed.**"]
    for book in CONFIG["official_star_wars_audio_books"]:
        lines.append(f'- [{book["title"]}]({book["url"]}) — {book["use"]} ({book["type"]})')
    lines+=["","## Publication and continuity safeguards","",
            "- Publisher episode audio is linked by source RSS enclosure; audio files are neither rehosted nor altered.",
            "- The first ten draw from five distinct dramatized shows and five different Star Wars RPG story arcs.",
            "- The last five normal story entries are a single consecutive story sequence, paired with five ranked lore episodes.",
            "- The two sections are designed as separate modes; individual drama pilots are not represented as a complete five-season storyline.",
            "- [Full machine-readable episode list](frontier-mix-episodes.json) and [publication validation](frontier-mix-status.json).",
            ""]
    return "\n".join(lines)

def atomic_bytes(path,bytes_data):
    tmp=HERE/(path+".tmp")
    tmp.write_bytes(bytes_data)
    tmp.replace(HERE/path)

def main():
    report={"state":"building","built_at":datetime.now(timezone.utc).isoformat(),
            "dramas":[],"actual_plays":[],"normal_pairs":0,"publisher_audio_rehosted":False,"warnings":[]}
    normal_rows,by_url=load_verified_previous()
    dramas=[]
    for show in CONFIG["dramas"]:
        try:
            result=publisher_drama_pilot(show)
            dramas.append(result)
            report["dramas"].append({"id":show["id"],"status":"verified","episode":result["title"]})
        except Exception as ex:
            report["dramas"].append({"id":show["id"],"status":"unavailable","reason":str(ex)[:250]})
            report["warnings"].append("Could not verify "+show["id"])
    # Never invent material or present 4 stories as the requested 5.
    if len(dramas)!=5:raise RuntimeError(f"Need five original audio dramas; only {len(dramas)} verified: {report['warnings']}")
    plays=select_original_actual_plays(normal_rows,by_url)
    report["actual_plays"]=[{"id":e["source_id"],"episode":e["title"]} for e in plays]
    themed=[]
    for drama,play in zip(dramas,plays):themed.extend((drama,play))
    used={e["item"].find("enclosure").get("url") for e in themed}
    ordinary=select_followup_pairs(normal_rows,by_url,used)
    out=themed+ordinary
    if len(out)!=20:raise RuntimeError("Unexpected episode count")
    urls=[e["item"].find("enclosure").get("url") for e in out]
    if len(set(urls))!=20:raise RuntimeError("Duplicated source audio in mix")
    expected=(["DRAMA","ACTUAL_PLAY"]*5)+(["LORE","STORY"]*5)
    if [e["role"] for e in out]!=expected:raise RuntimeError("Unexpected listening pattern")
    for e in out:
        enc=e["item"].find("enclosure")
        if not enc or not enc.get("url","").startswith("https://") or int(enc.get("length","0"))<1:
            raise RuntimeError("Invalid source-verified publisher enclosure")
    rows=episode_rows(out)
    files={
        "frontier-mix.xml":xml_feed(out),
        "frontier-mix-episodes.md":notes_markdown(rows).encode("utf-8"),
        "frontier-mix-episodes.json":(json.dumps({"built_at":report["built_at"],"episodes":rows},indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    }
    # Build all outputs before publishing any.
    for name,data in files.items():atomic_bytes(name,data)
    report["state"]="published";report["count"]=len(out);report["themed_count"]=len(themed)
    report["drama_count"]=len(dramas);report["actual_play_count"]=len(plays)
    report["normal_pairs"]=len(ordinary)//2
    atomic_bytes("frontier-mix-status.json",(json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode())
    print("Published",report["count"],"verified podcast recordings in the requested 10+5-pairs sequence")

if __name__=="__main__":
    main()
