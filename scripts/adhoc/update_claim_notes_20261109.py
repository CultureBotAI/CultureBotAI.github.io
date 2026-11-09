#!/usr/bin/env python3
"""Update checked secondary claims and source notes for the November 9 refresh PR.

Inputs: pinned corpus receipts, source excerpts, and independent hand-claim audit.
Outputs: hand-maintained audit notes.
2026-11-09. No generated data or original shared checkout is edited.
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
    evidence = ROOT / '_fleet/reviews/refresh-20261109'
    secondary = json.loads((evidence / 'secondary-fleet.json').read_text())
    links = json.loads((evidence / 'hand-claims-counts.json').read_text())
    auxiliary = json.loads((evidence / 'hand-claims-auxiliary.json').read_text())
    assert secondary['PathwayMech']['counts']['source_assertions'] == 22178
    assert secondary['PathwayMech']['counts']['quoted_evidence_items'] == 884
    assert secondary['HabitatMech']['counts']['attested_by_at_least_2_sources'] == 175
    assert secondary['AntibioticMech']['counts']['minted_ids'] == 343
    assert secondary['AntibioticMech']['counts']['grounded_ids'] == 2782
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
            ('3,105', '3,125'),
            ('2,767', '2,782'),
            ('338 minted', '343 minted'),
            ('145 REVIEWED, 155 PROPOSED and 2,805 SEEDED', '159 REVIEWED, 167 PROPOSED and 2,799 SEEDED'),
            ('539 with a mode of action and 361 with a molecular target', '557 with a mode of action and 374 with a molecular target'),
        ],
        'CommunityMech': [
            (
                'The published landing tile counts 510 kb/communities records. Five additional kb/communities files and nine data/isolates records make the common census and repository-statistics total 524.',
                'The published landing tile counts 511 kb/communities records. Eighteen additional data/isolates records make the common census and repository-statistics total 529.'
            ),
        ],
        'HabitatMech': [
            ('1,295 REVIEWED, 1,914 SEEDED and 2,149', '1,298 REVIEWED, 1,911 SEEDED and 2,147'),
        ],
    }
    for name, edits in replacements.items():
        for before, after in edits:
            if before in notes['notes'][name]:
                notes['notes'][name] = notes['notes'][name].replace(before, after)
            elif after not in notes['notes'][name]:
                raise ValueError(f'{name}: expected {before!r} in {notes["notes"][name]!r}')
    notes['notes']['culturebotai-claw'] = (
        'The e539df0 canonical snapshot declares 15 members (fourteen corpus Mechs plus EdgeMech curation infrastructure), 26 governed artifacts and 28 capabilities per member. '
        'EdgeMech does not add a scientific corpus, published browser, record count or historical PR total. '
        'The evidence_reference_validation contract is enabled for MediaIngredientMech, CellStructureMech and HabitatMech, and disabled with explicit reasons for the other twelve members. '
        'Capability tooltips preserve canonical statuses, settings and reasons; inherited native review is not independent scientific approval, and contract adoption does not imply that a record has a REVIEWED-bearing status or that every workflow runs unattended.'
    )
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    notes['scope'] = (
        'All fourteen Mechs and culturebotai-claw were pinned from one GitHub head query for the November 9, 2026 refresh. '
        f"The common pin-time bound is {pins['pinned_at_utc']}. "
        'Census occurrences, shared-term overlap assets, complete heatmap record lists, recent-record histories and repository statistics use those same immutable revisions. '
        'Record globs, namespace recognition and normalization, shared-term extraction and the separately pinned kg-microbe release comparison are unchanged. '
        'Card figures and secondary claims were rechecked against pinned source files and live sites; repository and published-browser totals retain their stated distinctions. '
        'Merged-PR counts are all-time totals queried during this refresh for fourteen Mechs, CLAW and this website. '
        'Website feature verdicts have their own dates, served revisions and browser-review scope in site_features.json. '
        'The separately versioned kg-microbe core release comparison remains excluded from Mech record totals and shared-term graph indexes.'
    )
    output = {notes_path: json.dumps(notes, indent=2) + '\n'}
    if args.apply:
        for path, text in output.items():
            path.write_text(text)
    print('Verified corpus counters; ' + ('updated' if args.apply else 'planned') + ' audit notes.')


if __name__ == '__main__':
    main()
