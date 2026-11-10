# LANCER | At the Table — actual plays and combat

This is a separate, curated audio-only podcast subscription, specifically for listeners who want to hear **Lancer played at a real table**: rolls, mechanical choices, combat tactics, imperfect but real table conversation, and the ways GMs adjudicate the rules. It does **not** rehost or modify creators' sound recordings.

**Subscribe:** https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/lancer/feed.xml

## Selection

- **CCRPG (Compelling Compiling):** strongest match for natural, low-frills tabletop play. All matched Lancer Gig, Lancer Ruse and Lancer War campaign episodes are selected in chronological order.
- **Role Playing Public Radio — Lancer:** all three complete, long-form Lancer recordings, including Solstice Rain Parts 1–2 and The Siege of Vermeer.
- **House of Bob — Vertigo:** the 16-part, LL0-starting Long Rim campaign. More polish and sound design; a secondary choice. The generator includes its audio only if a positive original media byte count is verified.
- **Roll for Distraction — The Lost Colony and Fractured Republic:** seasons C3 (11 parts) and C8 (10 parts). Lively organic friends-at-the-table play, but shorter edited episodes and more comedic distraction; secondary choice.

These are episode-level selections based on original producer RSS catalogs and community testimony, **not a claim to have listened to every hour or checked every rules ruling**. Particularly, no guarantee that any table's play is rules-perfect.

The playlist interleaves **two consecutive episodes at a time** from each series while keeping episodes chronological *within* each series. CCRPG continues when the shorter finished runs end. A playlist-order marker is used as the RSS pubDate so podcatchers do not re-sort different shows by unrelated historical dates; every episode description states its actual original publication date. Existing episode GUIDs in this curated feed remain deterministic across refreshes.

### Watch-only recommendations, not copied into audio RSS

- **Arcane Arcade: Lancer — Daybreak**: natural home-game feel, mostly first-party combat rules. Earlier episodes contain some rules errors; later episodes are stronger mechanically. Official video channel: https://www.youtube.com/results?search_query=Arcane+Arcade+Lancer+Daybreak
- **Interpoint Station**: many tactical live Lancer games (typically video first). https://www.youtube.com/results?search_query=Interpoint+Station+Lancer
- **No Home in Twilight**: interesting encounter design, but notable homebrew setting, mechanical changes and higher VTT production. https://www.youtube.com/results?search_query=No+Home+in+Twilight+Lancer

These are video recommendations only until the publishers provide independently verifiable podcast audio enclosures; no video audio is ripped or re-published.

## Technical / source handling

Generator: \`lancer/build_feed.py\`. All input sources are the publisher's official RSS. Only original HTTPS audio with verified positive byte length is included; invalid/missing publisher enclosures are rejected, never invented. The source name, original title and original release date remain in episode metadata. No existing podcast subscription or source feed is replaced.

Rebuild workflow: \`.github/workflows/update-lancer-feed.yml\`; source-update failures fail closed and leave the last published feed untouched. \`status.json\` gives source counts, exclusions and XML digest. Git commit, CDN availability and successful Podbean import/playback must be verified separately.
