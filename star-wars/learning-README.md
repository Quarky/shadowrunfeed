# Star Wars RPG — Ranked Listening with Featured Story Opening

**Original Podbean subscription:** [Star Wars combined RSS — feed-v2.xml](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/feed-v2.xml). This is the address first supplied to existing listeners; it now starts with the 20 special episodes, followed by the ranked collection and all original subscriber recordings. It contains **100 unique publisher-hosted recordings**, with all original 16 podcast GUIDs preserved. See the [subscriber publication status](subscriber-status.json).

## New actual-play selections (episodes 71–100)

The original subscribed RSS now adds [thirty new recorded actual plays](expansion-episodes.md) **after** the existing 70 episodes, without duplicating earlier publisher audio.

- **71–90: Remote facility and sci-fi survival.** Twenty new performances from Mothership, Alien RPG, and Star Wars FFG campaigns, exploring industrial science, abandoned structures, androids, containment, environmental threats, hostile fauna, and expedition decisions.
- **91–100: Ancient Sith ruins and Force mysteries.** Ten Star Wars tabletop actual-play sessions on dark-side relics, tombs, Force traditions, and competing motives, including Old Republic adventures and Saga Edition.
- The new thirty episodes represent **16 different shows**, including sources not used in the earlier collection. The two themed groups are curated for specific creative inspiration, not a claim that every episode takes place at those exact locations.

[View the 30-episode playlist](expansion-episodes.md) · [Source-specific details and systems](expansion-episodes.json) · [Verified source status](expansion-status.json). Some selections begin in an established arc and are marked as such. Non-Star-Wars actual plays are explicitly labeled as cross-genre references.


## Additional themed listening (episodes 71–110 of the original Podbean feed)

The original subscriber queue now retains the earlier **20 thematic actual plays** (71–80 remote research and survival; 81–90 Sith-tomb mysteries). Following those, **20 more unique audio recordings** use a deliberately different format mix: **91–100 Moraband-style** ancient magic, secret societies and ruins (five scripted audio dramas / five tabletop actual plays) and **101–110 Shard Moon-style** ancient laboratories, experimental facilities and survival (five dramas / five actual plays). All twenty new shows are different productions, with no reused recordings and no cross-genre episode misrepresented as Star Wars canon. See the [source-verified, playable additions](bonus-20-episodes.md) and [publication status](bonus-20-status.json).

## Alternative curated-only RSS

**[Standalone 61-episode ranked Star Wars RSS](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/learning-feed-v2.xml)** remains available for those already following that second address. It has the same 20-track opening, followed by 41 unique remaining ranked selections; it omits nine historical subscriber-sampler extras.

The first 20 entries have a deliberate two-phase order:

- **1–10:** Five full-cast/sound-designed science-fiction drama pilot episodes alternating with five distinct Star Wars FFG/D6 actual-play campaign openings. There are no lore interruptions here.
- **11–20:** Five conventional Star Wars lore → story pairs from the original ranked feed, maintaining consecutive chapters of a story campaign.
- **21 onward:** The remaining unique episodes from the previous ranked library. Original subscriber GUIDs remain unchanged, and previously featured episodes are not repeated. Additional lore-only entries at the end retain subjects whose story partner was moved to the start.

The original Podbean feed contains **100 episodes**: the 61-episode curated playlist, 9 unique historical subscriber extras, and 30 newly verified actual plays. The new episodes occupy positions 71–100. The 61-episode ranked-only address remains separately available. The automatic publisher rebuild updates both addresses every week, and retains all existing podcast GUIDs.

[Full current combined episode list](learning-episodes.md) · [Validation/status](learning-status.json) · [Merged playlist JSON](learning-episodes.json)

For reference, the original 56-episode ranked content is preserved independently as [the lore/story base](learning-base-episodes.md) and [base RSS](learning-base-v2.xml). The [separate 20-episode sampler](frontier-mix.xml), [its notes](frontier-mix-episodes.md), [source selections](frontier-mix-catalog.json), [lore-only RSS](learning-lore.xml) and [story-only RSS](learning-story.xml) are still available, but require no new subscription if you already follow the main URL.

All dramatized non-Star-Wars shows are labeled **cross-genre inspiration**, not Star Wars canon. Paid official full-cast audiobook recommendations are publisher/store links in the separate sampler notes, never copied into RSS. No episode audio is rehosted.

## Automatic updates

The [unified weekly GitHub Actions workflow](../.github/workflows/update-star-wars-learning.yml) rebuilds the normal lore/story base, adds the 20-episode featured sequence, then publishes both the 61-item ranked playlist and the expanded 70-item original Podbean `feed-v2.xml` subscription. It explicitly preserves the original 16 GUIDs, checks publisher audio and de-duplicates overlapping titles. The older source-feed builder updates the separately archived sampler rather than overwriting the subscribed URL. The original 16-episode discovery sampler is archived as [sampler-v2.xml](sampler-v2.xml); D6 and individual source collections remain untouched.

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
- [`generate_learning.py`](generate_learning.py) — validates publisher-hosted episodes and produces the independent original lore/story base.
- [`generate_frontier_mix.py`](generate_frontier_mix.py) — appends the special to the top of the original subscribed feed, deduplicates audio, and preserves existing episode identities.
- [`learning-episodes.md`](learning-episodes.md) and [`learning-episodes.json`](learning-episodes.json) — generated exact episode sequence with ranking rationale.
- [`learning-status.json`](learning-status.json) — generated coverage and missing sources; an unavailable source is not represented as published.
- [GitHub Actions updater](../.github/workflows/update-star-wars-learning.yml) — independent build, runs weekly and on source/script updates.

All existing podcast feed identities and downloadable recordings stay with their original publishers.
