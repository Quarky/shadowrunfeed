#!/usr/bin/env python3
"""Validate live Podbean subscription bytes on jsDelivr after RSS publication.

Expected: python3 anomaly/verify_published_rss.py
Checks exact remote-vs-local RSS bytes and the podcast-specific XML contract.
Attempts one jsDelivr branch-cache purge. Always writes cdn-health.json with
independent evidence; exits nonzero if the live subscription URL is stale.
This program cannot change a Podbean user's existing subscribed feed URL.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
ROOT = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/"
PURGE = "https://purge.jsdelivr.net/gh/Quarky/shadowrunfeed@main/"
ATOM = "{http://www.w3.org/2005/Atom}"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CHECK = [
    "anomaly/feed-v2.xml",
    "anomaly/feed.xml",
    "anomaly/optional-listening/feed-v2.xml",
    "anomaly/cover.png",
]

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def get(url: str, timeout: int = 18) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={
        "User-Agent": "AnomalyPodcastRSSHealth/1.0 (rss validation)",
        "Accept": "application/rss+xml, application/xml, image/png, */*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(8_000_000), {
            "http_status": response.status,
            "content_type": response.headers.get("Content-Type", ""),
            "age": response.headers.get("Age", ""),
            "cache_control": response.headers.get("Cache-Control", ""),
            "etag": response.headers.get("ETag", ""),
        }

def rss_check(document: bytes, expected_count: int, expected_url: str) -> dict:
    root = ET.fromstring(document)
    assert root.tag == "rss" and root.get("version") == "2.0"
    channel = root.find("channel")
    assert channel is not None
    title = channel.findtext("title") or ""
    assert title.startswith("Anomaly"), title
    assert channel.findtext("lastBuildDate") or expected_count == 9
    atom = channel.find(ATOM + "link")
    assert atom is not None and atom.get("href") == expected_url, (
        "atom:link not pointing at subscribed address", expected_url,
    )
    assert channel.find(ITUNES + "image") is not None
    entries = channel.findall("item")
    assert len(entries) == expected_count, len(entries)
    ids = [item.findtext("guid") for item in entries]
    assert len(set(ids)) == len(ids) and all(ids), "Missing/duplicate GUIDs"
    enc = [item.find("enclosure") for item in entries]
    assert all(e is not None and (e.get("url") or "").startswith("https://")
               and int(e.get("length") or "0") > 0
               and (e.get("type") or "").startswith("audio/") for e in enc), (
        "An enclosure lacks audio URL, MIME type or byte size"
    )
    assert all(item.findtext("title") and item.findtext("pubDate") for item in entries)
    return {"title": title, "episodes": len(entries),
            "lastBuildDate": channel.findtext("lastBuildDate"),
            "unique_guids": len(set(ids)), "playable_enclosures": len(enc)}

def main() -> int:
    report = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "canonical_feed_url": ROOT + "anomaly/feed-v2.xml",
        "state": "unverified",
        "podbean_access": "External RSS compatibility checked; user account cannot be inspected",
        "paths": {},
        "purge": {},
    }
    try:
        expected = {p: (BASE.parent / p).read_bytes() for p in CHECK}
        rss_check(expected[CHECK[0]], 120, ROOT + CHECK[0])
        rss_check(expected[CHECK[2]], 9, ROOT + CHECK[2])
        assert expected[CHECK[0]] == expected[CHECK[1]], (
            "The canonical and alternate feed paths differ"
        )
        assert expected[CHECK[3]].startswith(b"\\x89PNG\\r\\n\\x1a\\n")
        # The main feed is a discovery set. Already-listened shows are a
        # separate optional replay shelf; do not silently leak them back.
        main_entries = ET.fromstring(expected[CHECK[0]]).findall("./channel/item")
        assert all("Worlds Beyond Number" not in (x.findtext("title") or "")
                   and "Dungeons of Drakkenheim" not in (x.findtext("title") or "")
                   for x in main_entries)

        for p in CHECK:
            try:
                resp, headers = get(PURGE + p, timeout=14)
                report["purge"][p] = {"accepted": True,
                                      "http_status": headers["http_status"],
                                      "response": resp[:220].decode("utf-8", "replace")}
            except Exception as e:
                report["purge"][p] = {"accepted": False,
                                      "error": type(e).__name__ + ": " + str(e)[:180]}

        for p in CHECK:
            info = {"expected_sha256": sha(expected[p]), "matches": False}
            for attempt in range(1, 8):
                try:
                    observed, headers = get(ROOT + p)
                    info.update(headers)
                    info["actual_sha256"] = sha(observed)
                    info["bytes"] = len(observed)
                    info["attempts"] = attempt
                    info["matches"] = observed == expected[p]
                    if info["matches"]:
                        if p.endswith(".xml"):
                            info["rss_check"] = rss_check(
                                observed, 9 if "optional-listening" in p else 120,
                                ROOT + p if p.endswith("feed-v2.xml") else ROOT + "anomaly/feed-v2.xml",
                            )
                        break
                except Exception as e:
                    info["error"] = type(e).__name__ + ": " + str(e)[:240]
                    info["attempts"] = attempt
                if attempt < 7:
                    time.sleep(10)
            report["paths"][p] = info
        report["state"] = ("verified" if all(x["matches"] for x in
                                             report["paths"].values())
                           else "cdn_stale_or_inaccessible")
    except Exception as e:
        report["state"] = "validation_error"
        report["error"] = type(e).__name__ + ": " + str(e)[:500]

    (BASE / "cdn-health.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    return 0 if report["state"] == "verified" else 1

if __name__ == "__main__":
    sys.exit(main())
