#!/usr/bin/env python3
"""Append two real publisher-hosted pre-Shutdown lore recordings to the existing V1 RSS.

Runs *after* the deterministic 120-track builder. It does not replace any of
the 120 existing items or recycle their GUIDs. Fails closed if the original
Neo-Anarchist RSS lacks the exact recordings or valid audio enclosures.
"""
from __future__ import annotations
import collections
import datetime as dt
import email.utils
import hashlib
import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import build as b

H = Path(__file__).resolve().parent
RSS = "https://neo-anarchist.libsyn.com/rss"
PUB = "Neo-Anarchist Podcast"
PINS = ((28, 2058), (29, 2059))
ST = dt.datetime(2026, 10, 23, 13, 0, tzinfo=dt.timezone.utc)
IT = b.IT

def make_additions():
    feed_file = H / "feed-v1.xml"
    original = json.loads((H / "selected.json").read_text(encoding="utf-8"))
    if len(original) != 120 or collections.Counter(x["role"] for x in original) != b.POLICY["roles"]:
        raise ValueError("Core anthology must be original 120 item, 50/60/10 set before append")
    rss = ET.parse(feed_file)
    channel = rss.getroot().find("channel")
    if channel is None or len(channel.findall("item")) != 120:
        raise ValueError("Builder must supply precisely 120 valid XML items")
    old_guids = [n.findtext("guid") for n in channel.findall("item")]
    old_urls = [n.find("enclosure").get("url") for n in channel.findall("item")]
    if len(set(old_guids)) != 120 or len(set(old_urls)) != 120:
        raise ValueError("Baseline media or GUID duplication")
    candidates = b.fetch(RSS)
    if not candidates:
        raise ValueError("Neo-Anarchist original publisher RSS not reachable or empty")
    selected = []
    for number, year in PINS:
        matched = [item for item in candidates if
                   re.match(r"^Episode\s+" + str(number) + r":\s*" + str(year) + r"\b",
                            b.clean(item.findtext("title") or "", 250), re.I)]
        if len(matched) != 1:
            raise ValueError(f"Expected exactly one original RSS Episode {number} for {year}, got {len(matched)}")
        rec = b.make_record(matched[0], PUB, RSS, "lore")
        if rec is None or rec["size"] <= 0 or rec["mime"].startswith("audio/") is False:
            raise ValueError(f"Episode {number} missing publisher RSS HTTPS positive-length audio enclosure")
        rec["addition_reason"] = (
            "2058 Renraku Arcology upgrade before the Shutdown, useful for prelude workplace and security changes"
            if number == 28 else
            "2059 corporate changes including Renraku troubles immediately before the Shutdown"
        )
        rec["short_duration_exception"] = bool(rec["seconds"] and rec["seconds"] < 1800)
        selected.append(rec)
    new_urls = [e["url"] for e in selected]
    if len(set(old_urls + new_urls)) != 122:
        raise ValueError("A pinned addition duplicated an existing publisher audio enclosure")
    all_source_guids = [e.get("publisher_guid") for e in original + selected if e.get("publisher_guid")]
    if len(set(all_source_guids)) != len(all_source_guids):
        raise ValueError("A pinned addition duplicated an original publisher episode GUID")

    audit = []
    for n, rec in enumerate(selected, 121):
        rec["slot"] = n
        rec["theme"] = "corporate_power"
        rec["evidence"] = "publisher_metadata_only"
        rec["why"] = (
            "Direct pre-Shutdown Shadowrun lore. " + rec["addition_reason"] + ". "
            "Added without removing any of the original 120 selections. "
            "Short episode exception: direct setting relevance outweighs the 30-minute duration preference."
        )
        rec["focus"] = "Publisher synopsis: " + rec["publisher_summary"]
        el = ET.SubElement(channel, "item")
        b.put(el, "title", f"{n:03d} - LORE - {PUB} - {rec['title']}")
        b.put(el, "link", rec["publisher_link"])
        b.put(el, "description", (
            "WHY SELECTED: " + rec["why"] +
            "\n\nWHAT TO LISTEN FOR: " + rec["focus"] +
            "\n\nEVIDENCE: Publisher RSS synopsis, GUID, episode identity and HTTPS audio enclosure verified. "
            "The full transcript has NOT been examined. This is GM reference material, not session canon."
        ))
        guid = b.put(el, "guid", "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL,
                         "shadowrun:anthology:v1:" + rec["url"])))
        guid.attrib["isPermaLink"] = "false"
        b.put(el, "pubDate", email.utils.format_datetime(
            ST + dt.timedelta(minutes=n-120), usegmt=True))
        ET.SubElement(el, "enclosure", {"url":rec["url"], "length":str(rec["size"]), "type":rec["mime"]})
        b.put(el, "{" + IT + "}episode", n)
        b.put(el, "{" + IT + "}episodeType", "full")
        if rec["seconds"]:
            b.put(el, "{" + IT + "}duration", rec["duration"])
        audit.append({
            "position":n,"title":rec["title"],"publisher":PUB,"role":"lore",
            "original_publisher_guid":rec["publisher_guid"],"original_episode_link":rec["publisher_link"],
            "source_audio_url":rec["url"],"source_media_type":rec["mime"],
            "source_media_bytes":rec["size"],"scan_status":"full_transcript_pending",
            "transcript_url":None,"editorial_fit_score":None,
            "pre_shutdown_addition":True,"editorial_priority":"high",
            "selection_reason":rec["addition_reason"],"publisher_rss":RSS
        })
    b.put(channel, "x-arcology-build-note", "Publisher RSS original enclosure validation: 122 recordings (120 core + 2 additional pre-Shutdown lore).")
    # RSS namespace-free extension tags are not necessary for readers: remove
    # the temporary verification node after asserting the count.
    channel.remove(channel.findall("x-arcology-build-note")[-1])
    channel.find("description").text = (
        "Independent 122-episode publisher-hosted anthology: 120 original selections plus "
        "two additional pre-Shutdown Renraku lore episodes. Original eight-track feed remains available."
    )
    channel.find("lastBuildDate").text = email.utils.format_datetime(ST + dt.timedelta(minutes=3), usegmt=True)
    xml = ET.tostring(rss.getroot(), encoding="utf-8", xml_declaration=True)
    parsed = ET.fromstring(xml).find("channel")
    items = parsed.findall("item")
    if len(items) != 122 or [x.findtext("guid") for x in items[:120]] != old_guids:
        raise ValueError("An original GUID was changed or final RSS count not 122")
    if [x.find("enclosure").get("url") for x in items[:120]] != old_urls:
        raise ValueError("An original enclosure changed")

    manifest = original + selected
    status_file = H / "status.json"
    status = json.loads(status_file.read_text(encoding="utf-8"))
    status["state"] = "publisher_rss_metadata_validated"
    status["total"] = 122
    status["roles"] = dict(collections.Counter(x["role"] for x in manifest))
    status["publisher_rss_enclosures_validated"] = 122
    status["over_30_min"] = sum(x["seconds"] >= 1800 for x in manifest)
    status["over_60_min"] = sum(x["seconds"] >= 3600 for x in manifest)
    status["unknown_duration"] = sum(x["seconds"] == 0 for x in manifest)
    status["feed_sha256"] = hashlib.sha256(xml).hexdigest()
    status["pinned_pre_shutdown_additions"] = [{
        "slot":e["slot"],"title":e["title"],"guid":e["publisher_guid"],
        "publisher_rss":RSS,"full_transcript_examined":False,
        "short_duration_exception":e["short_duration_exception"]
    } for e in selected]
    status["short_exceptions"] += [
        {"slot":e["slot"],"publisher":e["publisher"],"title":e["title"],
         "minutes":round(e["seconds"]/60, 1)} for e in selected
         if e["seconds"] and e["seconds"] < 1800
    ]
    index_path = H / "v2" / "evidence-checkpoint-120.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    original_rows = [x for x in index["position_audit"] if int(x["position"]) <= 120]
    if len(original_rows) != 120 or sum(x["scan_status"] == "full_publisher_script_reviewed" for x in original_rows) != 16:
        raise ValueError("Existing V2 transcript evidence not as expected; refusing to overwrite")
    index["position_audit"] = original_rows + audit
    index["published_total"] = 122
    index["current_v1_feed_episode_count"] = 122
    index["baseline_pending"] = 106
    index["baseline_full_scripts_reviewed"] = 16
    index["total_distinct_scripts_reviewed"] = 29
    index["release_status"] = "BLOCKED - 106 current episode transcripts pending; NO V2 XML"
    index["snapshot_utc_date"] = "2026-10-23"
    index["source_note"] = "First 120 GUIDs preserved; two additional publisher-confirmed pre-Shutdown lore tracks now subscribed in V1 and awaiting full transcript review for V2."
    current_file = H / "v2" / "evidence-checkpoint-current.json"
    status_v2 = H / "v2" / "STATUS.md"
    v2text = (
        "# Shadowrun transcript-backed V2 checkpoint\n\n"
        "Published V1: **122 audio episodes**, retaining all 120 baseline selections and adding "
        "Neo-Anarchist Episodes 28 (2058 Arcology upgrade) and 29 (2059 corporate context).\n\n"
        "Full publisher scripts reviewed: **29 total**, comprising **16 currently selected "
        "episodes** and **13 researched alternatives**. **106 current V1 episodes are "
        "not yet full-transcript verified.** The two new lore episodes remain pending.\n\n"
        "Do not publish a transcript-backed V2 RSS until verified original audio, "
        "episode-specific full transcript evidence and all release checks pass.\n"
    )
    # All validations complete: write publication and V2 checkpoint as one action step.
    feed_file.write_bytes(xml)
    (H / "selected.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    current_file.write_text(json.dumps(index, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    status_v2.write_text(v2text, encoding="utf-8")
    (H / "build-diagnostic.json").write_text(json.dumps({
        "state":"passed","total":122,"base_count":120,
        "added_pre_shutdown_lore":2,"v2_transcripts_pending":106},indent=2)+"\n")
    (H / "additions-diagnostic.json").write_text(json.dumps({
        "state":"passed","added_slots":[121,122],
        "rss_source":RSS,"publisher_episodes":[28,29],
        "sha256":status["feed_sha256"]
    }, indent=2)+"\n")
    print("PASS: 122 publisher-hosted episodes; two verified pre-Shutdown additions, first 120 GUIDs unchanged")

if __name__ == "__main__":
    try:
        make_additions()
    except Exception as exc:
        (H / "additions-diagnostic.json").write_text(
            json.dumps({"state":"blocked","error":str(exc)},indent=2)+"\n")
        print("BLOCKED: pre-Shutdown addition failed: "+str(exc), file=sys.stderr)
        sys.exit(1)
