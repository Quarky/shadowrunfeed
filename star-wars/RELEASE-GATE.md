# Star Wars RSS — production release gate

**Production:** `feed-v2.xml`, `feed.xml` and `subscriber-status.json` are frozen to the exact original 100 recordings (source commit `f4d59327b8`). Never let scheduled builders replace them.

**Staging:** `feed-130-debug.xml` preserves the failed candidate for debugging. `feed-140-candidate.xml` holds all original 100 + 40 audio-distinct recordings with original GUIDs unchanged. Status files explicitly say staging.

**Promotion is forbidden** until RSS XML and GUID validation, audio URL and MIME checks, source-host reachability including signed URL expirations, end-to-end CDN serving of the test copy, a successful test-only Podbean import, and explicit user approval. A GitHub action success does not count as podcast import success.

Known failure: jsDelivr `@main` original URL continued serving 100 while GitHub had 130; other CDN hosts served 130. The 130 generated version silently changed previously published episode GUIDs and duplicated 20 previously present audio recordings under different GUIDs. Current production 100 may also have expiring signed publisher URLs; validate, do not assume audio will play forever. Never rehost publisher recordings.
