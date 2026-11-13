# Live landing content spot-check, November 12, 2026

The `*-final-landing.json` receipts record browser-rendered landing text,
headings and links, final-page HTTP headers, and the successful GitHub Pages
deployment before and after the observation. Each final page returned HTTP 200,
carried a GitHub Pages response header, and had a Last-Modified date no earlier
than its deployment request. The deployment stayed fixed during every check.
No browser JavaScript errors were observed.

| Site | Current deployment | Landing content confirmed |
| --- | --- | --- |
| [CofactorMech](https://culturebotai.github.io/CofactorMech/) | `89a8ca3b37b4cd3607fdbb0b74b7b73c5c539fee` | 14 records; 6 coenzymes, 5 metal ions, 3 prosthetic groups; code/schema CC0 |
| [AssayMech](https://culturebotai.github.io/AssayMech/) | `f7d2d79aa00b6e47816f2f7dea8b418ec084b91e` | 9 records; 6 ontology assay concepts and 3 operational assays; code/schema CC0 |
| [CMMMech](https://culturebotai.github.io/CMMMech/pages/index.html) | `9bf445aea708681be2283b5df346e769de3da623` | 713 materials, 609 mechanisms, 500 materials with mechanisms; category counts 66, 462, 111, 36, 31, 7 |
| [HabitatMech](https://culturebotai.github.io/HabitatMech/pages/index.html) | `61edb3d0ae912e8f041378e669928051fbbd509e` | 3,209 habitats, 2,143 ontology-grounded, 175 corroborated by 2+ sources, 1,301 REVIEWED status |
| [CommunityMech](https://culturebotai.github.io/CommunityMech/) | `03eab4fc6cf9ee91545e610cb8e008eaeeb20cd3` | 512 communities, 16 categories; landing links to browser, three maps, network, schema and exports |

These facts agree with the combined refresh sources. REVIEWED is the published
workflow status, not a claim of human review. CommunityMech's landing counts
communities; the additional 37 isolate records are measured by the pinned
repository census, not this landing observation.

The helper is `scripts/adhoc/spotcheck_live_pages_20261112.py`. CofactorMech was
run end to end first and its nonempty, parsed receipt and content hash were
verified before the other four sites ran through the same helper and browser
environment. Initial `*-landing.json` receipts retain the first pass. The final
pass uses the final rendered URL for HTTP metadata, explicitly handling root
meta-refresh shells, and checks the Last-Modified bound. Its CofactorMech canary
was verified again before the remaining four final runs.

This is a five-site landing-content spot-check, not a complete website-feature
audit. It does not redate feature verdicts, prove that every linked destination
works, or reproduce record-level scientific claims. CofactorMech and AssayMech's
existing complete audits are retained separately in `../site-launch-20261112/`;
their current deployment revisions still match those audits.
