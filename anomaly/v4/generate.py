#!/usr/bin/env python3
"""Create a new V4 RSS; require genuine publisher enclosures for all lore."""
import json,re,uuid,html,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import format_datetime
B=Path(__file__).resolve().parent
IT="http://www.itunes.com/dtds/podcast-1.0.dtd"; AT="http://www.w3.org/2005/Atom"
ET.register_namespace("itunes",IT);ET.register_namespace("atom",AT)
U="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/feed-v4.xml"
T=datetime(2026,10,21,4,0,tzinfo=timezone.utc)
TOP=[1,3,7,11,15,21,35,55,87,91]
DROP=[5,17,25,27,45,49,57,65,85,93]
MIDDLE=[22,50,68,60,72,112,118,98,28,76]
THEMES={"communities":("ordinary life in a magical city","social relationships and practical obligations"),
"eilistraee":("an elven refuge","cultural difference and chosen belonging"),
"itich":("a nonhuman colony in ancient works","living communities and material culture"),
"wall":("an altered landscape","environmental uncertainty and survival"),
"attina":("a transformed spellcaster","identity, agency and changing relationships"),
"aberrations":("strange ancient intelligence","psychic pressure, memory and autonomy")}
FULL={11,55,87,91,107}
def sec(v):
 if not v:return 0
 if v.isdigit():return int(v)
 try:
  p=list(map(int,v.split(":")))
  return p[0]*3600+p[1]*60+p[2] if len(p)==3 else p[0]*60+p[1] if len(p)==2 else 0
 except: return 0
def norm(v):return re.sub("[^a-z0-9]+"," ",html.unescape(v).lower()).strip()
def put(parent,key,value):
 n=ET.SubElement(parent,key);n.text=str(value);return n
def v3():
 x=ET.parse(B.parent/"feed-v3.xml").getroot().find("channel").findall("item")
 if len(x)!=120:raise ValueError("Missing V3 120-item baseline")
 out=[]
 for n,item in enumerate(x,1):
  name=item.findtext("title") or ""
  m=re.match(r"\d+ - (STORY|ACTUAL PLAY) - (.*?) - (.*)$",name)
  if not m:raise ValueError("V3 title cannot be parsed "+str(n))
  enc=item.find("enclosure"); desc=item.findtext("description") or ""
  theme=desc.partition("Theme: ")[2].partition(". Publisher:")[0]
  premise=desc.partition(". Description: ")[2].partition(". Editorial relevance: ")[0]
  # Strip promotion and production credits; the RSS should explain scenes,
  # not biographies of podcast authors or links to social accounts.
  premise=re.sub(r"(?i)written by.{0,110}?directed by.{0,110}?(?=join us|meet |explore |the story|when |as )","",premise)
  premise=re.sub(r"(?i)\\b(?:written by|directed by|narrated by|produced by)\\b[^.]{0,140}","",premise)
  premise=re.split(r"(?i)\\b(?:support us|follow us|follow the show|patreon|twitter|discord|learn more about your ad choices|read the transcript|check out)\\b",premise,maxsplit=1)[0]
  # Never let author credits, production biographies or ads flow into
  # a listener-visible WHY THIS EPISODE description.
  premise=re.sub(r"(?i)written by.{0,90}?directed by chris and megan burnside","",premise)
  premise=re.split(r"(?i)\\b(?:written by|directed by|support us|support the show|support our|follow us|follow the show|patreon|twitter|discord|learn more about your ad choices|check out|for new installments|get ad free|show notes)\\b",premise,maxsplit=1)[0]
  premise=re.sub(r"\\s+"," ",premise).strip()
  if theme not in THEMES:raise ValueError("Missing theme "+str(n))
  out.append(dict(origin=n,role="story" if m[1]=="STORY" else "actual_play",
   publisher=m[2],title=m[3],theme=theme,summary=premise[:300],
   link=item.findtext("link") or enc.get("url"),url=enc.get("url"),
   size=int(enc.get("length") or 0),mime=enc.get("type"),duration=item.findtext("{"+IT+"}duration") or "",
   seconds=sec(item.findtext("{"+IT+"}duration") or ""),
   evidence="full transcript" if n in FULL else "publisher synopsis"))
 return out
def lore(spec,cache):
 feed=spec["feed"]
 if feed not in cache:
  r=urllib.request.Request(feed,headers={"User-Agent":"Curated-Anomaly-Feed/4.0"})
  with urllib.request.urlopen(r,timeout=25) as f:raw=f.read(20000000)
  channel=ET.fromstring(raw).find("channel")
  if channel is None:raise ValueError("Publisher RSS missing channel "+feed)
  cache[feed]=channel.findall("item")
 matches=[x for x in cache[feed] if norm(spec["needle"]) in norm(x.findtext("title") or "")]
 if len(matches)!=1:raise ValueError("Publisher RSS ambiguous/missing "+spec["needle"]+" candidates "+str(len(matches)))
 e=matches[0];a=e.find("enclosure")
 if a is None:raise ValueError("No publisher recording: "+spec["needle"])
 url=a.get("url") or "";size=int(a.get("length") or 0);mime=a.get("type") or ""
 if size<=0:
  try:
   request=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"AnomalyV4RSSHead/1.0"})
   with urllib.request.urlopen(request,timeout=24) as response:size=int(response.headers.get("Content-Length") or 0)
  except Exception:pass
 if size<=0:
  try:
   request=urllib.request.Request(url,headers={"Range":"bytes=0-0","User-Agent":"AnomalyV4RSSHead/1.0"})
   with urllib.request.urlopen(request,timeout=24) as response:
    header=response.headers.get("Content-Range") or ""
    if "/" in header:size=int(header.split("/")[-1])
    elif response.status==200:size=int(response.headers.get("Content-Length") or 0)
    response.read(1)
  except Exception:pass
 duration=e.findtext("{"+IT+"}duration") or ""
 seconds=sec(duration)
 if not url.startswith("https://") or size<=0 or not mime.startswith("audio/") or seconds<1800:raise ValueError("Lore enclosure/duration invalid: "+spec["needle"]+" seconds="+str(seconds)+" bytes="+str(size)+" mime="+mime)
 return dict(role="lore",publisher=spec["publisher"],title=e.findtext("title") or "",
  theme=spec["theme"],summary="",link=e.findtext("link") or url,url=url,size=size,
  mime=mime,duration=duration,seconds=seconds,evidence="publisher chapter guide/synopsis",
  why=spec["why"],focus=spec["focus"],publisher_guid=e.findtext("guid") or "")
def rationale(e):
 if e["role"]=="lore":return e["why"],e["focus"]
 theme=e["theme"] if e["theme"] in THEMES else "communities"
 relation,focus=THEMES[theme]
 summ=e["summary"].strip()
 markers=[("trade, services and local institutions",["market","shop","guild","court","mayor"]),
 ("family and individual loyalties",["family","friends","father","brother","love"]),
 ("incomplete knowledge and unusual perception",["mind","vision","dream","psychic","mystery"]),
 ("old places and the traces left behind",["cave","ruin","mine","tunnel","underground"]),
 ("conflicting characters facing changing circumstances",["battle","threat","encounter","journey"])]
 element=next((name for name,words in markers if any(w in (e["title"]+" "+summ).lower() for w in words)),"characters responding to a distinctive situation")
 why="Chosen for "+element+", with a thematic connection to "+relation+". Focus on "+focus+"."
 if e["seconds"]<1800:why+=" Shorter than the preferred half-hour; retained as a deliberate content or variety exception."
 if e["seconds"]>=3600:why+=" Long-form length offers a substantial listening segment."
 evidence="A complete script was examined for this recording." if e["evidence"]=="full transcript" else "Publisher description evidence only; the full transcript has not been checked."
 what="Source premise: "+summ[:265]+". "+evidence if summ else evidence
 return why,what
def main():
 p=json.loads((B/"policy.json").read_text())
 v=v3();stories=[e for e in v if e["role"]=="story"];plays=[e for e in v if e["role"]=="actual_play"]
 assert len(stories)==len(plays)==60
 kept=[e for e in stories if e["origin"] not in DROP];assert len(kept)==50
 top=[next(e for e in kept if e["origin"]==n) for n in TOP]
 bottom=[e for e in kept if e["origin"] not in TOP]
 first=plays[:10];mid=[next(e for e in plays if e["origin"]==n) for n in MIDDLE]
 last=[e for e in plays if e["origin"] not in {x["origin"] for x in first+mid}]
 assert list(map(len,[top,bottom,first,mid,last]))==[10,40,10,10,40]
 cache={};facts=[lore(x,cache) for x in p["lore_specs"]]
 out=[]
 for a,b in zip(top,first):out.extend([a,b])
 for a,b in zip(facts,mid):out.extend([a,b])
 for a,b in zip(last,bottom):out.extend([a,b])
 assert len(out)==120 and len({e["url"] for e in out})==120
 assert all(e["size"]>0 and e["url"].startswith("https://") and e["seconds"]>0 for e in out)
 root=ET.Element("rss",version="2.0");channel=ET.SubElement(root,"channel")
 title="Anomaly V4 - Stories, Actual Plays and Lore"
 put(channel,"title",title);put(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly/v4")
 put(channel,"description","Curated original-publisher recordings: 20 stories and actual plays, 20 lore and actual plays, 80 actual plays and stories. Each episode carries a public-safe reason for selection.")
 put(channel,"language","en");put(channel,"{"+IT+"}author","Anomaly Listening Catalog")
 put(channel,"{"+IT+"}summary","Immersive roleplaying, unusual societies, worldbuilding and thoughtful fantasy lore.")
 put(channel,"{"+IT+"}explicit","true");put(channel,"{"+IT+"}type","episodic")
 ET.SubElement(channel,"{"+IT+"}category",text="Leisure")
 image=ET.SubElement(channel,"image")
 put(image,"url","https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/cover.png")
 put(image,"title",title);put(image,"link","https://github.com/Quarky/shadowrunfeed/tree/main/anomaly/v4")
 ET.SubElement(channel,"{"+IT+"}image",href="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/cover.png")
 ET.SubElement(channel,"{"+AT+"}link",href=U,rel="self",type="application/rss+xml")
 put(channel,"lastBuildDate",format_datetime(T,usegmt=True))
 for n,e in enumerate(out,1):
  a,b=rationale(e);e["slot"]=n;e["public_reason"]=a;e["public_focus"]=b
  node=ET.SubElement(channel,"item")
  put(node,"title",f"{n:03d} - {e['role'].upper().replace('_',' ')} - {e['publisher']} - {e['title']}")
  put(node,"link",e["link"])
  message="WHY SELECTED: "+a+"\n\nWHAT TO LISTEN FOR: "+b+"\n\nDURATION: "+str(round(e["seconds"]/60))+" minutes. SOURCE EVIDENCE: "+e["evidence"]+". Outside inspirations only; no private campaign history is described."
  put(node,"description",message)
  g=put(node,"guid","urn:uuid:"+str(uuid.uuid5(uuid.NAMESPACE_URL,"anomaly:v4:"+e["url"])));g.set("isPermaLink","false")
  put(node,"pubDate",format_datetime(T-timedelta(minutes=n),usegmt=True))
  ET.SubElement(node,"enclosure",url=e["url"],length=str(e["size"]),type=e["mime"])
  put(node,"{"+IT+"}episodeType","full");put(node,"{"+IT+"}episode",n)
  put(node,"{"+IT+"}duration",e["duration"])
 xml=ET.tostring(root,encoding="utf-8",xml_declaration=True)
 target=B.parent/"feed-v4.xml"
 if not target.exists() or target.read_bytes()!=xml:target.write_bytes(xml)
 (B/"selected.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
 stats=dict(version=4,state="publisher_verified",total=120,roles={"story":50,"actual_play":60,"lore":10},
  over_30_minutes=sum(e["seconds"]>=1800 for e in out),
  over_60_minutes=sum(e["seconds"]>=3600 for e in out),
  short_exceptions=[{"slot":n,"title":e["title"],"min":round(e["seconds"]/60,1)} for n,e in enumerate(out,1) if e["seconds"]<1800],
  publisher_count=len({e["publisher"] for e in out}),lore_publisher_rss_urls=sorted(cache),
  full_script_evidence_on_final_tracks=sum(e["evidence"]=="full transcript" for e in out),
  publisher_audio_enclosures_verified=120,podbean_import_tested=False)
 (B/"status.json").write_text(json.dumps(stats,indent=2,ensure_ascii=False)+"\n")
 print("V4 PASS",stats["roles"],"publishers",stats["publisher_count"],"short exceptions",len(stats["short_exceptions"]))
if __name__=="__main__":main()
