Independent adversarial review of PR #538 at `8e96fdb1be9222428dba513e415bce981244fa9e` found one P3 provenance-wording problem in `_fleet/README.md` lines 497–500.

The sentence saying the kg-microbe archive "was rescanned" follows a statement about the common refresh pins, so it can imply a rescan during the November 4 refresh. This run reused the saved comparison: `kg_microbe_census.json` remains dated 2026-10-10, and the source manifest, census, comparison assets, prefix registry and production pipeline are unchanged. Their source/registry hashes and byte identity were verified.

Clarify that the existing comparison was reused and its source and registry hashes checked. This does not call for a new scan or a methodology change. No duplicate was found; #512 concerns rescan triggers and is a different issue. Re-review the final PR head after the wording fix and CMM deployment follow-up are committed.
