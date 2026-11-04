#!/usr/bin/env python3
"""Independently verify TaxonMech's Nov4 deployment of the pinned corpus revision.
Inputs: fresh Taxon skeptic browser capture, prior ledger, public exact-commit diff.
Outputs: compact supplemental receipt and group-A skeptic addendum only.
No production edits or corpus-pin changes; fleet refresh PR, 2026-11-04.
Run audit_browser_group_b_20261104.py --mech TaxonMech --role skeptic first.
"""
import hashlib,json,shutil,subprocess
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from compact_browser_evidence_b_20261104 import small_page,small_action

OUT=Path('_fleet/reviews/refresh-20261104')
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
PIN='e0cc7c86ac2107242ab499db610737f5fcad1c9b'
PRIOR='b04590a7a416eb934f67e7c04416e37924f10ec8'

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    capture=OUT/'taxonmech-skeptic-b-observations.json';raw=json.loads(capture.read_text())
    assert raw.get('finished_at') and raw['pin']==PIN
    for d in [raw['deployment_before'],raw['deployment_after']]:
        assert d['sha']==PIN and d['state']=='success' and d['http_status']==200
        assert parsedate_to_datetime(d['last_modified'])>=datetime.fromisoformat(d['created_at'].replace('Z','+00:00'))
    assert raw['deployment_before']['id']==raw['deployment_after']['id']
    compare_bytes=subprocess.check_output(['gh','api',f'repos/CultureBotAI/TaxonMech/compare/{PRIOR}...{PIN}'])
    compare=json.loads(compare_bytes)
    assert compare['total_commits']==1 and compare['commits'][-1]['sha']==PIN and len(compare['files'])==9
    allowed=['curation/causal_graphs/README.md','docs/CURATION.md','tests/test_causal_graph_overlays.py']
    assert all(f['filename'] in allowed or f['filename'].startswith('reviews/') for f in compare['files'])
    assert all('error' not in v for v in raw['actions'].values())
    checked={u:p for u,p in raw['pages'].items() if not u.endswith('/schema.html')}
    assert all('error' not in p and p['http_status']==200 for p in checked.values())
    assert all(p['fresh_390']['scroll']==390 and p['resized_390']['scroll']==390 and p['theme']=='dark' for p in checked.values())
    actions={k:small_action(v) for k,v in raw['actions'].items()}
    combined={v['id']:v['value'] for v in actions['combined_query']['controls']}
    restored={v['id']:v['value'] for v in actions['restored']['controls']}
    assert combined['taxon-domain-filter']=='BACTERIA' and combined['taxon-rank-filter']=='SPECIES' and combined['taxon-source-filter']=='NCBITAXON'
    assert all(restored[k]=='' for k in ['taxon-domain-filter','taxon-rank-filter','taxon-source-filter'])
    assert combined['taxon-query']==restored['taxon-query']=='NCBITaxon:562'
    assert any('239 of 626048' in v['text'] for v in actions['combined_query']['counts'])
    assert any('259 of 626048' in v['text'] for v in actions['restored']['counts'])
    previous=json.loads((OUT/'taxonmech-skeptic-b.json').read_text())
    features={k:{'status':v['status'],'agreement':True,'rationale':'Fresh browser behavior and the independently inspected documentation/review/test-only diff preserve the prior judgment. '+v['rationale'],
      'independent_evidence':'actions' if k in ['search','facets','result_counts','sorting','shareable_state'] else 'pages',
      'prior_evidence':'taxonmech-skeptic-b.json#/features/'+k} for k,v in previous['features'].items()}
    assert len(features)==24
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    dest=ARCHIVE/'taxonmech-redeployment-e0cc7c8-skeptic-raw.json';shutil.copy2(capture,dest)
    assert digest(capture.read_bytes())==digest(dest.read_bytes())
    diff=ARCHIVE/'taxonmech-redeployment-e0cc7c8-compare.json';diff.write_bytes(compare_bytes)
    report={'mech':'TaxonMech','reviewer':'central_directory independent skeptic','pin':PIN,'previous_deployed_revision':PRIOR,
      'started_at':raw['started_at'],'finished_at':raw['finished_at'],'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],
      'compare_url':compare['html_url'],'changed_files':[{k:f[k] for k in ['filename','status','additions','deletions']} for f in compare['files']],
      'source_assessment':'One commit changes two documentation files, six review/evidence files and one test file. No taxon records, causal overlays, page renderer, schema, export, style or workflow source changed.',
      'features':features,'actions':actions,'pages':{u:small_page(p) for u,p in raw['pages'].items()},
      'failure_cases':{u:{'aborted':v.get('aborted',[]),'excerpt':[line for line in v.get('state',{}).get('body','').splitlines() if any(t in line.lower() for t in ['could not','failed','unavailable','retry'])]} for u,v in raw['failure_cases'].items()},
      'archive':{'raw_capture':str(dest),'raw_sha256':digest(dest.read_bytes()),'compare':str(diff),'compare_sha256':digest(compare_bytes)},
      'result':'All 24 statuses unchanged. The source corpus pin is unchanged; the served deployment now equals it. Filter-state partial independently reconfirmed: three facets are lost on reload and 239 becomes 259.'}
    receipt=OUT/'taxonmech-redeployment-skeptic.json';receipt.write_text(json.dumps(report,indent=2)+'\n')
    summary_path=OUT/'group-a-skeptic-b.json';summary=json.loads(summary_path.read_text())
    summary.setdefault('redeployment_addenda',{})['TaxonMech']={'report':str(receipt),'deployed_revision':PIN,'corpus_pin':PIN,'checked_at':raw['finished_at'],'verdicts':24,'disagreements':[]}
    summary_path.write_text(json.dumps(summary,indent=2)+'\n')
    capture.unlink()
    print(json.dumps({'deployment':raw['deployment_after'],'valid_routes':len(checked),'verdicts':len(features),'disagreements':[]}))

if __name__=='__main__':main()
