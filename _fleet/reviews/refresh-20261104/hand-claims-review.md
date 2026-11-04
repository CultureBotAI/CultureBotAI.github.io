# Hand-curated claim audit — 2026-11-04

This is the read-only source audit supporting the refresh, before the separate
adversarial review of the final PR head. It used the fourteen Mech pins in
`/private/tmp/xmech-refresh-20261104-snapshot/revisions.json`, bounded by
`2026-11-04T11:34:25.626729+00:00`. It wrote only the audit helpers and receipts
in the new worktree. No original checkout or shared Mech checkout was changed.

## Cross-reference coverage

`hand-claims-sources.json` contains all 59 `XREFS` entries, their exact original
claims, immutable replacement URLs, primary-file SHA-256 hashes, line-anchor
excerpts, and auxiliary `path@sha:line` evidence. The 59 ordered pairs match the
template's detailed list exactly. Each arrow still points to the consuming
Mech or the Mech to which the scope decision defers. No new relationship or
measurement rule is proposed.

All 59 primary evidence files exist at the new pins. Fifty-six are byte-identical
to their cited previous versions. The other three references cite the same
TaxonMech `docs/CURATION.md`: its scope table is unchanged; its later section now
documents implemented causal-graph overlays. The changed section does not
reverse those scope relationships. Every existing `#L` anchor was inspected
against its new pinned file and still addresses the claimed block. The
auxiliary CMMMech history adapter changed its exclusive-write fallback; its
credit and the AIMech adapter's independent credit remain unchanged.

The older `/blob/main/` URLs should also become immutable refresh-pin URLs.
This supplies current evidence without implying that a frozen sibling snapshot
was reacquired. Its original acquisition pins stay inside its manifest.

## Fact changes and wording decisions

| Locator | Previous wording or value | Verified replacement | Evidence |
| --- | --- | --- | --- |
| TaxonMech → PathwayMech | 99 records / 122 inline history events | 104 records / 127 events | Root's `secondary-fleet.json`, using top-level `curation_history` in all 280 pinned pathway records; schema's CurationEvent credit remains at line 95. |
| NaturalProductMech → AntibioticMech | 209 compounds share the linked structure | 213 records link to AntibioticMech | `hand-claims-counts.json`: owner records with `related_records[].corpus: AntibioticMech`; exact record paths and link samples are retained. Four other owners link to PathwayMech. |
| TraitMech → HabitatMech | 11 label-only trait nodes | 9 label-only trait nodes | The same counter reads every measured habitat record's graph nodes. All nine `node_type: TRAIT` nodes lack grounding/trait-term/identifier fields. |
| CommunityMech → MediaIngredientMech | Historical 17 imported / 10 live / 7 merged decomposition | 18 measured ingredient records retain synonyms with `source: communitymech-unmapped` | Exact owner paths and synonym samples are in `hand-claims-counts.json`. Seventeen also retain literal `source_id=communitymech.ingredient:...` text; `Edta.yaml` does not. Do not claim that all 18 preserve that literal source ID. |
| CultureMech → TraitMech | “nearly every TraitMech write script goes through them” | Name verified examples, or describe the shared helpers without a writer-coverage quantifier | The helper source credits are valid; the prose had no defined writer denominator. The root editor verified `add_abia_system_trait.py` and `enrich_oxidase_test_trait.py` as concrete examples using both helpers. |
| CellStructureMech → TaxonMech | “Every TaxonMech record is written through them” | “TaxonMech’s seeder writes records through the validated writer.” | `src/taxonmech/seed.py` at `e0cc7c86ac2107242ab499db610737f5fcad1c9b`, line 1372: `write_validated_taxon(doc, path)`. Helper docstrings credit HabitatMech / CellStructureMech. This does not assert universal coverage of every possible writer. |

The remaining typed pathway relationships retain their measured counts:
TraitMech has 19 links in 11 records to 15 targets; CellStructureMech has six
records and three targets; AntibioticMech has eight records and five targets;
NaturalProductMech has four records and two targets. Role distinctions remain
explicit. MIM has zero native causal graphs; its seven listed sibling links
remain schema permissions, not populated record relationships. The measured
CommunityMech ingredient identifiers all use the retired numeric
`MediaIngredientMech:` form. Seventeen CellStructureMech scripts name both
curation-history and validated-write helpers; their exact paths are retained.

## Auxiliary inventories retained in the notes

`hand-claims-auxiliary.json` independently validates products that the fleet
census deliberately does not count as additional Mech records:

- ProteinTraitsMech's protein inventory has **958** proteins with qualified
  examples, **648** with legacy examples only, and **996** discovery-only
  proteins. These replace 949 / 657 / 996. Parsed JSONL counts agree with
  `data/cross_mech/coverage.json`, and its file hash matches that receipt.
  The **16,082** protein-mention rows are unchanged and match their recorded
  hash. These qualifications are not whole-record REVIEWED statuses.
- DUFMech has **8,154 SEEDED** and **142 IN_PROGRESS** native FamilyRecords;
  PF13271 moved from SEEDED to IN_PROGRESS. All **8,296** remain UNSCORED.
  Every native YAML blob was read from the pinned Git archive and checked
  against `data/families/manifest.json`. The separate frozen discovery payload
  still has **16,298** rows, **6,532** scanned families and **1,764** unscanned
  additions; its payload hash matches its manifest. The measured census
  remains the frozen seed worklist, not these native records.
- All **246** NaturalProductMech referenced graph components resolve from
  **27** owner records. Every component's `record_id`, `standard_inchi_key`
  and `graph.graph_id` matches its owner and reference. Twenty-one component
  files changed since the previous refresh, so equality was checked directly
  rather than inferred from an unchanged component tree.
- TaxonMech's **100,745** distinct listed strains and **20,648** records with
  a type strain are stated by its pinned landing page; its README states
  **21,071** listed strains with genome identifier links. Only eleven taxon
  record blobs changed since the previous pins, and each parses identically
  outside `curation_history` and `causal_graphs`. All other record blobs are
  unchanged. Thus those strain and genome metadata totals did not change.
  A separate pinned-tree scan finds **15** records with causal graphs; the
  only **two TRAIT** nodes belong to the two Bacillus subtilis records and
  both are grounded to `METPO:1000874`. There are no HABITAT nodes in those
  graphs. The receipt retains all graph-owner paths and node-type counts.
- CultureMech's pin itself is unchanged, preserving its audited record and
  ingredient-occurrence figures. CommunityMech's map coverage is handled by
  the separate browser audit because it is a derived live-site product.

## HUB, source identity, schemas and licenses

`hand-claims-hub.json` supplies pinned source excerpts for every one of the 13
HUB relationships. TraitMech's templates identify kg-microbe's dated DeepWalk
input; TaxonMech and HabitatMech's extraction modules enumerate the kg-microbe
inventories they consume; CommunityMech's GTDB grounding and embedding loader
identify their input files; MIM's dictionary loader reconstructs identities and
synonyms from the published SSSOM set; CultureMech's matcher reads the MediaDive
transform. These remain input relationships. The namespace-only spokes are
supported by the actual schema namespace/shared-module declarations.

The current kg-microbe default branch is **master**, pinned separately for this
integration check at `ba19536867b1d1e93fe14745dac6b232bffcd4d3` (commit date
2026-11-04T04:26:11Z). At that pin, `docs/INGREDIENT_ACCEPTANCE.md` states:

> Registering `mim_ingredients` does not add it to the default production batch,
> and a `production` selection is refused.

Lines 30–32 also record `candidate_only` and
`production_promotion_authorized: false`; lines 64–70 reserve promotion for a
separate authorization and production review. This supports retaining MIM's
candidate-integration wording. It does not move the independent, published
2025-03-07 release comparison. The six Mechs whose HUB notes say no release
had empty public GitHub release inventories at the check; no new export spoke
is justified.

All top-level license files are byte-identical to the previous Mech pins.
The existing CC BY 4.0 / BSD-3-Clause statements and upstream-terms qualifications
remain supported. AIMech's explicit data grant still covers AIO source data
and derived imports without specifying the maintained-concept grant.
Schema class names agree with the graph's record types. CultureMech,
TraitMech and ProteinTraitsMech document their record classes without marking
those main classes `tree_root: true`; their graph entries name the documented
record classes and should not be described as assertions about that optional
LinkML flag. DUFMech's FamilyRecord class is distinct from the counted worklist,
as the page already explains. No tagline, source list or advertised grounding
chip required a methodology change; the known completeness issue for chips
remains separate (#154).

CLAW's pinned README still distinguishes supported discovery, validated dry
runs and shared tools from unimplemented execution/apply modes. The new
evidence-reference capability is represented by the manifest refresh rather
than by changing those orchestration claims.

## Links and limits

The URL canary persisted a successful HEAD result before the full pass.
All **53** distinct card/Explore URLs in the maintained template returned HTTP
200; see `hand-claims-links.json`. HEAD proves reachability, not JavaScript
behavior or fragment navigation. The separate feature reviewers exercise
those behaviors. No card/Explore route change was proposed.

An ignore-independent search (`rg -uu`) found no occurrences of the broken
feature-only CMMMech/AIMech `pages/schema.html` or CellStructureMech
`pages/map.html` links outside the feature JSON, generated page, review
receipts and helpers. Their feature evidence URLs are corrected by the browser
audit. The existing central mobile overflow issue #533 is outside this source
refresh. No new graph methodology, census namespace or ingestion claim was
introduced by this audit.

The root editor independently verifies and applies these proposals. This
source audit does not replace the requested read-only review of the final PR
head, and it does not authorize merging.
