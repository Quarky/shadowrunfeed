# Star Wars FFG and D6 — audience-reviewed actual-play podcast collection

This is a **separate collection** in the existing public [Quarky/shadowrunfeed](../README.md) repository, modeled after the existing [Ravnica catalog + filtered RSS builder](../ravnica/README.md). **Shadowrun and Ravnica were not changed or merged.** `Heroes of the Hydian Way` is deliberately omitted.

## Main Star Wars listening feed — originally supplied Podbean address

**[Original Star Wars RSS with the 20 episodes added first](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/feed-v2.xml)**

This is the original `feed-v2.xml` subscription supplied for Podbean—not the newer separate `learning-feed-v2.xml`. As of 2026-10-18 the original feed contains **130 verified publisher-hosted recordings**:

- **Episodes 1–10:** 5 science-fiction audio dramas alternating with 5 Star Wars actual-play starts, no lore interruptions.
- **Episodes 11–20:** 5 normal lore/story pairs.
- **Episodes 21–70:** The remaining ranked episodes plus 9 previously subscribed sampler recordings not already present.
- **Episodes 71–90:** 10 original science-fiction audio-drama chapters alternated with 10 new themed actual-play performances, featuring dangerous installations, alien experiments and survival.
- **Episodes 91–110:** 10 chapters of Star Wars community-made Old Republic audio drama alternated with 10 actual plays about Sith temples, relics and Force mysteries.
- **Episodes 111–130:** The additional fiction and actual-play bonus block, also alternating dramas and performances.

All original 16 subscriber GUIDs remain present; repeated audio is deduplicated. The new thirty recordings come from **16 distinct actual-play programs**.

[Subscriber feed status](subscriber-status.json) · [Twenty new exact audio picks](bonus-20-episodes.md) · [New selection catalog](bonus-20-catalog.json) · [Full new 30-episode actual-play list](expansion-episodes.md) · [Complete earlier 61-episode themed/ranked core](learning-episodes.md) · [Original 16-episode sampler](sampler-v2.xml) · [Automatic weekly updater](../.github/workflows/update-star-wars-learning.yml).

The old `feed.xml` is also updated as an equivalent feed. The `learning-feed-v2.xml` remains a separate 61-episode listening collection, so neither new nor existing listeners are forced to resubscribe. Separate D6 and individual actual-play RSS remain intact.

The original Podbean URL uses jsDelivr's `@main` branch CDN, which may cache responses for **up to 12 hours** even after GitHub publishes updates. Refreshing inside a podcast app cannot always bypass the CDN cache; the updater checks and requests invalidation when it detects a stale response. <https://github.com/jsdelivr/jsdelivr#caching>

Outside sci-fi audio dramas are clearly marked cross-genre creative inspiration, not Star Wars canon. No publisher recordings or paid audiobooks are redistributed.

## Original-scripted fiction now interleaves the actual plays

The originally subscribed Star Wars RSS has **130 playable episodes**. All former episode identities are retained, including the 16 GUIDs from the first sampler. The special theme-based additions now play as **a story episode followed by its matching real tabletop actual-play episode**, rather than grouping all actual plays together:

- **71–90:** Ten facility, survival, alien-archaeology and dangerous-machine fiction/actual-play pairs; original sci-fi drama from *DERELICT: FATHOM*, *The Orphans*, *Station 151*, and *Among the Stars and Bones*.
- **91–110:** Ten old-Sith and Force-mystery fiction/actual-play pairs. The stories are ten consecutive chapters from *Legacy: A Star Wars Audio Drama*, a creator-performed **unofficial Star Wars fan-fiction series**, not narrated commentary.
- **111–130:** The separately added twenty-episode fiction/actual-play bonus remains untouched and internally alternates stories and actual play.

[Publisher-verified fiction chapters](story-interleave-episodes.md) · [Fiction selection verification](story-interleave-status.json) · [Earlier actual-play selections](expansion-episodes.md) · [Exact current original-subscriber status](subscriber-status.json).

These are original publisher-hosted audio episodes only. Some fiction comes from other science-fiction settings and is **cross-genre inspiration, not Star Wars canon**. The weekly updater regenerates the original `feed-v2.xml` and `feed.xml` URLs and checks their CDN copies.

## Subscribe (Podbean / any RSS-capable player)

**Original subscribed Star Wars FFG/D6 feed (expanded collection):** `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/feed-v2.xml`

This feed has been successfully published with 130 original publisher-hosted recordings; see the [subscriber-specific status](subscriber-status.json). The original `feed.xml` address is an equivalent alias. The 16-episode original discovery sampler is preserved separately at [sampler-v2.xml](sampler-v2.xml).

**Complete Star Wars D6 anthology (publisher-hosted):** `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/d6-feed.xml`

**Individual show collections:**

| Show | Filtered RSS subscription URL | Content policy | Why included |
| --- | --- | --- | --- |
| Force Majeure | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/force-majeure.xml` | Entire Star Wars FFG show | Strong audience reviews, atmospheric Force-and-Destiny stories |
| Dice for Brains | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/dice-for-brains.xml` | Star Wars seasons/episodes only; excludes Genesys | Independent Star Wars RPG community endorsements for use of narrative dice |
| Campaign — The Mynock | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/campaign-mynock.xml` | Star Wars era only, not later Skyjacks | Longstanding strong audience reception, improv and character relationships |
| Redemption Productions | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/redemption.xml` | Published Star Wars actual-play episodes; excludes obvious out-of-character chats | Sound design, narrative editing and interpersonal drama |
| Respect the Crit — Empire's Edge | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/respect-the-crit.xml` | Star Wars **Empire's Edge** only; not Fallout or Call of Cthulhu | Character voices, cinematic production and long-form pacing |
| **Nastygram — Star Wars D6** | `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/nastygram-d6.xml` | **Only** *Empire's End* and *Dreamscapes*; excludes other systems | Imperial-outpost drama and Jedi mysteries using West End Games D6 |
| **Falling Star — Star Wars D6** | [Original Apple archive](https://podcasts.apple.com/us/podcast/falling-star-a-star-wars-d6-rpg-podcast/id847953650) (RSS **unavailable**) | Entire historical D6-only podcast (2014–2016) | Historic D6 reference; NOT a highly rated pick (3.8/5, 13 US ratings) |

In Podbean, use **Search → + Add Feed URL**, or your player's equivalent **Add by RSS URL**. These URLs work **only once their corresponding `.xml` files have been published by the [GitHub workflow](../.github/workflows/update-star-wars-feed.yml)**. Check [live builder status](status.json) (or repository directory) before subscribing. The first run and the CDN may take time; a configured feed is not proof of successful publication.

## Episode picks and ratings: avoid false precision

**The original five FFG series were selected based on overall show-level reviews/recommendations**, *not* because every episode is individually rated highly. Podcast services generally publish show-level stars, not per-episode rating tables. Different regions/platforms give incomparable vote counts. The archived `sampler-v2.xml` is an **editorial discovery sampler**; the active `feed-v2.xml` combines it with the themed and ranked selections. Neither is a verified chart of individually star-rated episodes.

| Show | Highlight / entry point (only included when publisher feed verifies it) | What the evidence actually says |
| --- | --- | --- |
| Force Majeure | An Ally Emerges; A Sense of Foreboding; In Which the Definition of a Heist Is Argued; A Daring Escape | These appeared in a low-engagement episode discovery list. This is **not** compelling statistical episode-review evidence. |
| Dice for Brains | Season 1 episode 10, *Mirages* | Specifically mentioned by a GM in a FFG forum discussion as a meaningful character/player moment; **not** a star-rated winner. |
| Campaign: The Mynock | *Episode One* | Recommended starting point. Show reviews also include the later, unrelated Skyjacks arc. |
| Redemption | *Just Another Rock in the Wall*; *Rough Times* | *Just Another Rock in the Wall* has documented individual Podchaser reviews; small sample. *Rough Times* is a season entry point, not peer-ranked. |
| Respect the Crit | *Empire's Edge* episodes 01, 46, 79 | Introduction and later arc choices; not demonstrably the top three most-rated episodes. |
| **Nastygram D6** | *Empire's End 1: Flash Traffic*; *Dreamscapes 1: Field of View*; *Empire's End 25: For the Empire*; *Dreamscapes 8: Synchronous* | Two verified D6 story arcs and editorial beginning/finale picks, **not** episode-rated winners. |
| **Falling Star D6** | Apple Podcasts' historical archive only | RSS returns **410 Gone** (checked 2026-10-11). No fabricated or copied audio in these feeds. |

The sampler uses the listed highlights when uniquely resolved in the original RSS; otherwise it uses the earliest available episodes from that *show's original current feed*. Before publication the generator checks the combined feed's audio URLs, obtains real content lengths from publisher servers when the original RSS specifies zero, and **omits any unverifiable items**. No MP3 sizes or URLs are invented. Missing or non-playable items are never fabricated. The sampler carries **original 2000×2000 PNG cover artwork** generated by [`generate_cover.py`](generate_cover.py).

### Independent community praise versus actual episode ratings

- **Most repeatedly recommended show-level choices:** *Dice for Brains* and *Campaign: The Mynock* across independent Reddit [2020 GM recommendations](https://www.reddit.com/r/swrpg/comments/iyuxld/), [2021 favorites](https://www.reddit.com/r/swrpg/comments/mupk30/), [2024 suggestions](https://www.reddit.com/r/swrpg/comments/1b68bgt/), and [2026 current recommendations](https://www.reddit.com/r/swrpg/comments/1tw83p4/). These are separate discussions, **not** quantitative popularity totals.
- **Actual episode-review evidence:** *Redemption — S03E05: Just Another Rock in the Wall* had [6 individual Podchaser ratings and 3 reviews](https://www.podchaser.com/podcasts/redemption-podcast-425872/episodes/episode-s03e05-just-another-ro-17023346/reviews/990) at research time. Too small a sample for a definitive #1 ranking.
- **D6 peer/community evidence:** [Nastygram *Empire's End* discussion](https://www.reddit.com/r/StarWarsD6/comments/rjkj5u/) and [follow-up](https://www.reddit.com/r/StarWarsD6/comments/t96t00/) confirm the D6 campaign, with limited independent feedback. Its **5.0/5 from 72 US Apple ratings** applies to all Nastygram RPG campaigns combined, not its Star Wars episodes.
- **Lower-rated historical D6 choice:** *Falling Star* has [3.8/5 from 13 US Apple ratings](https://podcasts.apple.com/us/podcast/falling-star-a-star-wars-d6-rpg-podcast/id847953650), with some positive written reviews. It is cataloged for breadth even though its RSS is gone.
- **X/Twitter:** Publicly accessible indexed posts did **not** establish reliable episode mention counts. No X popularity ranking is claimed. No episode inherits its parent show's star rating.


## Original sources and review context

- [Force Majeure publisher](https://forcemajeurepod.libsyn.com/); [Apple reviews](https://podcasts.apple.com/us/podcast/force-majeure-a-star-wars-actual-play-podcast/id1337284202).
- [Dice for Brains publisher](https://diceforbrains.com/d4bp/); [original SWRPG episode 10 discussion](https://ffg-forum-archive.entropicdreams.com/topic/201784-actual-play-dice-for-brains-podcast-episode-10/).
- [Campaign: The Mynock publisher archive](https://oneshotpodcast.com/actual-play/campaign/the-characters/); [Apple series reviews](https://podcasts.apple.com/us/podcast/campaign-skyjacks/id927205926).
- [Redemption Apple series reviews](https://podcasts.apple.com/us/podcast/redemption-productions/id1052623023); [publisher](https://www.redemptionpodcast.com/).
- [Respect the Crit Apple series reviews](https://podcasts.apple.com/us/podcast/respect-the-crit/id1489211492); [Empire's Edge episode listing](https://podcasts.apple.com/us/podcast/empires-edge-ep-79-back-to-black-spire/id1489211492?i=1000643662927).
- [Nastygram Apple ratings](https://podcasts.apple.com/us/podcast/nastygram-an-rpg-podcast/id1565416693); [D6 *Dreamscapes* episode](https://nastygram.libsyn.com/star-wars-dreamscapes-ep-5-decrypt-star-wars-d6).
- [Falling Star Apple archive](https://podcasts.apple.com/us/podcast/falling-star-a-star-wars-d6-rpg-podcast/id847953650); its current Podbean RSS endpoint responded 410 Gone during publisher-feed verification.

## Maintenance, traceability and copyright

- [`catalog.json`](catalog.json): publisher URLs/Apple podcast IDs, rationale, explicit Star Wars filters, editorial highlights.
- [`generate_feed.py`](generate_feed.py): regenerates each filtered feed and combined sampler from original, publicly reachable RSS. Corrects combined feed's invalid enclosure lengths, uses HTTPS media, and includes original artwork. For Apple-only sources, the publisher feed URL is resolved from the public iTunes Lookup endpoint at build time instead of inventing an enclosure location.
- [`status.json`](status.json): written on a successful builder run; documents which shows published, how many selected episodes, skipped invalid sampler items, and failures.
- [Automated weekly update workflow](../.github/workflows/update-star-wars-feed.yml): runs independently of existing updates and commits valid RSS files.

If a publisher omits their old recordings from RSS, the builder does **not** invent or scrape MP3 locations. That show's XML is kept unchanged if previously published, and the current status report marks it unavailable. Star Wars material from a mixed-genre podcast is restricted by exact era/title matching and may not cover every historical episode if the publisher RSS is truncated.

**No MP3/audio is uploaded or rehosted here.** Episodes play via the original publishers' enclosure URLs. Reviews are metadata/context, not an endorsement from any podcaster. Cover art, if present in a source feed, remains hosted by the publisher. All featured creators are unaffiliated with this independent listening index.
