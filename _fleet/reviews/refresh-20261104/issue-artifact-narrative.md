The November 4 pre-PR diff review found that the refreshed manifest correctly contains `artifact_count: 26`, but the maintained README, CLAW audit note and draft PR summary still described 24 governed artifacts.

The pinned source is CLAW `09b39ca8d0d1b7395249a1b3ae527ce36f7d8d7e`; `refresh_manifest.py --claw-root /private/tmp/xmech-refresh-20261104-snapshot/claw --check` passes. The prior website manifest at `56ec3db204095e425e2ed7481d4f97b997906815` has 24 artifacts. The capability count also increases from 27 to 28, while membership remains fourteen.

Update the maintained narrative to 26, regenerate site-audit provenance and assemble the page, and state the 24-to-26 increase in the refresh PR. This is propagation of the canonical manifest, not a methodology change.
