# Star Wars FFG and D6 — audience-reviewed actual-play podcast collection

This is a **separate collection** in the existing public [Quarky/shadowrunfeed](../README.md) repository, modeled after the existing [Ravnica catalog + filtered RSS builder](../ravnica/README.md). **Shadowrun and Ravnica were not changed or merged.** `Heroes of the Hydian Way` is deliberately omitted.

## Ranked lore and story listening queue

**New:** [Star Wars RPG Lore → Story — ranking, ratings and learning episodes](learning-README.md) combines original-publisher Star Wars lore explainers with continuous FFG/D6 actual-play story chapters.

- **[Ranked 1:1 lore/story RSS](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/learning-feed-v2.xml)** — alternating learning order (after successful builder publication).
- [Full verified episode list](learning-episodes.md) · [Live build status](learning-status.json) · [Independent updater](../.github/workflows/update-star-wars-learning.yml).
- Also publishes [lore-only RSS](learning-lore.xml) and [story-only RSS](learning-story.xml).

This is a separate listening feed: the older 16-item discovery sampler, complete D6 archive and each filtered actual-play show remain available at their original addresses.

## Scene-first drama, live play and lore follow-up (20 episodes)

A **separate verified 20-track RSS** now provides five independent full-cast/sound-designed science-fiction drama pilot episodes alternating with five Star Wars RPG actual-play openings, then five normal lore/story pairs. The first ten **do not alternate with lore**; the last ten preserve a five-chapter story arc.

- **[Subscribe to the 20-episode RSS](https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/frontier-mix.xml)**
- [Full ordered episode list, creative uses and legitimate commercial audiobook links](frontier-mix-episodes.md)
- [Automated verification status](frontier-mix-status.json) · [Source selection and policy](frontier-mix-catalog.json)

The independent fiction productions are marked **cross-genre inspiration rather than Star Wars canon**. Their original publisher-hosted audio is linked, never copied. Commercial Star Wars audiobooks are included only as purchase/library references, not RSS audio. The older general learning and actual-play feeds are unchanged.

## Subscribe (Podbean / any RSS-capable player)

**Podbean-compatible combined sampler (FFG + D6):** `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/star-wars/feed-v2.xml`

The earlier `feed.xml` URL remains an alias after publication, but `feed-v2.xml` is recommended for a fresh subscription because it avoids prior CDN/app caching of the incomplete feed. **Do not subscribe until `feed-v2.xml` exists and the [status report](status.json) confirms it was built.**

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

**The original five FFG series were selected based on overall show-level reviews/recommendations**, *not* because every episode is individually rated highly. Podcast services generally publish show-level stars, not per-episode rating tables. Different regions/platforms give incomparable vote counts. The combined `feed-v2.xml` is an **editorial discovery sampler**; it is not advertised as a verified ranking of the highest-rated individual episodes.

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
