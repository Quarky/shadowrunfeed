# Ravnica audio fiction — curated podcast and audiobook list

Companion to [Shadowrun — Renraku Arcology Shutdown Audio Collection](../README.md), in the same GitHub repository. **The original Shadowrun feeds are unchanged.**

## Podcast subscription

- **Unspoken Realms, Ravnica-only curated RSS:** `https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/ravnica/feed.xml` (available **after** the feed-builder GitHub Action successfully publishes `ravnica/feed.xml`).
- **Original podcast feed:** https://feeds.libsyn.com/70890/rss
- **Publisher's listening site:** https://unspokenrealms.wordpress.com/

The Ravnica feed uses the Unspoken Realms publisher's existing audio enclosures and credits, not copied MP3s. The `ravnica/generate_feed.py` script checks every selection before writing; if the publisher feed omits older entries, the script fails rather than publishing a misleading incomplete feed. For podcast apps, choose **Add by RSS URL** and paste the curated RSS address *only after* `ravnica/feed.xml` exists.

## Official audiobooks — licensed commercial editions

| Title | Author | Length | Official publisher |
|---|---|---|---|
| **War of the Spark: Ravnica** | Greg Weisman | 10h 16m | [Penguin Random House — audiobook (2019-04-23)](https://www.penguinrandomhouse.com/books/595014/war-of-the-spark-ravnica-magic-the-gathering-by-greg-weisman/audio/) |
| **War of the Spark: Forsaken** | Greg Weisman | 10h 47m | [Penguin Random House — audiobook (2019-11-12)](https://www.penguinrandomhouse.com/books/595015/war-of-the-spark-forsaken-magic-the-gathering-by-greg-weisman/audio/) |

These are **official audiobooks**, not free podcast episodes. They are cataloged with listening/purchase links only. No paid audiobook content is redistributed.

## Unspoken Realms — curated Ravnica stories

Listen in roughly setting chronology below (within the series, ascending episode/story number). All feed episode names and audio locations are resolved from the **publisher RSS** rather than guessed MP3 URLs. Publisher: [Unspoken Realms](https://unspokenrealms.wordpress.com/).

### Return to Ravnica stories

| Unspoken Realms episode | Recording |
|---|---|
| #145 | RTR#1 — The Shadows of Prahv |
| #158 | RTR#2 — Epic Experiment & Slaughter Games |
| #159 | RTR#3 — In Praise of the Worldsoul |
| #172 | RTR#4 — The Great Concourse |
| #176 | RTR#5 — The Seven Bells |
| #179 | RTR#6 — Rogue’s Passage |

### Gatecrash stories

| Unspoken Realms episode | Recording |
|---|---|
| #183 | GTC#1 — Gruul Ingenuity & The Fathom Edict |
| #187 | GTC#2 — The Absolution of the Guildpact & Persistence of Memory |
| #188 | GTC#3 — The Greater Good |
| #189 | GTC#4 — The Burying |

### Guilds of Ravnica stories

| Unspoken Realms episode | Recording |
|---|---|
| Special (unnumbered) | GRN#1 — Under the Cover of Fog |

### Ravnica Allegiance stories

| Unspoken Realms episode | Recording |
|---|---|
| #190 | RNA#1 — The Illusions of Child’s Play |
| #191 | RNA#2 — Rage of the Unsung |
| #192 | RNA#3 — The Principles of Unnatural Selection |
| #193 | RNA#4 — The Ledger of Hidden Fortunes |
| #194 | RNA#5 — The Ascension of Reza |

### The Gathering Storm (Django Wexler)

| Unspoken Realms episode | Recording |
|---|---|
| #201 | The Gathering Storm — Chapter 1 |
| #202 | The Gathering Storm — Chapter 2 |
| #203 | The Gathering Storm — Chapter 3 |
| #204 | The Gathering Storm — Chapter 4 |
| #205 | The Gathering Storm — Chapter 5 |
| #206 | The Gathering Storm — Chapter 6 |
| #207 | The Gathering Storm — Chapter 7 |
| #208 | The Gathering Storm — Chapter 8 |
| #209 | The Gathering Storm — Chapter 9 |
| #210 | The Gathering Storm — Chapter 10 |
| #211 | The Gathering Storm — Chapter 11 |
| #212 | The Gathering Storm — Chapter 12 |
| #213 | The Gathering Storm — Chapter 13 |
| #214 | The Gathering Storm — Chapter 14 |
| #215 | The Gathering Storm — Chapter 15 |
| #216 | The Gathering Storm — Chapter 16 |
| #217 | The Gathering Storm — Chapter 17 |
| #218 | The Gathering Storm — Chapter 18 |
| #219 | The Gathering Storm — Chapter 19 |
| #220 | The Gathering Storm — Chapter 20 |

## Important corrections and coverage notes

- The initially supplied mapping **161–165 = Guilds of Ravnica** is incorrect: these are part of **Return to Dominaria**. The proposed **168–172 = Ravnica Allegiance** is also incorrect: 168–171 are Dominaria, and **172 is Return to Ravnica: The Great Concourse**. The verified *Ravnica Allegiance* recordings are **190–194**.
- Of the five *Guilds of Ravnica* web stories, **only GRN#1, Under the Cover of Fog** has been verified in *Unspoken Realms* (a special episode read by Carolyn Page). **Do not present GRN#2–#5 as existing in this feed.**
- The earlier *Return to Ravnica* material spans episodes **145, 158, 159, 172, 176, 179**, with *Gatecrash* follow-up stories in **183, 187, 188, 189**. This is **not** a claim that *The Secretist* novels have been recorded in full.
- The 20 chapters of *The Gathering Storm* are **201–220**, authored by Django Wexler and narrated by the podcast. These prequel stories precede the *War of the Spark* climax.
- **Optional additional Ravnica-era audio** not included in this narrowly requested list: the six *War of the Spark* web-fiction recordings at **195–200**, overlapping the novel's events from a different perspective.

## Maintenance

- Machine-readable selection, source links and credits: [`catalog.json`](catalog.json).
- Feed generation: [`generate_feed.py`](generate_feed.py).
- Automated workflow: [Update Ravnica filtered RSS](../.github/workflows/update-ravnica-feed.yml).
- Filter is strict: all 36 selected recordings and enclosures are required before a feed can be published; paid audiobooks are excluded.
- Only add a missing *Guilds of Ravnica* adaptation if a legitimate original publisher source and playback enclosure have been verified.
