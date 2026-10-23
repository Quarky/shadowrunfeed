#!/usr/bin/env python3
"""Compare committed Shadowrun RSS bytes against actual public CDN/raw endpoints."""
import datetime as dt
import hashlib
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

B=Path(__file__).resolve().parent
p=json.loads((B/"policy.json").read_text())
feed=(B/"feed-v1.xml").read_bytes()
want=hashlib.sha256(feed).hexdigest()
urls={
    "cdn_main":p["subscription"],
    "github_raw":"https://raw.githubusercontent.com/Quarky/shadowrunfeed/main/shadowrun/anthology/feed-v1.xml",
}
sha=os.environ.get("PUBLISHED_COMMIT") or ""
if len(sha)==40:
    urls["immutable_cdn"]="https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@"+sha+"/shadowrun/anthology/feed-v1.xml"
result={
    "checked_at":dt.datetime.now(dt.timezone.utc).isoformat(),
    "expected_sha256":want,
    "published_commit":sha,
    "feed_url":p["subscription"],
    "endpoints":{},
    "podbean_import_tested":False,
    "source_audio_full_playback_tested":False,
}
with Image.open(B/"cover.png") as cover:
    result["cover"]={"width":cover.width,"height":cover.height,"mode":cover.mode}
root=ET.fromstring(feed)
result["items"]=len(root.find("channel").findall("item"))
for key,url in urls.items():
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ShadowrunFeedDeliveryCheck/1.0","Cache-Control":"no-cache"})
        with urllib.request.urlopen(req,timeout=35) as response:
            actual=response.read(4_000_000)
            status=response.status
            content_type=response.headers.get("Content-Type","")
        actual_hash=hashlib.sha256(actual).hexdigest()
        result["endpoints"][key]={
            "http_status":status,"bytes":len(actual),"content_type":content_type,
            "sha256":actual_hash,"identical_to_committed":actual_hash==want
        }
    except Exception as exc:
        result["endpoints"][key]={"error":str(exc)[:250],"identical_to_committed":False}
result["state"]="verified" if (
    result["items"]==int(p.get("published_count",p["count"])) and result["cover"]["width"]>=1400 and result["cover"]["height"]>=1400
    and result["endpoints"].get("cdn_main",{}).get("identical_to_committed")
    and result["endpoints"].get("github_raw",{}).get("identical_to_committed")
) else "blocked_or_stale"
(B/"delivery-status.json").write_text(json.dumps(result,indent=2)+"\n")
print("DELIVERY:",result["state"],{k:v.get("identical_to_committed") for k,v in result["endpoints"].items()})
