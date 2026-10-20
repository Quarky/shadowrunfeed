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
- `catalog.json`: sources and theme matching.
- `selection-lock.json`: stable selections, preserving existing episode GUIDs.
- `status.json`: publication evidence.
- `generate_feed.py`: publisher-source rebuild.
- `cover.png`: RSS cover artwork.

The obsolete prior-named feed has been retired and its directory removed. **Only `/anomaly/` is a supported subscription path.** Existing RSS episode GUIDs are retained internally for continuity.

Publisher recordings remain with their creators; no MP3 is redistributed. GitHub workflow validation requires 120 unique HTTPS enclosures, a 60/60 story/actual-play split and valid artwork before publication.

## Full selection rationale and source audit

The [120-episode Markdown audit](https://github.com/Quarky/mdfiles/blob/main/Rpg/Development/Anomaly%20Audio%20Feed%20-%20120%20Episode%20Selection%20Reasons%20and%20Source%20Audit.md) documents **every included recording**: publisher show, original episode page or audio enclosure, original date, short source-synopsis evidence, an individualized reason for relevance to Anomaly, a candid fit grade, and transparent limits including source-system differences and missing narrative context. It also explains the original interleaver, the 29 currently curated override slots, and the 35 current candidate sources. Canonical campaign documentation stays under `Quarky/mdfiles/Rpg/Development/`; this repository hosts the RSS source and generated media index.

## Optional replay shelf — already listened shows

**[Optional familiar-listening RSS](optional-listening/feed-v2.xml)** (9 tracks) keeps three *Worlds Beyond Number* and six *Dungeons of Drakkenheim* recordings for reviewing at leisure. These were **not removed because they were intrinsically poor selections**; the listener already follows these shows and prefers the 120-track main feed to highlight unfamiliar material. The former main positions have been refilled with other verified publishers.

The [optional index](optional-listening/README.md) records the original locations and source titles. The generator no longer depends on any prior-named directory.
