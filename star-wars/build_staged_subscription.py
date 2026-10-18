#!/usr/bin/env python3
"""Create isolated deduplicated RSS. Never write subscribed feeds."""
from datetime import datetime,timedelta,timezone
from email.utils import parsedate_to_datetime,format_datetime
import copy,json,xml.etree.ElementTree as ET
from publish_original_subscription import HERE,URLBASE,ATOM,audio_identity,item_audio,atomic,read_feed

def build():
    root,ch,original=read_feed(HERE/"feed-v2.xml")
    _,_,source=read_feed(HERE/"feed-130-debug.xml")
    assert len(original)==100 and len(source)==130
    used={audio_identity(item_audio(x)) for x in original}
    assert len(used)==100
    fresh=[]
    for item in source:
        key=audio_identity(item_audio(item))
        if key not in used:
            used.add(key)
            fresh.append(copy.deepcopy(item))
    assert len(fresh)==40 and len(used)==140,(len(fresh),len(used))
    last=parsedate_to_datetime(original[-1].findtext("pubDate"))
    for n,item in enumerate(fresh,1):
        pub=item.find("pubDate")
        if pub is None:pub=ET.SubElement(item,"pubDate")
        earlier=pub.text or ""
        pub.text=format_datetime(last-timedelta(minutes=n))
        desc=item.find("description")
        if desc is not None:desc.text=(desc.text or "")+" Source release date: "+earlier+"."
        ch.append(item)
    assert len(ch.findall("item"))==140
    assert all(ET.tostring(x)==ET.tostring(y) for x,y in zip(original,ch.findall("item")[:100]))
    ch.find("title").text="TEST COPY — Star Wars 140 unique recordings"
    desc=ch.find("description")
    if desc is not None:desc.text="STAGING ONLY. Original 100 publisher recordings plus 40 new unique recordings. "+(desc.text or "")
    atom=ch.find(f"{{{ATOM}}}link")
    if atom is None:atom=ET.SubElement(ch,f"{{{ATOM}}}link")
    atom.set("href",URLBASE+"feed-140-candidate.xml")
    atom.set("rel","self")
    atom.set("type","application/rss+xml")
    ET.indent(root,space="  ")
    payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    ET.fromstring(payload)
    status={"state":"staging","episode_count":140,"preserved_original_guids":100,"original_subscriber_episodes":100,"new_unique_audio":40,"debug_source_episodes":130,"deduplicated_source_audio":90,"release_approved":False,"generated_at":datetime.now(timezone.utc).isoformat(),"candidate_url":URLBASE+"feed-140-candidate.xml"}
    atomic(HERE/"feed-140-candidate.xml",payload)
    atomic(HERE/"candidate-status.json",(json.dumps(status,indent=2)+"\n").encode("utf-8"))
    print("STAGING PASS: original 100 protected, candidate 140",status)

if __name__=="__main__":
    build()
