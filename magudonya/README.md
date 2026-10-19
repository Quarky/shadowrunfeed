# Magudonya / Anomaly — D&D campaign audio anthology

A **separate 120-episode RSS feed** inspired by the played and established campaign lore. It is a curated listening anthology, not a recording of your campaign and not a supplement to be treated as canonical.

## Subscribe

**RSS address:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/feed-v2.xml

Add by URL in your podcast player. Podbean: **Search → + Add Feed URL**. This address is usable after the publisher-audio generator's first successful GitHub Actions run. Validate the [publication status](status.json) and [episodes](episodes.md) before describing it as live.

## Format and scope

Exactly **120 recordings, 60 dramatized stories and 60 actual plays**, with alternating **story → actual play** pairs. Six 20-episode theme chapters, ten fiction/actual-play pairs each:

1. **Veyrun's Reach:** daily life, magical conveniences, social relationships, different cultures and conversational styles. Do not substitute Pacthold's clothing-for-status norms for Veyrun's Reach.
2. **Eilistraee:** defecting Lolth drow, safety and trust in the un-walled southeastern woodland sanctuary, alliance with high and wood elves; RPPR *Drow and Dracoliches* includes a paladin of Eilistraee.
3. **Itich:** primitive horned insectoid survivors of abandoned dwarven mines, underground ecological society; they **do not** make metal there.
4. **Wall and screamers:** colossal collapsed earth wall, psychic flashes, semi-astral bacteria, metal crystal infection, and the previously tamed Wallfeeder.
5. **Attina and anomaly:** strong character agency, Weave distortions and transformation, nuanced personal relationships.
6. **Ancient minds:** aboleths, illithids, elder brains, mind prisons, mental influence, environmental mysteries.

The show index deliberately prioritizes *living stories, NPC motivations and character interaction*, not ratings of table pace or fabricated engagement metrics. Fictional plots from third-party shows are **inspiration only** and do not alter the established campaign canon.

## How it works

- `catalog.json`: thematic sources and publisher RSS/Apple search hints.
- `generate_feed.py`: obtains real publisher RSS enclosures, omits invalid/unavailable audio, and selects the fixed 60/60 interleaved anthology. The generated `selection-lock.json` preserves publisher episode IDs on later updates.
- `episodes.md`, `episodes.json`: traceable 1–120 listening sequence, labels and publisher links.
- `status.json`: generated count, any unavailable sources and real publication status.
- `feed-v2.xml`, `feed.xml`: Podbean-compatible RSS files, with original publisher media URLs, correct enclosure lengths and immutable entry GUIDs.
- `.github/workflows/update-magudonya-feed.yml`: validates and commits output with a weekly update, without modifying the Star Wars, Shadowrun, Ravnica or Fantasy Lore subscriptions.

No original audio is uploaded, scraped into a file, or rehosted. The anthology is unaffiliated with the creators and with Wizards of the Coast.
