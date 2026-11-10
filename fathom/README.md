# DERELICT story-only podcast subscriptions

The [DERELICT](https://www.derelictpodcast.com/) audio drama begins with
**FATHOM (Season 1)** and continues with **DERELICT (Season 2)**.

Both seasons have ten numbered story chapters. This independent listening index
excludes trailers, crowd-funding updates, advertisements-as-episodes, interviews,
and the separate "DERELICT Presents" recommendations. The audio is always
streamed from the original publisher, Night Rocket Productions.

## Subscribe

- **[Complete FATHOM + DERELICT — 20 episodes](feed.xml)** (original existing
  subscriber URL, extended without changing the season-one episode GUIDs):
  `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fathom/feed.xml`
- **[FATHOM Season 1 only — 10 episodes](season1.xml)**:
  `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/fathom/season1.xml`

Paste the CDN URL into **Podbean → Search → + Add Feed URL**, or the custom RSS
URL feature of another podcast player. The stories are listed in narrative order.

The checked-in [generator](build_feed.py) retrieves the publisher's
[official RSS](https://feeds.megaphone.fm/SBP4341397353), verifies that all
twenty numbered chapters are present with unique GUIDs and HTTPS enclosures,
and emits both RSS versions. [Status](status.json) lists the selected episodes.
GitHub Actions refreshes weekly (and when the generator changes); a source or
validation failure leaves the last published feed unchanged.
