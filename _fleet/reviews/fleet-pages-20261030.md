# Mech Pages check — October 30, 2026

Deployment freshness and landing-page smoke checks only; no new feature-by-feature audit.

Coverage: 14 manifest members; 28 desktop/mobile views. All returned HTTP 200, populated content and one main landmark, with no captured JavaScript/HTTP errors or horizontal overflow.

Fleet authority: `CultureBotAI/culturebotai-claw@18774380e032acb6da0d195214c59368cd47594f`; manifest SHA-256 `9fa51f0f3bbd8e2e15271d7189364fc9d8caaca87e4357e988adbd67900e7cc4`. Acquisition times, complete SHAs, deployment statuses and HTTP evidence are in [the receipt](fleet-pages-20261030.json).

| Mech | Main | Deployed | Publication |
| --- | --- | --- | --- |
| CultureMech | `a74dd48` | `9ea7ff3` | unchanged public inputs |
| MediaIngredientMech | `014fe04` | `bd9e730` | unchanged public inputs |
| CommunityMech | `a063177` | `060b1f3` | unchanged public inputs |
| TraitMech | `631087f` | `631087f` | current main |
| ProteinTraitsMech | `64daeed` | `64daeed` | current main |
| AntibioticMech | `13bf568` | `13bf568` | current main |
| CellStructureMech | `eaaef6a` | `eaaef6a` | current main |
| HabitatMech | `73f5de1` | `73f5de1` | current main |
| NaturalProductMech | `9deaa5e` | `9deaa5e` | current main |
| TaxonMech | `830eb57` | `830eb57` | current main |
| PathwayMech | `d869d5b` | `a2dc854` | unchanged public inputs |
| DUFMech | `1ad8fdc` | `1ad8fdc` | current main |
| CMMMech | `b9ef414` | `b9ef414` | current main |
| AIMech | `97c308f` | `97c308f` | current main |

Older deployment SHAs were checked against the changed files and their owning builders:

- **CultureMech:** No changed site inputs. Shared claw builder also unchanged; its deployed build used 432f4ecffa33fef3d3e4543bcd9bd3c00131408c, whose difference to the current claw pin is agent instructions only.
- **MediaIngredientMech:** No changed inputs consumed by scripts/build_pages_site.py; intervening commits change reviews, reports and agent workflow files.
- **CommunityMech:** No changed community-renderer inputs or docs files. The intervening kb/taxa record is outside its kb/communities input.
- **PathwayMech:** Latest change is PathBank provenance validation and review records; committed pages unchanged. Automatic Build and test must pass before its publish workflow runs.

No manual rebuild was dispatched. ProteinTraitsMech's existing automatic publication completed during this check. The central directory changes remain in PR #527 pending the maintainer's merge decision.

The read-only acquisition canary saved deployment metadata, workflow sources and served HTML for CommunityMech before the fleet pass. Its browser canary saved populated desktop/mobile views and screenshots before the remaining sites. Rate limits under parallel load and full catalogue interactions were not exercised.

Independent review found two latent audit-helper defects (#531 and #532); the selected evidence was unaffected. Regression fixtures failed on the original logic and passed after the latest-status and incomplete-evidence checks were repaired.

Reproduction helpers: `scripts/adhoc/audit_mech_pages_20261030.py`, `smoke_mech_pages_20261030.py`, and `summarize_mech_pages_20261030.py`. Raw HTML, API responses and screenshots are retained locally under `/private/tmp/mech-pages-20261030/`.
