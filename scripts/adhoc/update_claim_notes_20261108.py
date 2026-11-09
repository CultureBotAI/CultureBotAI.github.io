#!/usr/bin/env python3
"""Update checked secondary claims and source notes for the November 8 refresh PR.

Inputs: pinned corpus receipts, source excerpts, and independent hand-claim audit.
Outputs: hand-maintained audit notes and the two mirrored XREF descriptions.
2026-11-08. No generated data or original shared checkout is edited.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    evidence = ROOT / '_fleet/reviews/refresh-20261108'
    secondary = json.loads((evidence / 'secondary-fleet.json').read_text())
    links = json.loads((evidence / 'hand-claims-counts.json').read_text())
    auxiliary = json.loads((evidence / 'hand-claims-auxiliary.json').read_text())
    assert secondary['PathwayMech']['counts']['source_assertions'] == 22178
    assert secondary['PathwayMech']['counts']['quoted_evidence_items'] == 884
    assert links['NaturalProductMech']['related_record_counts']['AntibioticMech'] == 213
    assert links['HabitatMech']['trait_nodes'] == {'nodes': 9}
    assert links['MediaIngredientMech']['related_record_counts']['communitymech-unmapped'] == 18
    assert auxiliary['DUFMech']['native_curation_status'] == {'SEEDED': 8154, 'IN_PROGRESS': 142}
    assert auxiliary['NaturalProductMech']['referenced_components'] == 246
    assert auxiliary['NaturalProductMech']['owner_id_inchikey_and_graph_id_match']
    notes_path = ROOT / '_fleet/audit_notes.json'
    notes = json.loads(notes_path.read_text())
    replacements = {
        'AntibioticMech': [
            ('3,064', '3,105'),
            ('2,740', '2,767'),
            ('324 minted', '338 minted'),
            ('112 REVIEWED, 137 PROPOSED and 2,815 SEEDED', '145 REVIEWED, 155 PROPOSED and 2,805 SEEDED'),
            ('506 with a mode of action and 333 with a molecular target', '539 with a mode of action and 361 with a molecular target'),
        ],
        'CommunityMech': [
            (
                'The published landing tile counts 485 kb/communities records. Nine additional data/isolates records make the common census and repository-statistics total 494.',
                'The published landing tile counts 510 kb/communities records. Five additional kb/communities files and nine data/isolates records make the common census and repository-statistics total 524.'
            ),
        ],
        'HabitatMech': [
            ('1,294 REVIEWED, 1,915 SEEDED and 2,149', '1,295 REVIEWED, 1,914 SEEDED and 2,149'),
        ],
        'TraitMech': [
            ('761 records', '769 records'),
        ],
        'PathwayMech': [
            ('280', '282'),
            ('14,788', '14,838'),
            ('5,917', '5,922'),
            ('22,071', '22,178'),
            ('883 quoted', '884 quoted'),
            ('104 YAML records contain 127 inline events', '106 YAML records contain 129 inline events'),
        ],
        'CMMMech': [
            ('678 canonical', '698 canonical'),
            ('427 mineral', '447 mineral'),
            ('282 records carry NCBITaxon', '284 records carry NCBITaxon'),
            ('178 remain', '198 remain'),
        ],
    }
    for name, edits in replacements.items():
        for before, after in edits:
            if before in notes['notes'][name]:
                notes['notes'][name] = notes['notes'][name].replace(before, after)
            elif after not in notes['notes'][name]:
                raise ValueError(f'{name}: expected {before!r} in {notes["notes"][name]!r}')
    notes['notes']['culturebotai-claw'] = (
        'The 0ca25b8 canonical snapshot declares 15 members (fourteen corpus Mechs plus EdgeMech curation infrastructure), 26 governed artifacts and 28 capabilities per member. '
        'EdgeMech does not add a scientific corpus, published browser, record count or historical PR total. '
        'The evidence_reference_validation contract is enabled for MediaIngredientMech, CellStructureMech and HabitatMech, and disabled with explicit reasons for the other twelve members. '
        'Capability tooltips preserve canonical statuses, settings and reasons; inherited native review is not independent scientific approval, and contract adoption does not imply that a record has a REVIEWED-bearing status or that every workflow runs unattended.'
    )
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    notes['scope'] = (
        'All fourteen Mechs and culturebotai-claw were pinned from one GitHub head query for the November 8, 2026 refresh. '
        f"The common pin-time bound is {pins['pinned_at_utc']}. "
        'Census occurrences, shared-term overlap assets, complete heatmap record lists, recent-record histories and repository statistics use those same immutable revisions. '
        'Record globs, namespace recognition and normalization, shared-term extraction and the separately pinned kg-microbe release comparison are unchanged. '
        'Card figures and secondary claims were rechecked against pinned source files and live sites; repository and published-browser totals retain their stated distinctions. '
        'Merged-PR counts are all-time totals queried during this refresh for fourteen Mechs, CLAW and this website. '
        'Website feature verdicts have their own dates, served revisions and browser-review scope in site_features.json. '
        'The separately versioned kg-microbe core release comparison remains excluded from Mech record totals and shared-term graph indexes.'
    )
    shared = {
        '104 pathway YAML records include 127 inline curation-history events': '106 pathway YAML records include 129 inline curation-history events',
    }
    output = {notes_path: json.dumps(notes, indent=2) + '\n'}
    for file in ['_fleet/fleet_fragment.html', '_fleet/mechs_template.md']:
        path = ROOT / file
        text = path.read_text()
        for before, after in shared.items():
            if before in text:
                text = text.replace(before, after)
            elif after not in text:
                raise ValueError(f'{file}: expected {before!r}')
        output[path] = text
    readme_path = ROOT / '_fleet/README.md'
    readme_text = readme_path.read_text()
    old_readme_hist = 'TaxonMech supplies history machinery used by 104 PathwayMech records carrying\n127 events.'
    new_readme_hist = 'TaxonMech supplies history machinery used by 106 PathwayMech records carrying\n129 events.'
    if old_readme_hist in readme_text:
        readme_text = readme_text.replace(old_readme_hist, new_readme_hist)
    elif new_readme_hist not in readme_text:
        raise ValueError('_fleet/README.md: expected PathwayMech history sentence')
    output[readme_path] = readme_text
    if args.apply:
        for path, text in output.items():
            path.write_text(text)
    print('Verified corpus counters; ' + ('updated' if args.apply else 'planned') + ' audit notes and matching XREF descriptions.')


if __name__ == '__main__':
    main()
