# Magudonya / Anomaly — Fantasy Lore & Creature Inspiration

Independent curated fantasy lore listening library for developing **Phillip Berrie's Magudonya** and the Anomaly D&D campaign. Uses **publisher-hosted audio enclosures**, never copied MP3s. Created 2026-10-13; initial selections are editorial and deliberately broad, for later refinement.

## Podcast subscriptions — Podbean-compatible RSS

**Main anthology:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/feed-v2.xml

| Specialized subscription | Link | What it covers |
| --- | --- | --- |
| Creature ecology & aberrations | [creatures.xml](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/creatures.xml) | Creatures, folklore, wild ecology, monster behavior and aberrations |
| Cultures & settlements | [cultures.xml](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/cultures.xml) | Villages, empires, Drow/elf/dwarf societies, wilderness, travel |
| Magic, gods & strange planes | [magic-planar.xml](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/magic-planar.xml) | Arcane ecology, gods, planes, aberrant magic |
| Worldbuilding & GM craft | [worldbuilding.xml](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/magudonya/worldbuilding.xml) | Ecological encounter design, dungeons, narrative structure |

**Only subscribe after [status.json](status.json) says `state: published` and the XML actually exists.** On Podbean: **Search → + Add Feed URL**. Other apps: **Add Podcast by RSS URL**. Use **feed-v2.xml** for a fresh subscription to avoid older CDN/app caches.

Every audio entry has a verified publisher RSS item, the publisher's actual HTTPS MP3/audio enclosure, a nonzero file size, the original episode date, a persistent GUID and source credits. The feed does not make inaccessible audiobooks/YouTube videos appear as podcast recordings. The anthology includes the **original 1600×1600 PNG cover** produced by the scheduled builder (not copied publisher art).

## Podcast source lineup

| Priority | Publisher / show | Why selected | Inclusion |
| --- | --- | --- | --- |
| 1 | [Monster Man — James Holloway](https://www.monsterman.org/monsterman) | Monster history, ecology, myth and biological/worldbuilding implications | Broad monster selections, up to 28 |
| 2 | [The Dungeoncast](https://podcasts.apple.com/us/podcast/the-dungeoncast/id1175886354) | Gods, D&D monsters, worldbuilding lore and relationships | Relevant lore topics only, up to 25 |
| 3 | [Dungeons & Dragons Lorecast](https://linktr.ee/dndlorecast) | Ancient history, gods, factions, planes and settlements | Relevant lore topics, up to 24 |
| 4 | [The Travel Log](https://podcasts.apple.com/us/podcast/the-travel-log/id1556137924) | Faerûn settlements, cultures, travel and encounters | Location studies, up to 22 |
| 5 | [Monsters & Multiclass](https://www.buzzsprout.com/222686/episodes) | How individual monster abilities and environmental encounters actually play | Monsters & worldbuilding only; exclude class commentary, up to 22 |
| 6 | [Dragon Talk — official D&D](https://dragontalk.transistor.fm/) | **Lore You Should Know** official lore conversations | Only items with explicit 'Lore You Should Know' show-note text, up to 14 |

Actual included counts are in [status.json](status.json) once the build publishes. Up to means a *maximum*, not a claim that the publisher's current RSS exposes that many verified items. The weekly rebuild catches new qualifying episodes without introducing unrelated news or replacing the other campaign feeds.

**Focus this collection on old and new monster lore, not general D&D news.** Featured search interests include: Eilistraee/Lolth, drow, underground cultures, mind flayers/elder brains, aboleths, bulettes, purple worms, magic/weave, fey and mysterious planes, crystal magic, forests, guilds and wilderness.

## Lore documents and reference libraries

These are **reading links**, not playable episodes. They remain outside RSS unless a creator publishes genuine audio.

| Source | GM use |
| --- | --- |
| [Magudonya — Phillip Berrie's original world](https://www.worldanvil.com/w/magudonya-phillberrie) | **Canonical priority**: history, religions, people, geography, innate magic |
| [Engelian Adventures — original D&D play-by-post](https://www.dndbeyond.com/forums/dungeons-dragons-discussion/play-by-post/47061-engelian-adventures) | Original portrayals, speech patterns, NPC relationships, character lore |
| *Transgressions* (private user-provided PDF) | Engelian transformations and setting particulars; **private source only** |
| [D&D 2014 Monster Manual](https://www.dndbeyond.com/sources/dnd/mm-2014) | Original 2014 creature lore, abilities, habits; paid access may apply |
| [Official SRD 5.1 (CC BY 4.0)](https://dnd.wizards.com/resources/systems-reference-document) | 2014-compatible open creature/stat reference |
| [SRD 5.1 in Markdown](https://github.com/oldmanumby/dnd.srd.5.1) | Reference when creating indexed Markdown and D&D5e actors; honor license |
| [Archives of Nethys (PF2e)](https://2e.aonprd.com/Monsters.aspx) | Rich monster families and powers **for adaptation**; rules not directly compatible |
| [Forgotten Realms Wiki](https://forgottenrealms.fandom.com/wiki/Main_Page) | Secondary D&D history and factions; check cited source editions |
| [The Alexandrian](https://thealexandrian.net/) | Node-based scenario design, mystery structures and faction play |

Do not copy paid/private books into this public repo or paste large copyrighted lore extracts into the catalog.

## Adapting to Magudonya's established story

1. **Preserve canon:** Magudonya/Engelian lore and the player's existing facts outrank any outside podcast interpretation. Official D&D material is inspiration where the world leaves room for it.
2. **No current sci-fi substitutions:** worldbuilding ideas must be adapted to fantasy equivalents. Creatures originating in other worlds may be considered later within the Ion Storm, subject to approval.
3. **Metal-specific phenomenon:** anomalous crystals form on infected **metal** via semi-astral bacteria; the **bacteria**, not crystals alone, perpetuate infection; crystals contain magic and can remain after bacteria are destroyed. No stone infection.
4. **Ecological continuity:** for any creature, define habitat, food, senses, territory, reproductive pressures, local names, signs of activity, community reactions and how it changes day-to-day life.
5. **NPCs as inhabitants:** borrow *techniques* of speech, culture, etiquette, prejudice, hospitality, alliances, livelihoods and disputes without replacing canonical named NPCs or making every encounter a combat.
6. **Good starting hooks:** the Eilistraee forest colony, insectoid Itich community by the abandoned dwarven mine, Veyrun's Reach, the collapsed wall/mountains, and psychic aberrations.

## Maintenance and verification

- [`catalog.json`](catalog.json): machine-readable source list, classifications, priorities, inspiration notes, all reading sources.
- [`generate_feed.py`](generate_feed.py): resolves original publishers' RSS (plus the original Apple directory feed URL where needed), filters real episodes, rejects invalid HTTP or zero-length audio.
- [`status.json`](status.json): published counts, skipped sources and warnings — generated by the builder.
- [GitHub Actions workflow](../.github/workflows/update-magudonya-feed.yml): scheduled weekly Monday rebuild and manual dispatch, independent of other collections.
- Generator requires **three verified publisher feeds and at least 15 real episodes** before replacing the collection. Partial missing sources are reported, never invented. The builder regenerates and validates RSS XML and podcast artwork before committing.
- Original show copyrights and credits remain with publishers. No audio recording is uploaded, mirrored, transcoded or distributed by this repository. All URLs have canonical public publisher sources.

### Future refinements

Curate explicit episode-level picks, exclude too-chatty/too-rules-heavy shows, add European mythology and folktales, tag per creature/faction, and possibly create a chronological listening playlist. Never present a curated 5e/Pathfinder idea as part of Berrie's original setting without confirmation.

### Additional worldbuilding and creature-behavior research

- [The Monsters Know What They're Doing](https://www.themonstersknow.com/why-these-tactics/) — why a predator hunts, flees, uses an environment and chooses targets; convert assumptions to your own 2014 D&D5e creature data.
- [Sly Flourish — Lazy World Building](https://slyflourish.com/lazy_world_building.html) — techniques for local history, factions, divine traditions and settlements that support real player decisions.
- [A Collection of Unmitigated Pedantry — Resources for World-Builders](https://acoup.blog/resources-for-world-builders/) — realistic farms, food, logistics, cities and armies; especially useful for the day-to-day consequences of an enormous collapsed wall and shifting regional trade routes.
