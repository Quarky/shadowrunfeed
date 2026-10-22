# Shadowrun — Arcology Shutdown audio anthology

This **separate** RSS collection follows the documented transcript-first / publisher-source-first campaign-podcast curation procedure. It is an outside-fiction inspiration playlist, not a recording of campaign sessions or a source of canonical events.

## Subscribe

**Independent anthology feed:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/shadowrun/anthology/feed-v1.xml

In Podbean: **Search → + Add Feed URL**; paste the URL. A podcast app may cache items. **The original short Arcology collection remains** at https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/feed-v2.xml; no original GUID or subscription was changed.

## 120-track order

| Playlist positions | Interleaving | Count |
| --- | --- | --- |
| 1–20 | Story / actual play | 10 stories + 10 actual plays |
| 21–40 | Lore / actual play | 10 lore + 10 actual plays |
| 41–120 | Actual play / story | 40 actual plays + 40 stories |
| Total | | **50 stories, 60 actual plays, 10 lore** |

The publisher-source catalog is **not** taken from D&D/Anomaly. Fiction recordings explore networked society, cramped living spaces, competing loyalties and corporate futures; actual plays are genuine Shadowrun recordings; lore covers in-world history, Matrix and corporate culture.

Sources are **The Strata**, **The Program audio series**, **COSMIKO: Neon Night**, **InkandNeon**, **Shadowrun: Origins**, **The Arcology Shadowrun Podcast**, **Pink Fohawk**, **SINless**, **Neo-Anarchist Podcast**, and **Acceptable Losses**.

## Documentation and validation

- [Source policy, themes and mix](policy.json)
- [Publisher-backed episode index and listening rationale](selected.json)
- [Source inventory and quality status](status.json)
- [Actual public delivery readback](delivery-status.json) — reports `verified` only after byte comparison against both the committed feed and public CDN.
- [Publisher RSS build and deduplication gate](build.py)
- [Delivery validation script](verify_delivery.py)
- [RSS XML](feed-v1.xml)

Original podcast recordings are not rehosted. Episode-specific descriptions distinguish publisher metadata from a full transcript: **no episode is described as fully transcript-audited unless its complete recording/transcript was genuinely examined**. Metadata checks and publisher enclosure headers are not proof of uninterrupted playback; external Podbean subscription has not been independently tested.

This is a _new independent anthology_ and does not edit the original short collection, D&D/Anomaly feed or other campaign feeds.
