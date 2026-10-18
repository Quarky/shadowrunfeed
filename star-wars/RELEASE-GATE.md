# Star Wars RSS publication and import audit

As authorized 2026-10-18, the original subscribed `feed-v2.xml` and its alias `feed.xml` now have **140 unique recordings**, including all original 100 GUIDs and source audio identities. The original 100 is backed up as `feed-100-baseline.xml`.

Earlier 61-item learning RSS used only basic RSS/iTunes/Atom tags; later versions inherited unnecessary Libsyn and other source-specific XML elements. Production now uses a minimal RSS 2.0/XML structure, descriptions as plain text and canonical audio MIME types. XML simplification does not guarantee Podbean import; the user must verify in the actual app. Expiring publisher-signed URLs remain a separate unresolved playback risk.

Scheduled feed generation writes staging-only files and does not rewrite live production.

## Previous diagnostic evidence (historical)

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


## Podbean application-import isolation, 2026-10-18

Source and successful [GitHub Actions build](https://github.com/Quarky/shadowrunfeed/actions/runs/39157048034) establish **HTTP XML delivery only**, not Podbean app acceptance. The production 100 was not touched.

These new channel-distinct test copies are derived from the original frozen 100; original GUIDs are preserved and descriptions are normalized/HTML-free. Unknown publisher tags are stripped; M4A enclosure MIME is normalized to `audio/mp4` in the 100 copy. The first three contain only ordinary, unsigned MP3 enclosures.

| Trial | Items | Purpose | URL |
| --- | ---: | --- | --- |
| smoke-1 | 1 | Minimal working enclosure and channel | [podbean-smoke-1.xml](podbean-smoke-1.xml) |
| smoke-10 | 10 | Parser or episode count threshold | [podbean-smoke-10.xml](podbean-smoke-10.xml) |
| unsigned-only | 66 | Strip volatile signed media and M4A; isolate media URL lifetime | [podbean-smoke-stable.xml](podbean-smoke-stable.xml) |
| clean-100 | 100 | Test minimum RSS tag set but retain all original 100 items | [podbean-clean-100.xml](podbean-clean-100.xml) |

At build time, the original 100 feed had 9 enclosures with expired query timestamps (original positions 13, 15, 29, 41, 45, 47, 53, 63, 64), another 19 expiring within 24 hours, and 6 M4A enclosures. These are media reliability blockers but no app-specific error message has been observed.

**Required next decision:** In the Podbean *listener application* use Search → + Add Feed URL with the 1-episode test URL, leaving the existing 100-episode subscription untouched. If even the one-item feed fails, investigate app acceptance of custom/non-publisher curated RSS and CDN host; if it imports, test 10 → 66 → clean 100 to isolate the first failure. Do not replace the user's current feed or claim final success based only on HTTP 200.
