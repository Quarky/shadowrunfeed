#!/usr/bin/env python3
"""Inspect original publisher RSS candidates for Anomaly playlist improvements.

Read only: produces an evidence catalog, not a new published feed.
Usage: python3 -u anomaly/replacement_candidates.py
Failure modes: network unavailable (printed per source), no usable candidates
(fails nonzero). Does not download media or change the live podcast playlist.
"""
import concurrent.futures as cf
import json
from pathlib import Path
import runpy
from collections import Counter
import re

ROOT=Path(__file__).resolve().parent
ENG=runpy.run_path(str(ROOT.parent/"magudonya"/"generate_feed.py"),run_name="candidate_library")
CAT=json.loads((ROOT/"catalog.json").read_text())
ENG["THEME_TERMS"]["communities"]=ENG["THEME_TERMS"]["reach"]
RSS={
 "once-future-nerd":"https://onceandfuturenerd.com/feed/podcast",
 "silt-verses":"https://access.acast.com/rss/5fec690f8211cf453a1b89e2/",
 "inn-between":"https://innbetween.libsyn.com/rss",
 "alba-salix":"https://rss.art19.com/alba-salix--royal-physician",
 "counterbalance":"https://feeds.acast.com/public/shows/6ab68b65fb182c6fb5dc9171",
 "call-flame":"https://daisy-tangerine.squarespace.com/news?format=rss",
 "penumbra":"https://feeds.acast.com/public/shows/6831c608381499796b234652",
 "old-gods":"https://feeds.acast.com/public/shows/61ba0a431a8cbeb6ea3cf11a",
 "heart-pyre":"https://rss.buzzsprout.com/1896897.rss",
 "hidden-people":"https://feeds.megaphone.fm/SBP9476192479",
 "ordinary-epic":"https://feeds.megaphone.fm/theordinaryepic",
 "carcerem":"https://feeds.megaphone.fm/carceremtheseries",
 "worlds-beyond-number":"https://feeds.simplecast.com/IAPnSSRO",
 "drow-dracoliches":"https://actualplay.roleplayingpublicradio.com/tag/drow-and-dracoliches/feed/",
 "drakkenheim":"https://rss.libsyn.com/shows/201575/destinations/1438583.xml",
 "naddpod":"https://rss.art19.com/not-another-d-and-d-podcast",
 "lucky-die":"https://feeds.acast.com/public/shows/6ab67e2362a47b6bec0eba41",
 "dice-shame":"https://feeds.acast.com/public/shows/62691c6f17b69400149656fa",
 "venture-forth":"https://rss.buzzsprout.com/1694983.rss",
 "adventure-zone":"https://feeds.simplecast.com/cYQVc__c",
 "critical-role":"https://feeds.simplecast.com/LXz4Q9rJ",
 "dungeons-daddies":"https://feeds.acast.com/public/shows/46e42ca7-4921-5f04-a297-1970e72fd86d",
 "tabletop-gold":"https://feeds.libsyn.com/355706/rss",
 "encounter-party":"https://feeds.redcircle.com/925fac0e-79f3-49a1-b016-20c8de5ebaa0",
 "rppr":"https://actualplay.roleplayingpublicradio.com/feed/",
 "tale-of-manticore":"https://www.spreaker.com/show/6276878/episodes/feed",
 "join-party":"https://rss.introcast.io/1238902672/rss.art19.com/join-the-party",
 "high-rollers":"https://feeds.megaphone.fm/NSR8625352094",
 "girls-dnd":"https://feeds.megaphone.fm/GWD8899491190",
 "dark-dice":"https://feeds.megaphone.fm/SBP9028289759",
 "broadswords":"https://feeds.megaphone.fm/broadswords",
 "stinky-dragon":"https://feeds.megaphone.fm/stinkydragon",
 "adventures-erylia":"https://rss.buzzsprout.com/2611503.rss"
}
# Full episodes only; remove promotional/metadata-only/genre-mismatched items.
BAD=re.compile(r"\b(trailer|teaser|bonus|introduc(?:ing|tion)|promo|advert|recap|behind the scenes|bloop|table talk|meet the |start here|listening order|session zero|campaign announcement|welcome to worlds beyond number|prelude guide|feed drop|outtakes|episode 0\\b|episode zero|patreon|character creation)\b",re.I)
SCI=re.compile(r"(?:Doctor Who|Dark Journey|Mutants in the Now|Delta Green|Cyberpunk|Star Wars|Traveller|The Expanse)",re.I)
NEED=set(k for t in json.loads((ROOT/"selection-lock.json").read_text()).values() for l in t.values() for k in l)
def load(s):
 try:
  import xml.etree.ElementTree as ET
  data=ENG["get"](RSS[s["id"]],timeout=22)
  tree=ET.fromstring(data)
  ch=tree.find("channel") if tree.tag!="channel" else tree
  episodes=ENG["entries_from"](s,ch) if ch is not None else []
  return s,episodes,""
 except Exception as exc: return s,[],type(exc).__name__+": "+str(exc)[:140]

def main():
 sources=[s for s in CAT["sources"] if s["id"] in RSS and s["id"] not in ("rppr",)]
 with cf.ThreadPoolExecutor(max_workers=12) as pool: data=list(pool.map(load,sources))
 output={"available_sources":{},"failed_sources":{},"per_theme":{}}
 for s,eps,error in data:
  if error: output["failed_sources"][s["id"]]=error
  else: output["available_sources"][s["id"]]=len(eps)
  print(s["id"],len(eps),error,flush=True)
 grouped={}
 for theme in CAT["themes"]:
  grouped[theme]={}
  for role in ("story","actual_play"):
   candidates=[]
   for s,episodes,error in data:
    if error or role!=s["role"] or theme not in s["themes"]:continue
    for ep in episodes:
     if ep["key"] in NEED:continue
     if BAD.search(ep["title"]) or SCI.search(ep["title"]):continue
     if ep["source"]=="tale-of-manticore" and re.search(r"\\b(Episode 0|Trailer|Intro)\\b",ep["title"],re.I):continue
     score=ENG["scored"](ep,theme)
     if len(ep["description"])<75:score-=10
     if len(ep["description"])<25:score-=30
     candidates.append({"source":s["id"],"publisher":s["name"],"title":ep["title"],"key":ep["key"],"original_date":ep["original"],"role":role,"score":score,"blurb":ep["description"][:510],"publisher_link":ep["link"],"url":ep["url"],"theme":theme})
   candidates.sort(key=lambda e:(e["score"],e["original_date"]),reverse=True)
   # Take best for each source, plus first chronological genuine episode.
   reduced=[];per_source=Counter()
   for c in candidates:
    if per_source[c["source"]]>=5:continue
    reduced.append(c);per_source[c["source"]]+=1
   # include only top 100 so reviewed payload remains modest
   grouped[theme][role]=reduced[:85]
 output["per_theme"]=grouped
 (ROOT/"replacement-candidates.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\\n")
 print("Candidate counts",json.dumps({t:{r:len(v) for r,v in roles.items()} for t,roles in grouped.items()}),flush=True)
 if not any(grouped[t]["story"] and grouped[t]["actual_play"] for t in grouped):
  raise RuntimeError("No usable authenticated podcast episodes discovered")

if __name__=="__main__":main()
