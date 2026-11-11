# LANCER | At the Table — actual plays and combat

This is a separate, curated audio-only podcast subscription, specifically for listeners who want to hear **Lancer played at a real table**: rolls, mechanical choices, combat tactics, imperfect but real table conversation, and the ways GMs adjudicate the rules. It does **not** rehost or modify creators' sound recordings.

**Subscribe:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/feed.xml

## Selection

- **CCRPG (Compelling Compiling):** strongest match for natural, low-frills tabletop play. All matched Lancer Gig, Lancer Ruse and Lancer War campaign episodes are selected in chronological order.
- **Role Playing Public Radio — Lancer:** all three complete, long-form Lancer recordings, including Solstice Rain Parts 1–2 and The Siege of Vermeer.
- **House of Bob — Vertigo:** the 16-part, LL0-starting Long Rim campaign. More polish and sound design; a secondary choice. The generator includes its audio only if a positive original media byte count is verified.
- **Roll for Distraction — The Lost Colony and Fractured Republic:** seasons C3 (11 parts) and C8 (10 parts). Lively organic friends-at-the-table play, but shorter edited episodes and more comedic distraction; secondary choice.

These are episode-level selections based on original producer RSS catalogs and community testimony, **not a claim to have listened to every hour or checked every rules ruling**. Particularly, no guarantee that any table's play is rules-perfect.

## Listening order (gameplay first)

**Primary existing subscription:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/feed.xml

**Identical gameplay-first subscription on a new CDN path (use if existing branch alias remains stale):** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/gameplay-first.xml

**Alternative, campaign-order subscription:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/story-order.xml

The primary feed ranks individual episodes **descending by evidence of brisk, active tabletop play**, including tactical combat, frequent action resolution and rolls, actionable scenes and genuine in-character decisions. It de-prioritizes lengthy introductions, briefing, session prep, slow rules debates and epilogues. A dramatic synopsis about combat does NOT establish that an episode actually plays fast. All 193 original selected episodes remain; original source MP3s and item GUIDs stay unchanged.

### First transcript-checked pacing correction — 11 November 2026

A listener reported that **RPPR — Solstice Rain, Part 2** (previously incorrectly ranked #1 at 98/100) felt dominated by narrative and slow play. Its creator-posted [YouTube recording](https://www.youtube.com/watch?v=yK0uo27LC94) has a complete, automatically generated English caption track. Ten-minute caption samples across the three-hour-plus recording show that the first approximately 35–40 minutes are upgrades, introductions, reserves and briefing. Long tactical encounters follow, but movement/range deliberation and rules discussion are extensive; the ending has postgame commentary. It is **not** a fast-start, roll-forward recommendation. The editorial fast-play fit was reduced to **50/100**; this is a preference/pacing rating and **not** a claim that only 50% is active play.

For comparison, the creator-posted [CCRPG — Lancer Gig, Episode 8](https://www.youtube.com/watch?v=L0HgTahkkV4) has timed English auto-captions and begins in the middle of live mech combat within the opening minute. Much of its two-hour recording is actions, tactical decisions and rolls, with a narrative resolution near the end. Its editorial fast-play fit is **84/100** and is preferred as the new opener. This **does not** mean 84% of the episode is measured playtime.

I also examined the creator's timed auto-captions for [CCRPG — Lancer Gig, Episode 14](https://www.youtube.com/watch?v=EB0IEXNNXUo). Following a roughly 15–20-minute initial investigation, most of this recording is a continuing tactical encounter with turns, attack rolls, damage and heat. Its **81/100** editorial pacing score ranks below the immediate-action Episode 8, but ahead of metadata-only guesses.

The source files `lancer/reviewed-episode-evidence.json` and `lancer/ranking.py` record derived time segments, transcript sources, listener feedback and versioned ranking decisions. No creator transcript or audio is mirrored. **Three of 193 episodes have caption-based pacing reviews so far.** The remaining 190 episodes have provisional scores capped at 79/100, specifically to prevent dramatic publisher descriptions from outranking verified pacing evidence.

**Important measurement limit:** the displayed **FAST-PLAY FIT INDEX /100** is an *editorial suitability index*, **NOT a measured percentage of a recording devoted to gameplay**. Three complete YouTube auto-caption timelines were located and sampled; the remaining 190 recordings have not received a timed-content review. Most publishers provide no official timed transcript. Presenting a precise actual-play percentage would be misleading. Each episode records its evidence method and confidence; the generator stores the 20 top-ranked items and both checked-video assessments in `status.json`. Exact runtime percentages should only be added after timed audio/complete-transcript analysis.

The **campaign-order** alternative preserves the previous two-episodes-per-source interleaving with all individual series in episode sequence. This is better if you want to follow developing characters and story without spoilers.

The main feed uses deterministic, score-oriented RSS publication date markers so podcast apps sort strongest gameplay matches at the top, rather than switching back to historical publisher release dates. The original publisher dates remain in descriptions, and GUIDs are unchanged across both feeds.

### Watch-only recommendations, not copied into audio RSS

- **Arcane Arcade: Lancer — Daybreak**: natural home-game feel, mostly first-party combat rules. Earlier episodes contain some rules errors; later episodes are stronger mechanically. Official video channel: https://www.youtube.com/results?search_query=Arcane+Arcade+Lancer+Daybreak
- **Interpoint Station**: many tactical live Lancer games (typically video first). https://www.youtube.com/results?search_query=Interpoint+Station+Lancer
- **No Home in Twilight**: interesting encounter design, but notable homebrew setting, mechanical changes and higher VTT production. https://www.youtube.com/results?search_query=No+Home+in+Twilight+Lancer

These are video recommendations only until the publishers provide independently verifiable podcast audio enclosures; no video audio is ripped or re-published.

## Technical / source handling

Generator: \`lancer/build_feed.py\` with \`lancer/ranking.py\`. All input sources are the publisher's official RSS. Only original HTTPS audio with verified positive byte length is included; invalid/missing publisher enclosures are rejected, never invented. Both sort modes are rebuilt from the same validated source inventory. The source name, original title and original release date remain in episode metadata. No existing podcast subscription or source feed is replaced.

Rebuild workflow: \`.github/workflows/update-lancer-feed.yml\`; source-update failures fail closed and leave the last published feed untouched. \`status.json\` gives source counts, exclusions and XML digest. Git commit, CDN availability and successful Podbean import/playback must be verified separately.


### CDN cache verification

The existing `@main/lancer/feed.xml` path may temporarily serve an older ranking after GitHub succeeds, despite successful purge responses. The additional `gameplay-first.xml` path contains the same item GUIDs, source audio, ranking and updated weekly build, but has its own fresh CDN cache key. Confirm public URL bytes before claiming each subscription path current. A commit-pinned CDN URL is immutable, only suitable as a temporary audit copy.
