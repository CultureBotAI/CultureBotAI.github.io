#!/usr/bin/env python3
"""Update checked secondary claims and source notes for the November 4 refresh PR.

Inputs: pinned corpus receipts, source excerpts, and independent hand-claim audit.
Outputs: hand-maintained audit notes and the two mirrored XREF descriptions.
2026-11-04. No generated data or original shared checkout is edited.
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
    evidence = ROOT / '_fleet/reviews/refresh-20261104'
    secondary = json.loads((evidence / 'secondary-fleet.json').read_text())
    links = json.loads((evidence / 'hand-claims-counts.json').read_text())
    auxiliary = json.loads((evidence / 'hand-claims-auxiliary.json').read_text())
    assert secondary['PathwayMech']['counts']['source_assertions'] == 22071
    assert secondary['PathwayMech']['counts']['quoted_evidence_items'] == 883
    assert links['NaturalProductMech']['related_record_counts']['AntibioticMech'] == 213
    assert links['HabitatMech']['trait_nodes'] == {'nodes': 9}
    assert links['MediaIngredientMech']['related_record_counts']['communitymech-unmapped'] == 18
    assert auxiliary['DUFMech']['native_curation_status'] == {'SEEDED': 8154, 'IN_PROGRESS': 142}
    assert auxiliary['NaturalProductMech']['referenced_components'] == 246
    assert auxiliary['NaturalProductMech']['owner_id_inchikey_and_graph_id_match']
    notes_path = ROOT / '_fleet/audit_notes.json'
    notes = json.loads(notes_path.read_text())
    replacements = {
        'AntibioticMech': [('3,012','3,064'),('2,702','2,740'),('310 minted','324 minted'),
                           ('96 REVIEWED, 97 PROPOSED and 2,819 SEEDED','112 REVIEWED, 137 PROPOSED and 2,815 SEEDED'),
                           ('492 with a mode of action and 309 with a molecular target','506 with a mode of action and 333 with a molecular target')],
        'CellStructureMech': [('1,001','1,022'),('852 GO-grounded','873 GO-grounded'),
                              ('827 records with components and 970 with causal graphs (1,002 individual graphs and 4,336','848 records with components and 991 with causal graphs (1,023 individual graphs and 4,704')],
        'CommunityMech': [('480','485'),('total 489','total 494')],
        'HabitatMech': [('1,286 REVIEWED, 1,923 SEEDED and 2,151','1,294 REVIEWED, 1,915 SEEDED and 2,149')],
        'MediaIngredientMech': [('2,953','2,956'),('260 UNMAPPED, 81 REJECTED','262 UNMAPPED, 82 REJECTED'),
                                ('The record total and status distribution are unchanged. ', '')],
        'NaturalProductMech': [('3,116','3,136'),('3,407','3,441'),('806 supported','840 supported'),
                               ('2,341','2,351'),('185 records','216 records'),('297 graph-bearing','317 graph-bearing'),
                               ('795 individual graphs: 549 inline','815 individual graphs: 569 inline')],
        'ProteinTraitsMech': [('429,394','429,421'),('84,597','84,624'),
                              ('949 proteins with qualified examples, 657 with legacy examples only','958 proteins with qualified examples, 648 with legacy examples only')],
        'DUFMech': [('8,155 are SEEDED and 141 are IN_PROGRESS','8,154 are SEEDED and 142 are IN_PROGRESS')],
        'TraitMech': [('748 records','761 records')],
        'PathwayMech': [('275','280'),('14,691','14,788'),('5,912','5,917'),('21,871','22,071'),
                        ('879 quoted','883 quoted'),('99 YAML records contain 122 inline events','104 YAML records contain 127 inline events')],
        'CMMMech': [('663 canonical','678 canonical'),('412 mineral','427 mineral'),('499 records describe 607 mechanisms','500 records describe 609 mechanisms'),
                    ('164 remain','178 remain'),('without assigned microbial mechanisms','without assigned mechanisms')],
    }
    for name, edits in replacements.items():
        for before, after in edits:
            notes['notes'][name] = notes['notes'][name].replace(before, after)
    notes['notes']['culturebotai-claw'] = (
        'The 09b39ca canonical snapshot declares fourteen members, twenty-six governed artifacts and twenty-eight capabilities per member. '
        'The added evidence_reference_validation contract is enabled for MediaIngredientMech and disabled with explicit reasons for the other thirteen Mechs. '
        'Capability tooltips preserve the canonical status, settings and reasons, including native validation or history that does not yet meet a shared adapter contract. '
        'Contract adoption and separate scientific review artifacts do not imply that a record has a REVIEWED-bearing status or that every workflow runs unattended.')
    # Website scope is finalized only after all live audits and skeptical passes.
    pins = json.loads((args.snapshot / 'revisions.json').read_text())
    notes['scope'] = (
        'All fourteen Mechs and culturebotai-claw were pinned from one GitHub head query for the November 4, 2026 refresh. '
        f"The common pin-time bound is {pins['pinned_at_utc']}. "
        'Census occurrences, shared-term overlap assets, complete heatmap record lists, recent-record histories and repository statistics use those same immutable revisions. '
        'Record globs, namespace recognition and normalization, shared-term extraction and the separately pinned kg-microbe release comparison are unchanged. '
        'Card figures and secondary claims were rechecked against pinned source files and live sites; repository and published-browser totals retain their stated distinctions. '
        'Merged-PR counts are all-time totals queried during this refresh for fourteen Mechs, CLAW and this website. '
        'Website feature verdicts have their own dates, served revisions and browser-review scope in site_features.json. '
        'The separately versioned kg-microbe core release comparison remains excluded from Mech record totals and shared-term graph indexes.')
    shared = {
        '99 pathway YAML records include 122 inline curation-history events': '104 pathway YAML records include 127 inline curation-history events',
        'For the 209 compounds': 'For the 213 compounds',
        'the 11 trait nodes in use': 'the 9 trait nodes in use',
        ", and nearly every TraitMech write script goes through them.": '. Checked curation scripts use both helpers, including add_abia_system_trait.py and enrich_oxidase_test_trait.py.',
        'Every TaxonMech record is written through them.': "TaxonMech's seeder writes records through the validated writer.",
    }
    old_mim = ('MediaIngredientMech imported 17 growth-media ingredient names that CommunityMech could not match to an existing ingredient. '
               'Each record keeps the name as a synonym from communitymech-unmapped and cites its CommunityMech source id (communitymech.ingredient:name). '
               '10 records are still live; the other 7 were merged into existing records.')
    draft_mim = ('Eighteen current MediaIngredientMech ingredient records retain synonyms sourced from communitymech-unmapped, '
               'with CommunityMech source identifiers such as communitymech.ingredient:name. '
               'These preserve unmatched growth-media ingredient names as ingredient records or synonyms.')
    new_mim = ('Eighteen current MediaIngredientMech ingredient records retain synonyms sourced from communitymech-unmapped. '
               'These preserve unmatched growth-media ingredient names as ingredient records or synonyms.')
    output = {notes_path: json.dumps(notes, indent=2) + '\n'}
    for file in ['_fleet/fleet_fragment.html', '_fleet/mechs_template.md']:
        path = ROOT / file
        text = path.read_text()
        for before, after in shared.items():
            text = text.replace(before, after)
        if file.endswith('.html'):
            text = text.replace(old_mim, new_mim).replace(draft_mim, new_mim)
        else:
            marked_old = old_mim.replace('communitymech-unmapped', '<code>communitymech-unmapped</code>').replace('communitymech.ingredient:name', '<code>communitymech.ingredient:name</code>')
            marked_new = new_mim.replace('communitymech-unmapped', '<code>communitymech-unmapped</code>').replace('communitymech.ingredient:name', '<code>communitymech.ingredient:name</code>')
            text = text.replace(marked_old, marked_new)
            marked_draft = draft_mim.replace('communitymech-unmapped', '<code>communitymech-unmapped</code>').replace('communitymech.ingredient:name', '<code>communitymech.ingredient:name</code>')
            text = text.replace(marked_draft, marked_new)
        output[path] = text
    if args.apply:
        for path, text in output.items():
            path.write_text(text)
    print('Verified corpus counters; ' + ('updated' if args.apply else 'planned') + ' audit notes and matching XREF descriptions.')


if __name__ == '__main__':
    main()
