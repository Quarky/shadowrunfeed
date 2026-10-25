#!/usr/bin/env python3
"""Conservative Star Wars campaign episode discovery, never production RSS promotion.

Searches publisher RSS and Apple's podcast-episode directory for Shard Moon and
Moraband story-level parallels. Transcript URLs are only sampled when publicly
available and explicitly linked by the publisher. Saves *analysis metadata*,
never raw copyrighted transcripts or audio. A hit is not publication approval.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlparse, parse_qsl
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
OUT = HERE / "deep-match-v2-discovery.json"
AGENT = "QuarkyCampaignEpisodeResearch/2.0 (+https://github.com/Quarky/shadowrunfeed)"
PODCAST = "{https://podcastindex.org/namespace/1.0}transcript"
MAX_RSS_BYTES = 15_000_000
MAX_TRANSCRIPT_SAMPLE = 140_000
PUBLISHER_FEEDS = {
    "derelict": "https://feeds.megaphone.fm/SBP4341397353",
    "white-vault": "https://feeds.megaphone.fm/SBP7754210900",
    "amca": "https://amorecivilizedage.libsyn.com/rss",
    "nastygram": "https://nastygram.libsyn.com/rss",
    "force-majeure": "https://forcemajeurepod.libsyn.com/rss",
    "janus-descending": "https://janusdescending.libsyn.com/rss",
    "respect-the-crit": "https://feeds.megaphone.fm/respectthecrit",
}
APPLE_QUERIES = [
    "Korriban Sith Tomb",
    "Moraband Sith academy",
    "star wars holocron ancient jedi",
    "abandoned android factory actual play",
    "research base experiment artificial intelligence",
    "alien archaeology lost civilization podcast",
    "laboratory containment science fiction audio drama",
]
THEME_RULES = {
    "MORABAND": [
        (("korriban",), "exact planet alternate name", 36),
        (("moraband",), "exact planet", 36),
        (("sith", "tomb"), "Sith tomb", 30),
        (("sith", "academy"), "Sith academy", 30),
        (("sith", "temple"), "Sith temple", 29),
        (("holocron", "jedi"), "Jedi/holocron", 25),
        (("ancient", "force"), "ancient Force mystery", 21),
        (("old republic", "sith"), "Old Republic/Sith", 20),
        (("jedi", "relic"), "Jedi relic investigation", 19),
    ],
    "SHARD MOON": [
        (("android", "factory"), "android manufacturing AI", 36),
        (("ai", "facility"), "AI-controlled facility", 34),
        (("artificial intelligence", "station"), "automated outpost", 30),
        (("alien", "laboratory"), "alien laboratory", 30),
        (("research", "facility"), "research facility", 28),
        (("research", "station"), "isolated research station", 26),
        (("experimental", "subjects"), "experimental wards/subjects", 26),
        (("containment", "breach"), "containment failure", 28),
        (("alien", "ruins"), "alien ruins", 25),
        (("ancient", "artifact"), "ancient artifact investigation", 25),
        (("abandoned", "station"), "abandoned space installation", 23),
        (("malfunction", "robot"), "automated defense malfunction", 24),
        (("remote", "outpost"), "remote outpost", 20),
    ],
}
EXCLUSIONS = ("trailer", "teaser", "announcement", "reaction", "bonus chat",
              "cast interview", "behind the scenes", "movie review")
EVIDENCE = json.loads((HERE / "deep-match-v2-evidence.json").read_text(encoding="utf-8"))
IN_FEED_TITLE = {
    re.sub(r"\W+", " ", unescape(x["original_title"]).casefold()).strip()
    for x in EVIDENCE["selected"]
}
IN_FEED_GUID = {x["guide"] for x in EVIDENCE["selected"]}

def request_bytes(url: str, limit: int = MAX_RSS_BYTES) -> bytes:
    if not url.startswith("https://"):
        raise ValueError("HTTPS required")
    req = Request(url, headers={"User-Agent": AGENT, "Accept": "application/rss+xml, application/xml, text/xml, application/json, text/html, text/plain"})
    with urlopen(req, timeout=18) as resp:
        if int(resp.status) != 200:
            raise ValueError("HTTP " + str(resp.status))
        data = resp.read(limit + 1)
    if len(data) > limit or not data:
        raise ValueError("empty or oversized response")
    return data

def clean(value: str) -> str:
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(value)).strip()

def signed(url: str) -> bool:
    fields = {key.casefold() for key, _ in parse_qsl(urlparse(url).query)}
    return bool(fields & {"key", "timetoken", "request_event_id", "expires", "exp", "token", "x-amz-signature"})

def editorial_prefilter(title: str, summary: str) -> tuple[str, int, list[str]] | None:
    title_l = clean(title).casefold()
    body = clean(title + ". " + summary).casefold()
    if not title_l or any(word in title_l for word in EXCLUSIONS):
        return None
    rankings = []
    for lane, rules in THEME_RULES.items():
        valid = []
        for needles, label, points in rules:
            if all(re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", body) for needle in needles):
                title_hits = sum(bool(re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", title_l)) for needle in needles)
                valid.append((points + title_hits * 5, label))
        if valid:
            valid.sort(reverse=True)
            score = min(70, valid[0][0] + min(9, 3 * (len(valid) - 1)))
            rankings.append((lane, score, [label for _, label in valid[:4]]))
    return max(rankings, key=lambda r: r[1]) if rankings else None

def rss_episode_records(source: str, feed_url: str):
    root = ET.fromstring(request_bytes(feed_url))
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError("not a podcast RSS channel")
    result = []
    for item in channel.findall("item")[:1200]:
        title = clean(item.findtext("title") or "")
        desc = clean(item.findtext("description") or "")
        reviewed = editorial_prefilter(title, desc)
        if not reviewed:
            continue
        lane, score, matches = reviewed
        enclosure = item.find("enclosure")
        media = enclosure.get("url", "") if enclosure is not None else ""
        mimetype = enclosure.get("type", "") if enclosure is not None else ""
        declared_size = enclosure.get("length", "0") if enclosure is not None else "0"
        transcripts = [x.get("url") for x in item.findall(PODCAST) if x.get("url", "").startswith("https://")]
        guid = (item.findtext("guid") or "").strip()
        if guid in IN_FEED_GUID:
            continue
        result.append({
            "source": source, "source_rss": feed_url, "title": title,
            "publisher_synopsis": desc[:950], "original_guid": guid,
            "episode_link": (item.findtext("link") or "").strip(),
            "role": "research_candidate", "theme": lane, "metadata_relevance": score,
            "triggered_scene_mechanisms": matches,
            "confidence": "publisher_metadata", "full_transcript_examined": False,
            "publisher_transcript_urls": transcripts[:3],
            "enclosure_type": mimetype, "declared_bytes": declared_size,
            "has_https_publisher_enclosure": media.startswith("https://"),
            "publisher_enclosure_url": media if media.startswith("https://") and not signed(media) else None,
            "publisher_pub_date": (item.findtext("pubDate") or "").strip(),
            "enclosure_signed_or_volatile": signed(media) if media else False,
            "audio_reachability_verified": False,
            "release_state": "discovery_only_requires_source_review"
        })
    return result

def apple_episode_records():
    output = []
    for query in APPLE_QUERIES:
        uri = "https://itunes.apple.com/search?" + urlencode({
            "term": query, "media": "podcast",
            "entity": "podcastEpisode", "limit": 100, "country": "us"
        })
        try:
            entries = json.loads(request_bytes(uri, 6_000_000)).get("results", [])
        except Exception as exc:
            output.append({"query": query, "error": type(exc).__name__})
            continue
        for x in entries:
            if x.get("kind") != "podcast-episode":
                continue
            title = x.get("trackName", "")
            desc = x.get("description") or x.get("shortDescription") or ""
            result = editorial_prefilter(title, desc)
            if not result:
                continue
            lane, score, matches = result
            output.append({
                "source": "apple-podcast-episode-search", "search_query": query,
                "title": clean(title), "publisher_synopsis": clean(desc)[:950],
                "original_guid": str(x.get("trackId") or ""),
                "episode_link": x.get("trackViewUrl", ""),
                "publisher": x.get("collectionName", ""), "theme": lane,
                "metadata_relevance": score, "triggered_scene_mechanisms": matches,
                "confidence": "directory_metadata", "full_transcript_examined": False,
                "audio_reachability_verified": False, "publisher_enclosure_verified": False,
                "release_state": "discovery_only_requires_publisher_rss_matching"
            })
    return output

def annotate_transcript_samples(records):
    """Sample only publisher-linked plaintext/HTML; store *findings*, never passage text."""
    checked = 0
    for episode in sorted(records, key=lambda r:r["metadata_relevance"], reverse=True)[:15]:
        for url in episode.get("publisher_transcript_urls", []):
            if not re.search(r"\.(txt|html|htm)(?:$|\?)", url, re.I):
                episode["transcript_sample_status"] = "linked_but_not_public_plaintext"
                continue
            try:
                data = request_bytes(url, MAX_TRANSCRIPT_SAMPLE)
                excerpt = clean(data.decode("utf-8", errors="replace"))
                if len(excerpt) < 400:
                    raise ValueError("transcript sample too short")
                review = editorial_prefilter(episode["title"], excerpt)
                episode["transcript_sample_status"] = "bounded_public_text_sample"
                episode["transcript_sample_chars"] = len(excerpt)
                episode["transcript_sample_theme_corrob"] = bool(review and review[0] == episode["theme"])
                episode["transcript_sample_url"] = url
                # Never imply full transcript coverage or copy copyrighted dialogue.
                checked += 1
                break
            except Exception as exc:
                episode["transcript_sample_status"] = "fetch_failed_" + type(exc).__name__
    return checked

def main():
    if "--self-test" in sys.argv:
        assert editorial_prefilter("78: Korriban", "Ancient Sith tombs")[0] == "MORABAND"
        assert editorial_prefilter("Android factory", "AI-controlled facility")[0] == "SHARD MOON"
        assert editorial_prefilter("Baking a pie", "Vegetable recipes") is None
        assert signed("https://host.invalid/file.mp3?timetoken=123")
        assert not signed("https://traffic.libsyn.com/audio.mp3")
        print("PASS: editorial classification, negative case and volatile URL gate")
        return
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(rss_episode_records, name, url):name for name,url in PUBLISHER_FEEDS.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results.extend(future.result())
            except Exception as exc:
                failures.append({"source":name, "error":type(exc).__name__ + ": " + str(exc)[:200]})
    apples = apple_episode_records()
    search_errors = [x for x in apples if "error" in x]
    results.extend(x for x in apples if "error" not in x)
    dedup = {}
    for episode in results:
        key = (episode["source"] if episode["source"] != "apple-podcast-episode-search" else episode.get("publisher", ""),
               re.sub(r"\W+", "", episode["title"].casefold()))
        if key not in dedup or episode["metadata_relevance"] > dedup[key]["metadata_relevance"]:
            dedup[key] = episode
    candidates = sorted(dedup.values(), key=lambda e:(-e["metadata_relevance"],e["source"],e["title"]))
    sampled = annotate_transcript_samples(candidates)
    data = {
        "edition": "star_wars_deep_match_v2", "source_campaigns": ["shard_moon", "moraband"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "existing_published_feed_preserved": True,
        "discovery_is_not_automated_rss_promotion": True,
        "searched_source_feeds": len(PUBLISHER_FEEDS), "publisher_failures": failures,
        "apple_queries": APPLE_QUERIES, "apple_search_errors": search_errors,
        "candidate_count": len(candidates), "publisher_transcript_samples": sampled,
        "method": "Multiple-constraint scenario prefilter; metadata scores are not transcript review. Human scene-level audit and exact episode/publisher enclosure checks required before adding.",
        "candidates": candidates[:150]
    }
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISCOVERY: " + str(len(candidates)) + " candidates; " + str(len(failures)) + " publisher errors; " + str(sampled) + " transcript snippets")
    print("Written " + str(OUT))

if __name__ == "__main__":
    main()
