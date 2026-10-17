#!/usr/bin/env python3
"""Generate stable base lore/story playlist for the main combined podcast feed.

Independent of existing FFG/D6 podcast samplers; final main feed is assembled later.
No private campaign information. No invented RSS enclosures or episode ratings.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from generate_feed import checked_sampler_item

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/"learning_catalog.json").read_text(encoding="utf-8"))
PUBLIC="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/"
REPO="https://github.com/Quarky/shadowrunfeed/tree/main/star-wars"
ITUNES="http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM="http://www.w3.org/2005/Atom"
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)
USER_AGENT="FantasyAndStarWarsRPGListeningLibrary/1.0 (+https://github.com/Quarky/shadowrunfeed)"
STOPWORDS={"the","of","and","a","on","to","for","in","from","at","an","vs","with","star","wars"}

def norm(s):
    return re.sub(r"\s+"," ",(s or "").casefold().strip())

def url_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=35) as response:
        data=response.read(18_000_000)
    if not data:raise ValueError("Empty source")
    return data

def original_date(item):
    try:
        d=parsedate_to_datetime(item.findtext("pubDate") or "")
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError,TypeError,IndexError):
        return datetime(2000,1,1,tzinfo=timezone.utc)

def remote_lore_items(source):
    iid=int(source["apple_id"])
    query=urllib.parse.urlencode({"id":iid,"country":"us","entity":"podcast"})
    response=json.loads(url_bytes("https://itunes.apple.com/lookup?"+query))
    rows=[r for r in response.get("results",[]) if r.get("collectionId")==iid and r.get("feedUrl")]
    if len(rows)!=1:raise ValueError(f"No unique publisher RSS via Apple lookup for {iid}")
    rss_url=rows[0]["feedUrl"]
    root=ET.fromstring(url_bytes(rss_url))
    channel=root.find("channel")
    if root.tag!="rss" or channel is None:
        raise ValueError(f"Invalid publisher RSS at {rss_url}")
    items=channel.findall("item")
    if not items:raise ValueError(f"No publisher episodes at {rss_url}")
    return rss_url,items

def is_lore(item,source):
    title=norm(item.findtext("title"))
    description=norm(ET.tostring(item.find("description"),encoding="unicode",method="text") if item.find("description") is not None else "")
    if not title or any(term in title for term in CFG["blacklist"]):return None
    if re.search(r"\blast\b.{0,25}\bweeks?\b",title) or "best of" in title:
        return None
    # Do not introduce a serialized lore explanation at chapter 2 or later.
    if re.search(r"\b(?:part|pt\.?)\s*[2-9]\b",title):return None
    mode=source.get("mode","")
    if mode=="character" and ("calendar" in title or "special" in title and "character" not in title):
        return None
    if mode=="explained" and any(x in title for x in (
        "last week","reaction","reviews","chapter ","this is the show",
        "live discussion","what to read","what to watch","watch before",
        "season three","season two","rumor","new show","trailer","commentary",
        "movie discussion","podcast","you missed","watching","episodes")):
        return None
    if mode=="explained":
        # This mixed-genre feed publishes weekly entertainment news and reviews
        # as well as evergreen lore. Require a genuine lore-bearing headline.
        if any(x in title for x in (
            "live","updates","the good, the bad","movie","biggest questions",
            "the book of boba fett","mandalorian and grogu",
            "trailer","upcoming","release","reaction","ranking","explaining the news",
            "new star wars","what we know","premiere","star wars fans","rewatch")):
            return None
        if not any(x in title for x in (
            "lore","history","timeline","explained","origins","species",
            "ancient","sith lord","jedi order","sith order","holocron",
            "technology","droid","starship","weapon","who is","all about",
            "what is","force power","how does","everything you need","creature",
            "planet","culture","faction","mandalorian history","force lore",
            "the mystery of","dark side","lightsaber")):
            return None
    if source["id"]=="eye-on-canon" and any(x in title for x in (
        "big screen","publishing","episode special","200th","watch party",
        "movie review","season review","all about maul","future of star wars",
        "live watch","trailer","what's new","what we think")):
        return None
    if source["id"]=="old-canon-book-club" and any(x in title for x in (
        "return of return","movie review","season 2","episode special",
        "tracking bantha","production history","box office","film review")):
        return None
    # Explicit lexical signals. Prevent news/promotion episodes of mixed feeds.
    title_hits=sum(bool(re.search(r"\b"+re.escape(term)+r"\b",title)) for cat in CFG["themes"].values() for term in cat["terms"])
    summary_hits=sum(term in description for term in CFG["spotlight"])
    if mode=="character" and ("in character" in title or "swic" in title):
        title_hits=max(1,title_hits)
    if mode=="history" and any(w in title for w in ("era ","old republic","canon","folklore","legends","history","high republic")):
        title_hits=max(1,title_hits)
    if not title_hits and summary_hits<2:return None
    themes=[key for key,val in CFG["themes"].items() if any(w in title or w in description[:550] for w in val["terms"])]
    return {"title_hits":title_hits,"summary_hits":summary_hits,"themes":themes or ["npc"]}

def verified_episode(item):
    try:
        checked=checked_sampler_item(item)
    except Exception:
        return None
    if checked is None:return None
    audio=checked.find("enclosure")
    if audio is None:return None
    try: size=int(audio.get("length","0"))
    except ValueError:return None
    return checked if size>0 and audio.get("url","").startswith("https://") else None

def pick_lore(source):
    rss,episodes=remote_lore_items(source)
    candidates=[]
    for item in episodes:
        review=is_lore(item,source)
        if review:
            score=review["title_hits"]*7+min(6,review["summary_hits"])*2
            score+=sum(s in norm(item.findtext("title")) for s in CFG["spotlight"])*3
            candidates.append((score,original_date(item),item,review))
    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
    sampled=candidates[:source.get("max_candidates",24)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        valid=list(pool.map(lambda x:verified_episode(x[2]),sampled))
    output=[];seen=set()
    for (priority,date,_,review),checked in zip(sampled,valid):
        if checked is None:continue
        uri=checked.find("enclosure").get("url")
        if uri in seen:continue
        seen.add(uri)
        output.append({
            "source_id":source["id"],"source":source,"rss":rss,
            "title":checked.findtext("title") or "Untitled",
            "item":checked,"role":"LORE","chap":None,"priority":priority,
            "date":date,"themes":review["themes"]})
    return output

NUMBER_WORDS=["One","Two","Three","Four","Five","Six","Seven","Eight"]
def chapter_num(arc,title):
    key=arc["match"]
    if key=="english_number":
        clean=re.sub(r"\s+"," ",title).strip().casefold()
        for n,word in enumerate(NUMBER_WORDS,1):
            if clean=="episode "+word.casefold():return n
        return None
    expressions={
       "coldfire":r"Coldfire Chronicles S0?1\s*E(?:p(?:isode)?)?[\s.:-]*0?(\d+)\b",
       "dice":r"Dice For Brains Podcast\s*\|\s*Episode\s*(\d+)\b",
       "empire-edge":r"Empire['’]s Edge\s*-\s*Ep\.?\s*0?(\d+)\b",
       "empires-end":r"^Empire['’]s End\s*(\d+)\s*:",
       "dreamscapes":r"^Star Wars:\s*Dreamscapes\s*-\s*Ep\.?\s*(\d+)\b",
    }
    pat=expressions.get(key)
    if not pat:raise ValueError("Unknown story series selector "+str(key))
    match=re.search(pat,title,re.IGNORECASE)
    return int(match.group(1)) if match else None

def pick_story(arc):
    path=HERE/arc["feed"]
    if not path.is_file():raise ValueError(f"Missing verified source playlist: {arc['feed']}")
    root=ET.parse(path).getroot()
    channel=root.find("channel")
    if channel is None:raise ValueError("Missing story podcast channel")
    items={}
    for it in channel.findall("item"):
        n=chapter_num(arc,it.findtext("title") or "")
        if n is None or n>arc["max_chapters"]:continue
        items.setdefault(n,[]).append(it)
    output=[]
    for n in range(1,arc["max_chapters"]+1):
        found=items.get(n,[])
        if len(found)!=1:
            break  # no out-of-context chapters and no invented recordings
        valid=verified_episode(found[0])
        if valid is None:break
        output.append({
          "source_id":arc["id"],"source":arc,
          "rss":PUBLIC+arc["feed"],"title":valid.findtext("title") or "",
          "item":valid,"role":"STORY","chap":n,"priority":7,
          "date":original_date(valid),"themes":["npc"]})
    return output

def show_score(source):
    rating=source.get("show_rating") or source.get("rating")
    cfg=CFG["methodology"]
    stars=rating["stars"] if rating else cfg["rating_prior"]
    count=rating["count"] if rating else 0
    bayes=(count*stars+cfg["rating_prior_votes"]*cfg["rating_prior"])/(count+cfg["rating_prior_votes"])
    return max(0.0,min(1.0,(bayes-3.5)/1.5))

def text_score(entry):
    title=norm(entry["title"])
    desc=norm((entry["item"].findtext("description") or "")[:1300])
    title_hits=sum(any(word in title for word in t["terms"]) for t in CFG["themes"].values())
    desc_hits=sum(any(word in desc for word in t["terms"]) for t in CFG["themes"].values())
    spotlight=sum(word in title for word in CFG["spotlight"])
    return min(1,0.22+0.10*title_hits+0.045*desc_hits+0.06*spotlight)

def npc_score(entry):
    hay=norm(entry["title"]+" "+(entry["item"].findtext("description") or "")[:700])
    terms=["crew","alliance","betray","character","negotiat","friend","politic","cantina",
           "investigation","underworld","dialogue","villain","mystery","society",
           "family","prison","faction","bounty","mission","discovery","conflict","temple","force"]
    base=0.32+0.055*sum(w in hay for w in terms)
    return max(0.81,min(1,base)) if entry["role"]=="STORY" else min(1,base)

def score(entry):
    weights=CFG["methodology"]["score_weights"]
    value=100*(weights["episode_relevance"]*text_score(entry)+
               weights["npc_story_utility"]*npc_score(entry)+
               weights["show_rating"]*show_score(entry["source"])+
               weights["diversity"]*.70)
    entry["score"]=round(value,2)
    return entry["score"]

def title_family(entry):
    title=norm(entry["title"])
    if any(w in title for w in ("sith","jedi","force","holocron","kyber")):return "force"
    if any(w in title for w in ("species","alien","wookiee","ewok","rancor","sarlacc","hutt")):return "species"
    if any(w in title for w in ("planet","old republic","history","canon","legends")):return "history"
    if any(w in title for w in ("droid","ship","technology","lightsaber")):return "tech"
    return "society"

def build_story_order(arcs):
    # Alternate 4/5-chapter story blocks; every individual arc is sequential.
    # Campaign chronology is not interleaved with unrelated campaigns.
    ranked=sorted((arc for arc in arcs if arc["entries"]),key=lambda x:
          (-len(x["entries"]),-float(x.get("community_bonus",0)),x["id"]))
    out=[]
    for arc in ranked:
        out.extend(arc["entries"])
    return out[:CFG["methodology"]["max_pairs"]]

def rank(lore,story_arcs):
    story=build_story_order(story_arcs)
    if len(story)<10:raise RuntimeError(f"Only {len(story)} verified continuous story chapters")
    if len(lore)<10:raise RuntimeError(f"Only {len(lore)} validated lore episodes")
    for e in lore+story:score(e)
    limit=min(len(story),len(lore),CFG["methodology"]["max_pairs"])
    used=set();seen_shows={};seen_family={};selected=[]
    show_ids={e["source_id"] for e in lore}
    for i in range(limit):
        target=story[i]
        synopsis=norm(target["title"]+" "+(target["item"].findtext("description") or "")[:650])
        options=[]
        for e in lore:
            uri=e["item"].find("enclosure").get("url")
            if uri in used:continue
            show=e["source_id"]
            played=seen_shows.get(show,0)
            if played>=CFG["methodology"]["per_lore_show_limit"]:continue
            family=title_family(e)
            novelty= (16 if played==0 else 8 if played==1 else -5*(played-2))
            family_penalty=max(0,seen_family.get(family,0)-1)*5
            common=sum(term in synopsis and term in norm(e["title"]) for term in
                ("jedi","sith","force","planet","droid","crew","republic","imperial",
                 "mystery","artifact","underworld","bounty","alien","species","lore",
                 "temple","mandalorian","ancient","war","faction","ship","pirate"))
            options.append((e["score"]+novelty-family_penalty+min(14,3*common),e))
        if not options:break
        chosen=max(options,key=lambda x:(x[0],x[1]["source_id"]))[1]
        selected.append((chosen,target))
        seen_shows[chosen["source_id"]]=seen_shows.get(chosen["source_id"],0)+1
        fam=title_family(chosen)
        seen_family[fam]=seen_family.get(fam,0)+1
        used.add(chosen["item"].find("enclosure").get("url"))
    if len(selected)<10:raise RuntimeError("Fewer than 10 verified lore/story pairs")
    return [e for pair in selected for e in pair]

def serialize(entries,filename,title):
    root=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(root,"channel")
    def put(tag,value,parent=channel):
        e=ET.SubElement(parent,tag);e.text=str(value);return e
    put("title",title)
    put("link",REPO)
    put("description","Curated independent Star Wars RPG inspiration. Original lore and fully produced actual-play audio remain hosted by their publishers. Ranked playlist alternates research and continuous story chapters. Stars refer only to entire shows, never individual episodes.")
    put("language","en")
    put("copyright","Audio and original program descriptions copyright their publishers.")
    put(f"{{{ITUNES}}}author","Independent Star Wars RPG Listening Index")
    put(f"{{{ITUNES}}}summary","Star Wars lore, species, planets, history, Force mysteries and dramatized RPG storycraft.")
    put(f"{{{ITUNES}}}type","episodic")
    ET.SubElement(channel,f"{{{ITUNES}}}image",{"href":PUBLIC+"cover.png"})
    ET.SubElement(channel,f"{{{ATOM}}}link",{"href":PUBLIC+filename,"rel":"self","type":"application/rss+xml"})
    for index,entry in enumerate(entries,1):
        src=entry["source"];original=entry["item"]
        it=ET.SubElement(channel,"item")
        put("title",f"{index:02d} • {entry['role']} • [{src['title']}] {entry['title']}",it)
        uid=hashlib.sha256((entry["source_id"]+"|"+original.find("enclosure").get("url")).encode()).hexdigest()
        guid=put("guid","urn:sw-learning:"+uid,it);guid.set("isPermaLink","false")
        put("link",original.findtext("link") or src.get("publisher_site") or (src.get("show_rating") or src.get("rating") or {}).get("url") or REPO,it)
        rating=src.get("show_rating") or src.get("rating")
        stars=f"{rating['stars']}/5 over {rating['count']} ratings" if rating else "unrated / unverified"
        description=(original.findtext("description") or "").strip()
        if len(description)>450:description=description[:450]+"…"
        put("description",
            f"Role: {entry['role']}. Publisher show: {src['title']}. US Apple show-wide rating: {stars} (NOT this episode's rating). Editorial algorithm estimate: {entry['score']:.1f}/100. Original publication: {original.findtext('pubDate') or 'unknown'}. Creative application: {src['why']}. Original notes: {description}",it)
        # Most podcast players sort newest first. Stable artificial timestamps
        # encode curated play order while explicitly retaining original dates above.
        put("pubDate",format_datetime(datetime(2026,10,17,15,0,tzinfo=timezone.utc)-timedelta(minutes=index)),it)
        enclosure=original.find("enclosure")
        ET.SubElement(it,"enclosure",{"url":enclosure.get("url"),
              "length":enclosure.get("length"),"type":enclosure.get("type") or "audio/mpeg"})
        for t in ("duration","explicit"):
            val=original.findtext(f"{{{ITUNES}}}{t}")
            if val:put(f"{{{ITUNES}}}{t}",val,it)
        element=put("source",src["title"],it)
        element.set("url",entry["rss"])
    ET.indent(root,space="  ")
    out=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(out)
    return out

def episode_metadata(entries):
    rows=[]
    for n,e in enumerate(entries,1):
        rating=e["source"].get("show_rating") or e["source"].get("rating")
        rows.append({"order":n,"kind":e["role"],"show":e["source"]["title"],
            "episode":e["title"],"source_id":e["source_id"],
            "show_rating_us":rating["stars"] if rating else None,
            "show_rating_count_us":rating["count"] if rating else None,
            "show_rating_reference":rating.get("url") if rating else None,
            "editorial_score":e["score"],"themes":e["themes"],
            "original_date":e["item"].findtext("pubDate"),
            "episode_url":e["item"].findtext("link") or e["rss"],
            "publisher_audio_url":e["item"].find("enclosure").get("url"),
            "story_chapter":e["chap"],"inspiration":e["source"]["why"]})
    return rows

def episode_markdown(rows):
    lines=["# Star Wars RPG — Ranked Lore and Story Listening Order","",
    "Alternating **LORE → STORY**: first learn the lore, then hear a story with NPC dialogue, relationships, factions and consequences. Stories stay in consecutive episode order within each arc.",
    "",
    "**Ratings are show-wide US Apple podcast snapshots, never episode-specific ratings.** Episode scores are editorial algorithms only; titles and publisher audio were verified in original RSS. The synthetic RSS dates implement playlist order; each episode's real broadcast date remains in the JSON/description.",
    "",
    "| Play | Kind | Podcast and episode | Show-level US rating | Editorial score | What to learn |",
    "| ---: | --- | --- | --- | ---: | --- |"]
    for r in rows:
        rating=f'{r["show_rating_us"]}/5 ({r["show_rating_count_us"]} ratings)' if r["show_rating_us"] else "Not verified"
        title=r["episode"].replace("|","–")
        name=r["show"].replace("|","–")
        note=r["inspiration"].replace("|","–")
        link=r["episode_url"]
        if link.rstrip("/") in ("https://thelorehounds.com","https://www.theswu.com","https://starwarsunderworld.net"):
            link=r["publisher_audio_url"]
        lines.append(f'| {r["order"]} | {r["kind"]} | [{title}]({link}) — {name} | {rating} | {r["editorial_score"]:.1f} | {note} |')
    lines+=["","## How the ranking works","",
    "52% topical relevance (species, regions, technology, history, Force traditions), 22% NPC and performed-story usefulness, 16% Bayesian-smoothed show-wide US Apple rating, 10% diversity, followed by pairing and repetitive-topic penalties.",
    "Story excerpts are whole original episodes, not redistributed or clipped. No published audio content is copied. Source podcast quality signals are not individual episode reviews.",
    "Continuity rule: each story arc starts at chapter one and advances without skipping; a missing or invalid chapter truncates the arc. No non-Star-Wars material is imported.",
    ""]
    return "\n".join(lines)

def checked_write(filename,data):
    tmp=HERE/(filename+".tmp")
    tmp.write_bytes(data)
    tmp.replace(HERE/filename)

def main():
    report={"generated_utc":datetime.now(timezone.utc).isoformat(),"state":"building","lore_sources":[],
            "story_arcs":[],"outputs":{},"copyrighted_audio_rehosted":False,"warnings":[]}
    all_lore=[]
    for source in CFG["lore_sources"]:
        try:
            found=pick_lore(source)
            if not found:raise ValueError("No matching verified lore audio")
            all_lore+=found
            report["lore_sources"].append({"id":source["id"],"status":"included","episodes":len(found)})
        except Exception as error:
            report["lore_sources"].append({"id":source["id"],"status":"unavailable","reason":str(error)[:400]})
            report["warnings"].append("Unavailable lore: "+source["id"])
    all_arcs=[]
    for arc in CFG["story_arcs"]:
        try:
            chapters=pick_story(arc)
            if not chapters:raise ValueError("No verified consecutive story chapters beginning with episode 1")
            item=dict(arc);item["entries"]=chapters;all_arcs.append(item)
            report["story_arcs"].append({"id":arc["id"],"status":"included","episodes":len(chapters)})
        except Exception as error:
            report["story_arcs"].append({"id":arc["id"],"status":"unavailable","reason":str(error)[:300]})
            report["warnings"].append("Unavailable story: "+arc["id"])
    if len([s for s in report["lore_sources"] if s["status"]=="included"])<2:
        raise RuntimeError("Need at least two verified independent lore sources")
    if len(all_arcs)<3:
        raise RuntimeError("Need at least three verified continuous story arcs")
    result=rank(all_lore,all_arcs)
    # Cross-feed duplicates never allowed.
    enclosure_urls=[e["item"].find("enclosure").get("url") for e in result]
    if len(set(enclosure_urls))!=len(enclosure_urls):raise RuntimeError("Duplicate original audio enclosures")
    if any((e["role"]!=("LORE" if i%2==0 else "STORY")) for i,e in enumerate(result)):
        raise RuntimeError("Alternation failed")
    rows=episode_metadata(result)
    outputs={
      "learning-base-v2.xml":serialize(result,"learning-base-v2.xml","Star Wars RPG — Ranked Lore + Story (Base Sequence)"),
      "learning-lore.xml":serialize(result[::2],"learning-lore.xml","Star Wars RPG — Curated Lore Only"),
      "learning-story.xml":serialize(result[1::2],"learning-story.xml","Star Wars RPG — Continuous Actual-Play Story"),
      "learning-base-episodes.md":episode_markdown(rows).encode("utf-8"),
      "learning-base-episodes.json":(json.dumps({"generated_utc":report["generated_utc"],
          "rating_basis":"US Apple show-level only; editorial scores are not episode ratings",
          "episodes":rows},indent=2,ensure_ascii=False)+"\n").encode("utf-8")}
    for name,data in outputs.items():checked_write(name,data)
    report["outputs"]={"learning-base-v2.xml":len(result),"learning-lore.xml":len(result)//2,
                        "learning-story.xml":len(result)//2,"learning-base-episodes.md":len(rows)}
    report["state"]="published"
    report["episodes"]=len(result)
    report["pairs"]=len(result)//2
    checked_write("learning-base-status.json",(json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode("utf-8"))
    print("Generated verified independent lore/story base; final subscription assembled by generate_frontier_mix.py",report["outputs"])

if __name__=="__main__":
    try:main()
    except Exception as err:
        print("Learning feed failed, prior published feeds preserved:",err,file=sys.stderr)
        raise
