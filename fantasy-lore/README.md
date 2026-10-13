# Fantasy Lore — Creatures, Mythology & Worldbuilding

A public, general-purpose fantasy-lore audio library for roleplaying game worldbuilding. Recordings remain hosted by their original publishers. No MP3 or premium audiobook files are redistributed here.

## RSS subscriptions

- **Recommended: ranked alternating lore + story:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/feed-v2.xml
- **Ranked queue alias:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/ranked-feed.xml
- **Creature ecology:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/creatures.xml
- **Fantasy cultures and history:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/cultures.xml
- **Magic, gods and planes:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/magic-planar.xml
- **Worldbuilding and GM craft:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/worldbuilding.xml

**Publication:** The initial ranked feed was successfully generated with 28 verified publisher-hosted episodes on 2026-10-13; the automated updater may expand or refine that list. Check [current publication status](status.json) and [the episode-by-episode ranked listening list](episode-list.md). The generator checks for actual original publisher audio enclosures and valid lengths. A new builder run refreshes once each week and on catalog/algorithm changes. Use your podcast app's **Add by RSS URL** feature; for Podbean, choose **Search → + Add Feed URL**.

## Selected podcasts

| Podcast | Emphasis |
| --- | --- |
| [Monster Man](https://www.monsterman.org/monsterman) | Classic and contemporary monsters, mythology, ecology and folklore |
| [The Dungeoncast](https://podcasts.apple.com/us/podcast/the-dungeoncast/id1175886354) | D&D monster histories, gods, adventures and lore |
| [Dungeons & Dragons Lorecast](https://linktr.ee/dndlorecast) | Fantasy history, gods, planes and factions |
| [The Travel Log](https://podcasts.apple.com/us/podcast/the-travel-log/id1556137924) | Location and culture studies |
| [Monsters & Multiclass](https://www.buzzsprout.com/222686/episodes) | Creature powers and encounter ideas, excluding irrelevant class commentary |
| [Dragon Talk](https://dragontalk.transistor.fm/) | Official *Lore You Should Know* segments where verified in original publisher RSS |
| [D&D Legends and Lore](https://podcasts.apple.com/us/podcast/d-d-legends-and-lore/id1769219620) | Narratively presented monster, deity and culture lore |
| [Worlds Beyond Number](https://podcasts.apple.com/us/podcast/worlds-beyond-number/id1670750937) | NPC relationships, characterization, world texture and compelling dialogue |
| [The Silt Verses](https://podcasts.apple.com/us/podcast/the-silt-verses/id1547222295) | Dramatized religious beliefs, rituals, cults and ordinary characters |
| [Dark Dice](https://podcasts.apple.com/us/podcast/dark-dice/id1437360249) | Fully performed fantasy encounters and character-driven tension |
| [The Once and Future Nerd](https://podcasts.apple.com/us/podcast/the-once-and-future-nerd/id711119555) | Drama, society and court dynamics; included only when a continuous publisher-audio arc can be verified |

The main feed alternates **lore → performed story → lore → performed story**, preserving the original order of consecutive serialized narrative chapters. Lore-only topic subscriptions remain separate. The latest [episode list](episode-list.md) and [machine-readable ranked list](episode-list.json) are published by the automated updater. Show ratings are **not** episode ratings. The transparent algorithm uses 52% episode thematic relevance, 22% storytelling/NPC usefulness, 16% Bayesian-smoothed US Apple show rating, and 10% diversity, plus matching and repeated-topic penalties. Stars and counts are dated editorial snapshots rather than live episode popularity metrics. Episodes must exist in actual publisher feeds with valid HTTPS audio enclosures.

## Reading references

- [D&D 2014 Monster Manual](https://www.dndbeyond.com/sources/dnd/mm-2014) — baseline monster lore.
- [Official D&D SRD](https://dnd.wizards.com/resources/systems-reference-document) — open rules and creatures.
- [Archives of Nethys](https://2e.aonprd.com/Monsters.aspx) — creature families and unusual encounter mechanics.
- [Forgotten Realms Wiki](https://forgottenrealms.fandom.com/wiki/Main_Page) — setting reference; check original sources.
- [The Monsters Know What They're Doing](https://www.themonstersknow.com/why-these-tactics/) — believable monster behavior.
- [Sly Flourish — Lazy World Building](https://slyflourish.com/lazy_world_building.html) — practical settlements and factions.
- [The Alexandrian](https://thealexandrian.net/) — node-based adventure design.
- [Resources for World-Builders](https://acoup.blog/resources-for-world-builders/) — real-world history and economies.

## Implementation

- [Catalog](catalog.json): independent podcast publishers, subject filters and reference links.
- [Feed generator](generate_feed.py) + [ranking code](ranked.py): resolves original publisher RSS, validates HTTPS enclosures, ranks and sequences lore/serial story pairs, and builds themed feeds. Synthetic RSS item dates are used only for listening-order display; original dates remain in metadata.
- [Weekly GitHub Action](../.github/workflows/update-fantasy-lore-feed.yml): runs independently of the other collection workflows.
- [Status report](status.json): explicitly distinguishes configured feeds from validated, published files.

No episode audio is stored in this repository. All original publisher attribution and copyrights remain with the source creators.
