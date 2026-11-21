#!/usr/bin/env python3
"""Record root auditor's 96 judgments for independent review, 2026-11-19.

Inputs: immutable baseline wording and fresh browser/download receipts.
Output: root/proposals.json. This does not write the published feature table.
Each retained statement was checked against the new observations; overrides
remove historical corpus claims that this site-only pass did not remeasure.
"""
import copy
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '_fleet/reviews/site-features-20261119/root'
BASELINE = 'bc50236b513043e907481c4a71b40d5251fcf744'
FILES = {'CofactorMech': 'cofactor-canary.json', 'AssayMech': 'assay-auditor.json',
         'AIMech': 'aimech-auditor-v2.json', 'TraitMech': 'trait-auditor.json'}

# Explicit per-criterion decisions, not inference from redeployment.
STATUSES = {
    'CofactorMech': 'present present present missing partial present present partial present missing present present missing present present partial present partial partial present present missing present not_applicable',
    'AssayMech': 'present present present missing partial present present partial present missing present present missing present present partial present partial partial present present missing present not_applicable',
    'AIMech': 'present present present present present present present present present present partial present present missing present present present partial partial partial present present partial not_applicable',
    'TraitMech': 'present present present present present present present partial present present present present present present present present present present partial partial present present partial present',
}
ORDER = 'search facets result_counts sorting shareable_state full_catalogue record_pages term_links evidence review_status curation_history source_link domain_view cross_mech_links corpus_stats category_browse suite_nav downloads schema_docs license build_provenance theme_toggle responsive load_failure'.split()
NOTES = {
    'AIMech': {
        'search': 'AIMech:KernelPCA returns one linked concept, Adam returns 131 matches and SoftDTW returns one across the 1,930-record catalogue. Literal-markup and unmatched queries return zero.',
        'facets': 'Origin, concept kind and AIO branch filters have Reset. Curated selects 1,488 records, algorithm selects 1,047 and Layer selects 168. Combining attention, Curated and architecture selects 48; Reset restores 1,930.',
        'result_counts': 'The matching count changes to one for AIMech:KernelPCA, 131 for Adam and zero for an unmatched query, separately from the 1,930 total.',
        'sorting': 'The browser offers six sort choices. Exercised name ascending, name descending and identifier ascending choices update the selected ordering and result rows.',
        'shareable_state': 'Search, origin, kind, branch and sort controls encode their state in the URL. A cold load of the combined attention, Curated and architecture query restores the controls and 48 matches.',
        'full_catalogue': 'The complete browser and downloaded index contain 1,930 records, matching 1,930 canonical YAML records and 1,930 static record pages in the untruncated deployed-revision inventory. Sampled links open populated records.',
        'record_pages': 'Browse links static curated/<name>.html and aio/<name>.html record pages. Sampled Adam, KernelPCA, SoftDTW and TrainingStrategy pages render populated records.',
        'evidence': 'Sampled curated claims link source rows and primary evidence URLs; the landing distinguishes 5,151 claims from 3,271 evidence citations.',
        'domain_view': 'The graph renders 1,950 nodes and 4,258 edges; the text map contains 1,259 concepts, a subset of the 1,930-record catalogue. KernelPCA and unmatched queries exercise both maps, with reset restoring their respective totals.',
        'corpus_stats': 'The landing reports 1,930 concepts (1,488 curated and 442 AIO), 5,151 curated claims and 3,271 evidence citations.',
        'category_browse': 'The landing links curated-kind and AIO-branch subsets with counts; the browser also provides working kind and branch filters.',
        'downloads': 'Linked index.json contains all 1,930 concepts as listing metadata with claim/source counts; it omits complete claims and evidence. The downloaded corpus_map.json contains 1,259 map points. Per-record YAML sources are also linked.',
        'build_provenance': 'Page footers identify the project snapshot date 2026-11-16 and digest 62a5ad9f4862, separately from upstream AIO import provenance.',
    },
    'TraitMech': {
        'license': 'Templated landing, Browse, record and map pages state CC BY 4.0 project data and BSD-3-Clause code, with third-party terms retained. The linked discussions index omits these licence notices and links.',
        'full_catalogue': 'Browse exposes 1,130 distinct record links, matching the landing, bulk export and all 1,130 canonical records and record HTML paths in the untruncated deployed-revision inventory.',
        'record_pages': 'All 1,130 traits have static pages under pages/traits/<category>/<slug>.html. Sampled animal pathogen, aerobic respiration and Wood–Ljungdahl pages show populated overview, grounding, curation and source sections.',
        'review_status': 'Sampled record headers and Identifier cards show the record workflow status, including REVIEWED on animal pathogen. This is distinct from a claim that all records were manually reviewed.',
        'domain_view': 'Sampled record pages render causal SVG diagrams. PaCMAP, text and graph-layout maps each render 1,130 traits, and the sequence map renders 156 associated proteins; these are separately labeled views.',
        'downloads': 'Download traits.json provides 1,130 full records, including definitions, evidence, causal graphs and curation history. Downloaded map exports contain 1,130 traits or 156 proteins as labeled.',
        'load_failure': 'Aborted JSON requests produce explicit map failure messages and Retry; retry after restoring requests recovers 1,130 traits or 156 proteins. Aborting discussion data shows Discussions could not be loaded; reload after restoring requests recovers 925 discussions.',
    },
}


def ptr(*parts):
    return '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def main():
    old = json.loads(subprocess.check_output(['git', 'show', f'{BASELINE}:_fleet/data/site_features.json'], cwd=ROOT, text=True))
    assert set(ORDER) == set(old['catalogue'])
    proposals = {}
    for mech, filename in FILES.items():
        raw = json.loads((BASE / filename).read_text())
        assert raw['complete'] and raw['deployment_before']['sha'] == raw['deployment_after']['sha']
        row = copy.deepcopy(old['mechs'][mech])
        row['deployed_revision'] = raw['deployment_after']['sha']
        row['checked_on'] = '2026-11-19'
        row['scope'] = ('Site-only Chrome/Playwright review on November 19, 2026 America/Los_Angeles; receipt timestamps are UTC. All 24 criteria were judged from current page content and reader actions, with identifier/label and empty searches, filters/reset, URL reload, theme persistence, fresh and resized 390px layouts, representative populated details and failed-request recovery where applicable. Complete inventories or published manifests support catalogue coverage. Successful deployment and served Last-Modified were checked before and after. Corpus census pins are unchanged. These auditor proposals require independent skeptical review.')
        archive = str((BASE / filename).relative_to(ROOT)) + '.gz'
        prefix = archive + '#'
        small = mech in ('CofactorMech', 'AssayMech')
        # All 24 statements are grounded in fresh receipts. Broad page pointers
        # include complete content/links, not only a screenshot or a page title.
        listing = 'index.html' if small else row['features']['search']['url']
        record = ('records/biotin/index.html' if mech == 'CofactorMech' else
                  'records/ax17-extracted-feii-ferrozine/index.html' if small else
                  row['features']['record_pages']['url'])
        listing_ref = prefix + ptr('pages', listing)
        record_ref = prefix + ptr('pages', record)
        action_ref = prefix + ptr('actions')
        pages_ref = prefix + ptr('pages')
        for feature, status in zip(ORDER, STATUSES[mech].split(), strict=True):
            entry = row['features'][feature]
            entry['status'] = status
            entry['note'] = NOTES.get(mech, {}).get(feature, entry['note'])
            evidence_page = entry['url'].split('#', 1)[0].split('?', 1)[0]
            specific_ref = prefix + ptr('pages', evidence_page) if evidence_page in raw['pages'] else record_ref
            evidence = [listing_ref, action_ref] if feature in ORDER[:6] else [specific_ref]
            if feature in ('domain_view', 'corpus_stats', 'category_browse', 'suite_nav', 'schema_docs', 'theme_toggle', 'responsive'):
                evidence = [pages_ref]
            if feature in ('full_catalogue', 'source_link', 'downloads', 'build_provenance'):
                evidence += [prefix + ptr('manifest' if small else 'source_inventory')]
            if feature == 'build_provenance' and not small:
                evidence += [pages_ref]
            if feature == 'license':
                evidence = [pages_ref, str((BASE / ('cofactor-supplement.json' if mech == 'CofactorMech' else 'assay-supplement.json')).relative_to(ROOT))] if small else [pages_ref, prefix + ptr('license_sources')]
            if feature == 'load_failure':
                evidence = [prefix + ptr('data_failure_probe' if small else 'failures'), pages_ref]
            if small and feature in ('full_catalogue', 'downloads', 'source_link', 'build_provenance'):
                evidence += [prefix + ptr('asset_integrity'), prefix + ptr('no_javascript')]
            if small and feature == 'responsive':
                evidence += [str((BASE / ('cofactor-supplement.json' if mech == 'CofactorMech' else 'assay-supplement.json')).relative_to(ROOT))]
            if mech == 'AIMech' and feature in ('domain_view', 'full_catalogue', 'downloads'):
                evidence += [str((BASE / 'aimech-supplement.json').relative_to(ROOT)) + '.gz']
            if mech == 'TraitMech' and feature in ('domain_view', 'full_catalogue', 'downloads', 'cross_mech_links', 'schema_docs'):
                evidence += [str((BASE / 'trait-supplement.json').relative_to(ROOT))]
            entry['evidence'] = evidence
        proposals[mech] = row
    target = BASE / 'proposals.json'
    target.write_text(json.dumps(proposals, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'path': str(target.relative_to(ROOT)), 'mechs': len(proposals), 'verdicts': sum(len(x['features']) for x in proposals.values())}))


if __name__ == '__main__':
    main()
