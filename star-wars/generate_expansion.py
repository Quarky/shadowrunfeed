#!/usr/bin/env python3
"""Select exactly 20 existing verified publisher-hosted actual-play episodes.

Ten general remote/alien/automated-facility sessions, followed by ten Star Wars
dark-side/ancient-ruins sessions. Keep public descriptions generic and private
campaign canon outside public source. Abort on missing title or invalid audio.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from generate_learning import HERE,ITUNES,ATOM,url_bytes,verified_episode,norm

CFG=json.loads((HERE/"expansion-catalog.json").read_text(encoding="utf-8"))
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)

def lookup_publisher(show):
    import urllib.parse
    query=urllib.parse.urlencode({"id":int(show["apple_id"]),"country":"us","entity":"podcast"})
    result=json.loads(url_bytes("https://itunes.apple.com/lookup?"+query))
    matches=[r for r in result.get("results",[]) if r.get("collectionId")==int(show["apple_id"]) and r.get("feedUrl")]
    if len(matches)!=1:raise ValueError("Apple Podcasts publisher RSS lookup not unique")
    rss=matches[0]["feedUrl"]
    root=ET.fromstring(url_bytes(rss))
    channel=root.find("channel")
    if root.tag!="rss" or channel is None:raise ValueError("No valid publisher RSS")
    return rss,channel.findall("item")

def cleaned(s):
    return re.sub(r"[^a-z0-9]+"," ",(s or "").casefold()).strip()

def choose_episode(row,rss,items):
    terms=[cleaned(t) for t in row["terms"]]
    candidate=[]
    for item in items:
        title=item.findtext("title") or ""
        nt=cleaned(title)
        if any(block in nt for block in (" trailer "," teaser "," preview "," outtakes "," roundtable ")):continue
        matching=[len(t) for t in terms if t in nt]
        if not matching:continue
        candidate.append((max(matching),title,item))

    candidate=[c for c in candidate if not any(bad in cleaned(c[1]) for bad in (
        "debrief","behind the scenes","asset creation","making of","roundtable",
        "character creation","interview","review","gm tips","table talk","retrospective"))]
    if row.get("series_ordinal"):
        def serial_sort(title):
            parts=re.search("part\\s*([0-9]+)(?:[.]([0-9]+))?",title.casefold())
            return (int(parts.group(1)),int(parts.group(2) or 0)) if parts else (999,999)
        candidate.sort(key=lambda c:(serial_sort(c[1]),-c[0],len(c[1])))
        if len(candidate)<row["series_ordinal"]:
            raise ValueError("Requested series ordinal not present in RSS")
        candidate=[candidate[row["series_ordinal"]-1]]
    else:
        candidate.sort(key=lambda x:(x[0],-len(x[1])),reverse=True)
    if not candidate:
        # Diagnostics for maintaining exact title references, never pick random.
        examples=[(it.findtext("title") or "")[:95] for it in items[:8]]
        raise ValueError("No exact editorial title match; publisher recent episodes="+repr(examples))
    if len(candidate)>1 and candidate[0][0]==candidate[1][0] and cleaned(candidate[0][1])==cleaned(candidate[1][1]):
        raise ValueError("Ambiguous duplicate source episode title")
    _,title,item=candidate[0]
    verified=verified_episode(item)
    if verified is None:raise ValueError("Selected episode has no verifiable HTTPS MP3 enclosure and length: "+title)
    enc=verified.find("enclosure")
    link=verified.findtext("link") or rss
    return {"row":row,"item":verified,"rss":rss,"episode":title,
            "publisher_audio_url":enc.get("url"),"episode_page":link}

def gather_source(pair):
    row,source=pair
    try:
        return choose_episode(row,source["rss"],source["items"]),None
    except Exception as error:
        return None,{"id":row["id"],"show":row["show"],"error":str(error)[:1000]}

def atomically_write(name,data):
    output=HERE/name
    tmp=HERE/(name+".tmp")
    tmp.write_bytes(data)
    tmp.replace(output)

def main():
    if len(CFG["entries"])!=20:raise RuntimeError("Expected twenty remote-science episodes and ten Sith-ruins episodes")
    shows={}
    diagnostics=[]
    for row in CFG["entries"]:
        apple_id=row["apple_id"]
        if apple_id in shows:continue
        try:
            rss,items=lookup_publisher(row)
            shows[apple_id]={"rss":rss,"items":items}
            print("SOURCE",apple_id,row["show"],len(items),"RSS episodes")
        except Exception as error:
            diagnostics.append({"id":row["id"],"show":row["show"],"error":str(error)[:550]})
    selected=[]
    for row in CFG["entries"]:
        if row["apple_id"] not in shows:continue
        picked,error=gather_source((row,shows[row["apple_id"]]))
        if error:diagnostics.append(error);print("MISSING",row["id"],error["error"])
        elif picked:
            selected.append(picked)
            print("SELECTED",row["id"],"::",picked["episode"])
    if len(selected)!=20:
        print("VALIDATION MISSING:",json.dumps(diagnostics,indent=2))
        raise RuntimeError("Refusing partial podcast publication: "+str(len(selected))+"/20 verified sources")
    used_ids=set();used_audio=set()
    for selection in selected:
        ident=selection["row"]["id"]
        audio=selection["publisher_audio_url"]
        if ident in used_ids or audio in used_audio:
            raise RuntimeError("Duplicate publisher audio or playlist identity")
        used_ids.add(ident);used_audio.add(audio)
    assert all(e["row"]["group"]=="remote-complex" for e in selected[:10])
    assert all(e["row"]["group"]=="sith-ruins" for e in selected[10:])
    root=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(root,"channel")
    def put(parent,tag,value):
        e=ET.SubElement(parent,tag);e.text=str(value);return e
    put(channel,"title","Star Wars RPG — Additional Actual Play Inspiration")
    put(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/star-wars")
    put(channel,"description","Twenty actual-play selections. First twenty: hazardous research installations, ruins and sci-fi survival. Following ten: ancient Sith relics, tombs and dark-side mysteries. Non-Star-Wars games are labeled as cross-genre inspiration.")
    put(channel,"language","en")
    put(channel,f"{{{ITUNES}}}author","Independent RPG Listening Index")
    ET.SubElement(channel,f"{{{ITUNES}}}image",{"href":"https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/cover.png"})
    ET.SubElement(channel,f"{{{ATOM}}}link",{"href":"https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/expansion.xml","rel":"self","type":"application/rss+xml"})
    rows=[]
    for n,e in enumerate(selected,1):
        row=e["row"]
        orig=e["item"]
        item=ET.SubElement(channel,"item")
        kind="STAR WARS ACTUAL PLAY" if row["star_wars"] else "CROSS-GENRE SCI-FI ACTUAL PLAY"
        put(item,"title",f"{n:02d} · {kind} · [{row['show']}] {e['episode']}")
        guid=put(item,"guid","urn:sw-new-actual-play:"+hashlib.sha256((row["id"]+"|"+cleaned(e["episode"])).encode()).hexdigest())
        guid.set("isPermaLink","false")
        put(item,"link",e["episode_page"])
        publication=orig.findtext("pubDate") or ""
        detail=(orig.findtext("description") or "")[:450]
        qualifier="Star Wars actual play; " if row["star_wars"] else "OTHER SCI-FI SETTING, not Star Wars canon; "
        context=row.get("context_warning","")
        put(item,"description",qualifier+row["learning"]+
            " System: "+row["system"]+". "+context+
            " Original publication: "+publication+". Publisher notes: "+detail)
        put(item,"pubDate",publication or "Mon, 01 Jan 2024 00:00:00 +0000")
        enc=orig.find("enclosure")
        ET.SubElement(item,"enclosure",{"url":enc.get("url"),
                 "length":enc.get("length"),"type":enc.get("type") or "audio/mpeg"})
        duration=orig.findtext(f"{{{ITUNES}}}duration")
        if duration:put(item,f"{{{ITUNES}}}duration",duration)
        source=put(item,"source",row["show"]);source.set("url",e["rss"])
        rows.append({
            "new_selection":n,"source_id":row["id"],"theme":row["group"],
            "publisher":row["show"],"episode":e["episode"],
            "actual_play_system":row["system"],"star_wars_setting":row["star_wars"],
            "episode_url":e["episode_page"],"publisher_audio_url":e["publisher_audio_url"],
            "original_pubDate":publication,"creative_use":row["learning"],
            "mid_series_notice":context or None})
    ET.indent(root,space="  ")
    xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(xml)
    report={"state":"published","generated_utc":datetime.now(timezone.utc).isoformat(),
           "count":len(rows),"first_section":10,"second_section":10,
           "new_publisher_programs":len({r["publisher"] for r in rows}),
           "non_star_wars_actual_plays":sum(not r["star_wars_setting"] for r in rows),
           "no_audio_rehosted":True,"all_enclosures_https_valid":True,"warnings":[]}
    lines=["# Additional Star Wars RPG actual-play inspiration: 20 episodes","",
        "Twenty existing expansion episodes appended **after** the original Star Wars subscriber's existing seventy. First ten are remote-complex/experimental-science/survival inspired; next ten are Sith-temple, relic, tomb and Force inspired. These are broad public genres only, never private campaign story canon.",
        "",
        "Some shows are other science-fiction systems, **not Star Wars**; they provide encounter structure and world portrayal without being Star Wars source lore. An episode explicitly marked *mid-arc* may need preceding story context.",
        "",
        "| New # | Theme | Show / verified playable episode | System | Idea |",
        "| ---: | --- | --- | --- | --- |"]
    for row in rows:
        name=row["episode"].replace("|","–")
        idea=row["creative_use"].replace("|","–")
        lines.append(f'| {row["new_selection"]} | {row["theme"].replace("-"," ")} | [{name}]({row["episode_url"]}) — {row["publisher"]} | {row["actual_play_system"]} | {idea} |')
    lines+=["","**No audio is mirrored.** RSS episodes always link to the original publisher's HTTPS recording. The main [Star Wars subscription](feed-v2.xml) remains the same URL.", ""]
    outputs={
       "expansion.xml":xml,
       "expansion-episodes.json":(json.dumps({"episodes":rows,"generated_utc":report["generated_utc"]},indent=2,ensure_ascii=False)+"\n").encode(),
       "expansion-episodes.md":"\n".join(lines).encode(),
       "expansion-status.json":(json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode(),
    }
    for name,bytes_ in outputs.items():atomically_write(name,bytes_)
    print("VERIFIED:",len(rows),"actual-play podcast episode references; separately generated.")

if __name__=="__main__":
    main()
