#!/usr/bin/env python3
"""Verify public V3 RSS delivery; do NOT invoke the rate-limited jsDelivr purge.

The new @main V3 subscription must match the just-published GitHub bytes.
A revision-pinned CDN URL is separately checked for access to immutable bytes.
This script never asserts that a specific Podbean installation imported it.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CANONICAL="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/feed-v3.xml"
REV="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@{commit}/anomaly/feed-v3.xml"
EXPECTED=(BASE/"feed-v3.xml").read_bytes()
def digest(b):
    return hashlib.sha256(b).hexdigest()
def read(url):
    req=Request(url,headers={"User-Agent":"AnomalyV3PublicationVerifier/1.0",
                             "Accept":"application/xml,application/rss+xml,*/*"})
    with urlopen(req,timeout=25) as response:
        return response.read(4_000_000),{
            "http_status":response.status,
            "content_type":response.headers.get("Content-Type"),
            "age_seconds":response.headers.get("Age"),
            "cache_control":response.headers.get("Cache-Control")
        }

def validate(data):
    rss=ET.fromstring(data)
    assert rss.tag=="rss" and rss.get("version")=="2.0"
    channel=rss.find("channel")
    assert channel is not None
    entries=channel.findall("item")
    ids=[x.findtext("guid") for x in entries]
    media=[x.find("enclosure") for x in entries]
    assert len(entries)==len(set(ids))==120
    assert all(g.startswith("urn:uuid:") for g in ids)
    assert len({e.get("url") for e in media})==120
    assert all(e.get("url","").startswith("https://")
               and int(e.get("length","0"))>0 for e in media)
    assert channel.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit")=="true"
    assert channel.find("{http://www.w3.org/2005/Atom}link").get("href")==CANONICAL
    return {
      "title":channel.findtext("title"),"count":120,
      "unique_guids":len(set(ids)),"enclosures":len(media),
      "last_build":channel.findtext("lastBuildDate")
    }

def main():
    pub=validate(EXPECTED)
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=BASE.parent,text=True).strip()
    urls={"canonical":CANONICAL,"immutable":REV.format(commit=sha)}
    result={
      "verified_at_utc":datetime.now(timezone.utc).isoformat(),
      "expected_source_sha256":digest(EXPECTED),
      "github_commit":sha,
      "state":"checking",
      "rss":pub,
      "podbean_import_tested":False,
      "methods":{}
    }
    for name,url in urls.items():
        item={"url":url,"matches":False}
        try:
            raw,headers=read(url)
            item.update(headers)
            item["received_sha256"]=digest(raw)
            item["matches"]=raw==EXPECTED
            if item["matches"]:
                item["rss"]=validate(raw)
        except Exception as e:
            item["error"]=type(e).__name__+": "+str(e)[:240]
        result["methods"][name]=item
    canonical=result["methods"]["canonical"]["matches"]
    immutable=result["methods"]["immutable"]["matches"]
    result["state"]=("canonical_live_verified" if canonical and immutable else
                     "immutable_verified_canonical_stale" if immutable else
                     "cdn_unverified")
    (HERE/"cdn-health.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False),flush=True)
    return 0 if canonical and immutable else 1

if __name__=="__main__":
    raise SystemExit(main())
