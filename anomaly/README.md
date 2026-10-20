# Anomaly — D&D campaign listening feed

**New canonical RSS:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/feed-v2.xml

This is a 120-track original-publisher listening catalog: 60 performed stories interleaved one-for-one with 60 RPG actual plays. These are outside inspiration, not recordings of the user's campaign or new canon.

## Six listening themes

1. **Communities, culture and relationships** — NPC voices, friendships, daily life, cross-cultural encounters and settlements. **Veyrun's Reach is not an Anomaly campaign location**; earlier references conflated an author's city with the campaign setting.
2. **Eilistraee and defectors** — drow leaving Lolth's traditions, allied elves, refuge, trust and personal freedom, without assuming a location from the authors' other setting.
3. **Itich and ancient ruins** — survival, unusual societies and the abandoned dwarven forge/mine.
4. **Wall and screamers** — environmental threats, psychic impressions, anomalous crystals and the Wallfeeder.
5. **Attina and transformations** — identity, magic, agency, intimate conversations and long-term consequences.
6. **Ancient minds and aberrations** — aboleths, illithids, elder brains and unusual magical phenomena.

## What is published

- `feed-v2.xml`: canonical RSS for subscription.
- `feed.xml`: matching alternate RSS path.
- `episodes.json` and `episodes.md`: the ranked listening sequence.
- `fresh-episode-catalog.json`: frozen 120-episode editorial selection, publisher enclosure links and source metadata.
- `catalog.json` and `selection-lock.json`: historical selection evidence, no longer controlling RSS publication.
- `status.json`: publication evidence.
- `publish_fresh_rss.py`: deterministic, independent RSS 2.0 + iTunes publisher, without legacy identities.
- `cover.png`: RSS cover artwork.

The obsolete prior-named feed has been retired and its directory removed. **Only `/anomaly/` is a supported subscription path.** **The primary RSS was intentionally rebuilt as a NEW podcast on 20 October 2026.** All 120 episode GUIDs were replaced once with fresh, standards-based UUID identities. Previously imported entries may appear again, and listening progress attached to the old episode IDs may not transfer.

Publisher recordings remain with their creators; no MP3 is redistributed. GitHub workflow validation requires 120 unique HTTPS enclosures, a 60/60 story/actual-play split and valid artwork before publication.

## Fresh podcast rebuild and import

On 20 October 2026 the user requested a complete rebuild of the existing primary RSS, not an incremental patch. The current main feed is a **new show identity with 120 new UUID episode identities** at the **same Anomaly RSS URL**. It retains the curated 120 recordings, their publisher-hosted enclosures and 60/60 interleaving, but no legacy episode IDs or old feed directory references appear in its XML.

This reset is intentional and may result in a new Podbean subscription entry or reset play history. Never revert the feed to the previous identifiers while troubleshooting import. [Source manifest](fresh-episode-catalog.json) and [fresh builder](publish_fresh_rss.py) are authoritative; the old publisher discovery code is archived as historical source only. GitHub publication is independently verified against actual CDN bytes in [cdn-health.json](cdn-health.json).

## Podbean refresh and subscription compatibility

**Subscribe to the primary RSS at the exact URL:** `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/feed-v2.xml`

On Android or iOS Podbean, choose **Search → + Add Feed URL** and paste that address. The retired, formerly named directory and its feed were intentionally deleted at the listener's request; **subscriptions still pointing at the deleted address cannot update themselves**. Remove the stale entry and add the Anomaly address. This is an external RSS subscription; it does not require importing or uploading the publisher audio.

The GitHub Actions RSS builder writes `feed-v2.xml` and `feed.xml` to `main`; these are byte-for-byte identical. After publishing, `anomaly/verify_published_rss.py` attempts a jsDelivr branch-cache purge and validates the actual public subscription response against the committed RSS, including all 120 GUIDs, valid HTTPS enclosures, nine optional episodes, artwork, and feed identity. [CDN verification report](cdn-health.json) uses `state: verified` only after a literal byte-for-byte CDN match. A missing or stale report is **not** proof of live delivery.

The CDN caches `@main` branch URLs for up to roughly 12 hours unless invalidated. Podcast players may then independently delay refresh. After this explicit, one-time new-podcast reset, the 120 new UUIDs, item publication dates and RSS bytes are deterministic and stable across rebuilds. Changing episode IDs again would cause duplicate entries. The weekly builder revalidates the 120-entry manifest; new listening choices require a catalog edit rather than automatic replacement with recent releases.

## Full selection rationale and source audit

The [120-episode Markdown audit](https://github.com/Quarky/mdfiles/blob/main/Rpg/Development/Anomaly%20Audio%20Feed%20-%20120%20Episode%20Selection%20Reasons%20and%20Source%20Audit.md) documents **every included recording**: publisher show, original episode page or audio enclosure, original date, short source-synopsis evidence, an individualized reason for relevance to Anomaly, a candid fit grade, and transparent limits including source-system differences and missing narrative context. It also explains the original interleaver, the 29 currently curated override slots, and the 35 current candidate sources. Canonical campaign documentation stays under `Quarky/mdfiles/Rpg/Development/`; this repository hosts the RSS source and generated media index.

## Optional replay shelf — already listened shows

**[Optional familiar-listening RSS](optional-listening/feed-v2.xml)** (9 tracks) keeps three *Worlds Beyond Number* and six *Dungeons of Drakkenheim* recordings for reviewing at leisure. These were **not removed because they were intrinsically poor selections**; the listener already follows these shows and prefers the 120-track main feed to highlight unfamiliar material. The former main positions have been refilled with other verified publishers.

The [optional index](optional-listening/README.md) records the original locations and source titles. The generator no longer depends on any prior-named directory.
