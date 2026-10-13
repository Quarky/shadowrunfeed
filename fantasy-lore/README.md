# Fantasy Lore — Creatures, Mythology & Worldbuilding

A public, general-purpose fantasy-lore audio library for roleplaying game worldbuilding. Recordings remain hosted by their original publishers. No MP3 or premium audiobook files are redistributed here.

## RSS subscriptions

- **Combined lore anthology:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/feed-v2.xml
- **Creature ecology:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/creatures.xml
- **Fantasy cultures and history:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/cultures.xml
- **Magic, gods and planes:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/magic-planar.xml
- **Worldbuilding and GM craft:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fantasy-lore/worldbuilding.xml

**Publication:** Before subscribing, verify that [status.json](status.json) reports `state: published` and the selected XML file exists. The generator checks for original publisher audio enclosures and valid file lengths; it will not invent missing recordings. To initialize, [run the GitHub Actions workflow](../.github/workflows/update-fantasy-lore-feed.yml) from the Actions tab. The workflow also refreshes once each week. Use your podcast app's **Add by RSS URL** feature; for Podbean, choose **Search → + Add Feed URL**.

## Selected podcasts

| Podcast | Emphasis |
| --- | --- |
| [Monster Man](https://www.monsterman.org/monsterman) | Classic and contemporary monsters, mythology, ecology and folklore |
| [The Dungeoncast](https://podcasts.apple.com/us/podcast/the-dungeoncast/id1175886354) | D&D monster histories, gods, adventures and lore |
| [Dungeons & Dragons Lorecast](https://linktr.ee/dndlorecast) | Fantasy history, gods, planes and factions |
| [The Travel Log](https://podcasts.apple.com/us/podcast/the-travel-log/id1556137924) | Location and culture studies |
| [Monsters & Multiclass](https://www.buzzsprout.com/222686/episodes) | Creature powers and encounter ideas, excluding irrelevant class commentary |
| [Dragon Talk](https://dragontalk.transistor.fm/) | Official *Lore You Should Know* segments where verified in original publisher RSS |

Selection is thematic, not a quantitative rating or popularity ranking. Published episode counts and omitted sources are recorded in [status.json](status.json).

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
- [Feed generator](generate_feed.py): resolves publisher RSS (including Apple Lookup when needed), validates genuine HTTPS audio enclosures, and builds separate themed RSS files.
- [Weekly GitHub Action](../.github/workflows/update-fantasy-lore-feed.yml): runs independently of the other collection workflows.
- [Status report](status.json): explicitly distinguishes configured feeds from validated, published files.

No episode audio is stored in this repository. All original publisher attribution and copyrights remain with the source creators.
