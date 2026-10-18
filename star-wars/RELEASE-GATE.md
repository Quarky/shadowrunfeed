# Star Wars RSS — production release gate

**Production:** `feed-v2.xml`, `feed.xml` and `subscriber-status.json` are frozen to the exact original 100 recordings (source commit `f4d59327b8`). Never let scheduled builders replace them.

**Staging:** `feed-130-debug.xml` preserves the failed candidate for debugging. `feed-140-candidate.xml` holds all original 100 + 40 audio-distinct recordings with original GUIDs unchanged. Status files explicitly say staging.

**Promotion is forbidden** until RSS XML and GUID validation, audio URL and MIME checks, source-host reachability including signed URL expirations, end-to-end CDN serving of the test copy, a successful test-only Podbean import, and explicit user approval. A GitHub action success does not count as podcast import success.

Known failure: jsDelivr `@main` original URL continued serving 100 while GitHub had 130; other CDN hosts served 130. The 130 generated version silently changed previously published episode GUIDs and duplicated 20 previously present audio recordings under different GUIDs. Current production 100 may also have expiring signed publisher URLs; validate, do not assume audio will play forever. Never rehost publisher recordings.

## Staging probe results (2026-10-18, GitHub Actions)
Run: https://github.com/Quarky/shadowrunfeed/actions/runs/39156360040

- The exact live production URL served **100**, the isolated unreconciled debug URL served **130**, and the isolated deduplicated candidate URL served **140**. All three returned HTTP 200, RSS 2.0 XML and matching expected episode counts.
- All 40 novel candidate audio enclosures returned HTTP 200 to a HEAD request; this **does not prove playback or Podbean import**.
- Three publishers using Acast returned `text/plain` despite HTTP 200 in their HEAD responses: candidate items 123 (*The Silt Verses*), 125 (*Old Gods of Appalachia*), and 140 (*Ain't Slayed Nobody*). They require a bounded GET/content signature test before acceptance; HEAD alone may be misleading.
- At probe time, **7 original production enclosures had already expired timestamps** (positions 13, 15, 41, 47, 53, 63, 64), and 21 other production enclosures expired within 24 hours. Candidate totals: 7 expired, another 35 due within 24 hours. A signed URL expiry does not conclusively prove HTTP rejection, but demonstrates an unmaintainable long-term RSS recording URL.
- No live Podbean import has been completed or observed. **Promotion remains blocked**.

