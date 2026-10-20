# Anomaly publisher-candidate validation (non-publishing)

**Owner:** Quarky/shadowrunfeed, Anomaly podcast curation.  
**Trigger:** Source changes or manual dispatch of `.github/workflows/anomaly-candidate-audit.yml`.  
**Scope:** Reads public publisher RSS feeds, writes a *non-subscribable* evidence file `anomaly/replacement-candidates.json`. It never changes feed-v2.xml, the selection lock, or published episode GUIDs.

**Local reproducer:** `python3 -u anomaly/replacement_candidates.py` (Python 3.11+, no dependencies). Requires outbound HTTPS from publisher feeds. Expected: "Candidate counts" with populated story and actual-play entries. A network outage prints each source error and fails when no balanced theme set has candidates.

**Failure diagnostics:** Failed source URL, 403/404/timeout/parse error are printed under the exact source ID. No audio is downloaded. Failing this discovery is not a blocking RSS release test.

**Evidence before workflow enablement:** generator source and existing publisher RSS paths are inspected. Python execution in the present agent container is blocked by DNS; GitHub-hosted runner is required for live publisher checks. A runner PASS is required before this discovery is trusted.

**Rollback:** Remove this audit workflow and candidate JSON; the published RSS remains unaffected. No unrelated workflow or repo-wide gating.
