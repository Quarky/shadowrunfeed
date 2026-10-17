# Star Wars RPG — Ranked Lore + Story Inspiration Feed

An independently curated Star Wars roleplaying inspiration queue. Learn a piece of the galaxy's lore, then hear a performed Star Wars RPG scene showing how characters, culture, dialogue, and choices work in play.

## Recommended podcast subscriptions

- **[Ranked 1:1 Lore → Story feed](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/learning-feed-v2.xml)** — alternates topical lore and continuous, publisher-hosted actual-play fiction.
- **[Lore only](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/learning-lore.xml)** — species, creatures, culture, planets, technology and Force mythology.
- **[Story only](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/learning-story.xml)** — publisher-hosted, consecutively ordered story chapters.

Before subscribing check **[publication status](learning-status.json)** (state must be `published`) and the **[complete episode list](learning-episodes.md)**. In Podbean choose Search → + Add Feed URL. Existing [FFG sampler](feed-v2.xml), [D6 anthology](d6-feed.xml), and all show-specific RSS files are untouched.

## How it selects episodes

**52% topic relevance**, **22% NPC/storytelling usefulness**, **16% show-level audience rating** (smoothed toward 4.5 stars with a 250-vote prior), and **10% diversity**, followed by source-balance and pairing bonuses. The score is an **editorial algorithmic recommendation**, never an individually reviewed or star-rated episode. Show ratings are dated regional snapshots; sample sizes and applicability are always shown. A star rating on a mixed-topic series cannot be transferred to its Star Wars episodes.

**Lore:** original, licensed publisher-podcast audio from sources such as [Star Wars In Character](https://podcasts.apple.com/us/podcast/star-wars-in-character/id420574267), [its archive](https://podcasts.apple.com/us/podcast/star-wars-in-character-archives/id1491547719), [The Star Wars Canon Timeline Podcast](https://podcasts.apple.com/us/podcast/the-star-wars-canon-timeline-podcast/id1744643686), [Star Wars: Old Canon Book Club](https://podcasts.apple.com/us/podcast/star-wars-old-canon-book-club/id1686249893), [Star Wars Explained](https://podcasts.apple.com/us/podcast/star-wars-explained/id1488511803) and [Eye on Canon](https://podcasts.apple.com/us/podcast/id1780459329). News, reaction videos, calendars, rankings, casting and advertising-only episodes are filtered out.

**Story:** existing *Star Wars FFG* and *West End Games D6* publisher feeds are used for serialized campaigns: *Campaign — The Mynock*, *Force Majeure — Coldfire Chronicles*, *Dice for Brains*, *Respect the Crit — Empire's Edge*, and *Nastygram — Empire's End / Dreamscapes*. The builder uses **chapter 1 onward, never skipping missing chapters**. D6 mechanics aren't misrepresented as FFG mechanics. The source collection's explicitly excluded show stays excluded.

## What to learn from each pair

| Lore subject | Story application | GM ideas |
| --- | --- | --- |
| Alien societies, species and creatures | Crew contacts and ordinary people | Clothing, occupations, mannerisms, rituals, local tensions, predator ecology |
| Planets, geography and underworlds | Smuggling and frontier campaigns | Markets, bureaucracy, travel, local faction networks |
| Jedi/Sith philosophies and unusual Force phenomena | Force-sensitive character drama | Temptation, traditions, competing interpretations, moral consequences |
| Droids, ships and forgotten technology | Heists, troubleshooting, starport scenes | Equipment as culture, maintenance life, grounded hazards |
| Republic, Empire, Mandalorians and smugglers | Political and crew-centered campaigns | Differing institutional viewpoints, negotiation, consequences |

Treat **Canon vs Legends** as separate continuities and identify the source in adaptations. These are brainstorming references, not claims about a single roleplaying world.

## Written lore references

- [Official Star Wars Databank](https://www.starwars.com/databank): character, creature, ship and planet entries.
- [Wookieepedia](https://starwars.fandom.com/wiki/Main_Page): fan-compiled Canon/Legends entries; verify references and continuity.
- [EDGE Studio Star Wars RPG](https://www.edge-studio.net/categories-games/star-wars/): FFG/EDGE RPG product and rules context.
- [SWTOR lore articles](https://swtorista.com/articles/category/lore/): Old Republic planets, groups and cultures.

Only links and metadata are published; no licensed audio, paid audiobook, full text or sourcebook is mirrored.

## Maintenance

- [`learning_catalog.json`](learning_catalog.json) — editorial policy, source links, original evidence and ranking settings.
- [`generate_learning.py`](generate_learning.py) — validates sources and publisher-hosted episode enclosures, generates an alternating feed and rated ordered list.
- [`learning-episodes.md`](learning-episodes.md) and [`learning-episodes.json`](learning-episodes.json) — generated exact episode sequence with ranking rationale.
- [`learning-status.json`](learning-status.json) — generated coverage and missing sources; an unavailable source is not represented as published.
- [GitHub Actions updater](../.github/workflows/update-star-wars-learning.yml) — independent build, runs weekly and on source/script updates.

All existing podcast feed identities and downloadable recordings stay with their original publishers.
