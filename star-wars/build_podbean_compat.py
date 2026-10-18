#!/usr/bin/env python3
"""Produce minimal, Podbean-compatible RSS diagnostics WITHOUT altering subscribed feeds.

No audio is downloaded, rehosted, or altered. Original episode GUIDs preserved.
Different test URLs/channel titles avoid misleading an existing Podbean subscription.
"""
from __future__ import annotations
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import copy, json, re, html
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ITUNES="http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM="http://www.w3.org/2005/Atom"
ET.register_namespace("itunes",ITUNES)
ET.register_namespace("atom",ATOM)
BASE="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/"
ART=BASE+"cover.png"
def text(node,tag):
    return node.findtext(tag) or ""
def expiry(url):
    params=parse_qs(urlsplit(url).query)
    for key in ("Expires","expires","timetoken"):
        val=params.get(key,[""])[0].split("_")[0]
        if val.isdigit() and len(val) in (10,13):
            stamp=int(val)
            return stamp//1000 if len(val)==13 else stamp
    return None
def plain(s):
    s=html.unescape(re.sub(r"<[^>]*>"," ",s or ""))
    return re.sub(r"\s+"," ",s).strip()[:1500]
def new_feed(rows,filename,title):
    root=ET.Element("rss",{"version":"2.0"})
    channel=ET.SubElement(root,"channel")
    def val(parent,tag,v):
        o=ET.SubElement(parent,tag);o.text=str(v);return o
    val(channel,"title",title)
    val(channel,"link","https://github.com/Quarky/shadowrunfeed/tree/main/star-wars")
    val(channel,"description","Technical test copy of the Star Wars listening collection. Original publishers host all recordings; not a new podcast or audio mirror. Test this without removing the existing subscription.")
    val(channel,"language","en")
    val(channel,f"{{{ITUNES}}}author","Independent Quarky podcast curation")
    val(channel,f"{{{ITUNES}}}summary","RSS compatibility test; unchanged publisher recordings")
    val(channel,f"{{{ITUNES}}}explicit","yes")
    ET.SubElement(channel,f"{{{ITUNES}}}category",{"text":"Leisure"})
    ET.SubElement(channel,f"{{{ITUNES}}}image",{"href":ART})
    cover=ET.SubElement(channel,"image")
    val(cover,"title",title)
    val(cover,"link","https://github.com/Quarky/shadowrunfeed/tree/main/star-wars")
    val(cover,"url",ART)
    ET.SubElement(channel,f"{{{ATOM}}}link",{"href":BASE+filename,"rel":"self","type":"application/rss+xml"})
    for src in rows:
        item=ET.SubElement(channel,"item")
        val(item,"title",text(src,"title"))
        val(item,"description",plain(text(src,"description")))
        val(item,"pubDate",text(src,"pubDate"))
        uid=src.find("guid")
        if uid is None or not uid.text:raise ValueError("Missing original GUID")
        val(item,"guid",uid.text).set("isPermaLink","false")
        source_link=text(src,"link")
        if source_link.startswith("https://"):
            val(item,"link",source_link)
        enc=src.find("enclosure")
        if enc is None:raise ValueError("Missing original enclosure")
        url=enc.get("url","")
        if not url.startswith("https://"):raise ValueError("Not HTTPS")
        length=int(enc.get("length","0"))
        if length<=0:raise ValueError("Missing audio byte length")
        fmt=enc.get("type","")
        if fmt in ("audio/x-m4a","audio/m4a"):
            fmt="audio/mp4"
        if fmt not in ("audio/mpeg","audio/mp4","audio/aac"):
            raise ValueError("Unexpected audio MIME: "+fmt)
        ET.SubElement(item,"enclosure",{"url":url,"length":str(length),"type":fmt})
        dur=text(src,f"{{{ITUNES}}}duration")
        if dur:val(item,f"{{{ITUNES}}}duration",dur)
    ET.indent(root,space="  ")
    blob=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    check=ET.fromstring(blob).find("channel").findall("item")
    assert len(check)==len(rows)
    assert len({x.findtext("guid") for x in check})==len(rows)
    (HERE/filename).write_bytes(blob)
    print("WROTE",filename,len(rows),"episodes",len(blob),"bytes")
    return {"file":filename,"episodes":len(rows),"bytes":len(blob),"rss_url":BASE+filename}

def main():
    root=ET.parse(HERE/"feed-v2.xml").getroot()
    original=root.find("channel").findall("item")
    assert len(original)==100,"Only diagnose the protected 100-item original"
    ids=[x.findtext("guid") for x in original]
    assert len(set(ids))==100
    now=int(datetime.now(timezone.utc).timestamp())
    stable=[]
    expired=[]
    soon=[]
    m4a=[]
    for idx,item in enumerate(original,1):
        enc=item.find("enclosure")
        u=enc.get("url","")
        exp=expiry(u)
        if exp and exp<=now:
            expired.append(idx)
        if exp and now<exp<now+86400:
            soon.append(idx)
        if enc.get("type") in ("audio/x-m4a","audio/m4a"):m4a.append(idx)
        if not exp and enc.get("type")=="audio/mpeg" and u.lower().startswith("https://"):
            stable.append(item)
    if len(stable)<10:raise RuntimeError("Not enough ordinary nonexpiring MP3 enclosures for smoke test")
    tests=[]
    tests.append(new_feed(stable[:1],"podbean-smoke-1.xml","Star Wars RSS Test - 1 unsigned MP3"))
    tests.append(new_feed(stable[:10],"podbean-smoke-10.xml","Star Wars RSS Test - 10 unsigned MP3"))
    tests.append(new_feed(stable,"podbean-smoke-stable.xml","Star Wars RSS Test - all unsigned MP3"))
    tests.append(new_feed(original,"podbean-clean-100.xml","Star Wars RSS Test - cleaned original 100"))
    status={"state":"diagnostic_only","source":"feed-v2.xml","original_count":100,
        "stable_unsigned_mp3":len(stable),"expired_media_positions":expired,
        "expiring_within_24h":soon,"m4a_positions":m4a,
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "tests":tests,"existing_feed_modified":False,
        "podbean_import_verified":False,
        "meaning":"A successful GitHub build does NOT prove Podbean can import. Compare smoke 1, 10, stable, cleaned 100 within the Podbean listener app."}
    (HERE/"podbean-compat-status.json").write_text(json.dumps(status,indent=2)+"\n",encoding="utf-8")
    print("DIAG",json.dumps(status))

if __name__=="__main__":
    main()
