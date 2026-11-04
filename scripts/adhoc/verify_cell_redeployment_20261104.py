#!/usr/bin/env python3
"""Independently verify CellStructureMech's concurrent Nov4 Pages redeployment.
Inputs: fresh skeptic browser capture, prior 24-verdict ledger, public commit diff.
Outputs: compact supplemental receipt and group-A skeptic addendum only.
Preserves original corpus pin and all shared production files; refresh PR, 2026-11-04.
Run audit_browser_group_b_20261104.py --mech CellStructureMech --role skeptic first.
"""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from compact_browser_evidence_b_20261104 import small_page,small_action

OUT=Path('_fleet/reviews/refresh-20261104')
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
PIN='6ef043ed4d3ca7ee0e3934cc1d12c073551fbacc'
DEPLOYED='d4d24c6c38d06ef27a6bac2c25ed381d50e96431'

def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    path=OUT/'cellstructuremech-skeptic-b-observations.json';raw=json.loads(path.read_text())
    assert raw.get('finished_at') and raw['pin']==PIN
    for d in [raw['deployment_before'],raw['deployment_after']]:
        assert d['sha']==DEPLOYED and d['id']==7545767004 and d['state']=='success' and d['http_status']==200
        assert parsedate_to_datetime(d['last_modified'])>=datetime.fromisoformat(d['created_at'].replace('Z','+00:00'))
    assert all('error' not in v and v['http_status']==200 for v in raw['pages'].values())
    assert all('error' not in v for v in raw['actions'].values())
    compare_bytes=subprocess.check_output(['gh','api',f'repos/CultureBotAI/CellStructureMech/compare/{PIN}...{DEPLOYED}'])
    compare=json.loads(compare_bytes)
    assert compare['total_commits']==1 and compare['commits'][-1]['sha']==DEPLOYED
    assert len(compare['files'])==22
    assert all(f['status']=='added' and f['filename'].startswith('reviews/structured/') and f['filename'].endswith(('/review.md','/review.yaml')) for f in compare['files'])
    previous=json.loads((OUT/'cellstructuremech-skeptic-b.json').read_text())
    actions={k:small_action(v) for k,v in raw['actions'].items()}
    for key in ['query:GO:0097589','query:MitoStore','query:cellstructuremech:insoluble_protein_deposit']:
        assert any('1 of 1022' in v['text'] for v in actions[key]['counts'])
    assert any('0 of 1022' in v['text'] for v in actions['query:no-such-record-nov4-audit']['counts'])
    for p in raw['pages'].values():
        assert p['fresh_390']['scroll']==390 and p['resized_390']['scroll']==390
        assert p['theme']=='dark'
    record_url='https://culturebotai.github.io/CellStructureMech/pages/structures/appendage/attachment_organelle_membrane.html'
    record=raw['pages'][record_url]
    links=[x['url'] for x in record['links'] if isinstance(x.get('url'),str)]
    assert all(any('GO_'+term in url for url in links) for term in ['0033111','0033099','0005886'])
    assert 'corpus as of 2026-11-03 05:55:11 UTC' in record['footer'] and 'd7c5fef867d9' in record['footer']
    blocked=[v for v in raw['failure_cases'].values() if v.get('aborted')]
    assert blocked and any('could not' in v.get('state',{}).get('body','').lower() or 'failed' in v.get('state',{}).get('body','').lower() for v in blocked)
    dest=ARCHIVE/'cellstructuremech-redeployment-d4d24c6-skeptic-raw.json';shutil.copy2(path,dest)
    assert digest(path.read_bytes())==digest(dest.read_bytes())
    diff=ARCHIVE/'cellstructuremech-redeployment-d4d24c6-compare.json';diff.write_bytes(compare_bytes)
    features={key:{'status':v['status'],'agreement':True,'rationale':'Fresh browser check and independently verified review-only diff preserve the prior criterion judgment. '+v['rationale'],
                   'evidence':'actions' if key in ['search','facets','result_counts','sorting','shareable_state'] else 'pages',
                   'prior_evidence':'cellstructuremech-skeptic-b.json#/features/'+key} for key,v in previous['features'].items()}
    assert len(features)==24
    report={'reviewer':'central_directory independent skeptic','mech':'CellStructureMech','pin':PIN,
      'started_at':raw['started_at'],'finished_at':raw['finished_at'],'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],
      'compare_url':compare['html_url'],'changed_files':[{k:f[k] for k in ['filename','status','additions','deletions']} for f in compare['files']],
      'source_assessment':'Exactly one commit adds 22 reviews/structured review.md/review.yaml files; no schema, record, render, export, style or workflow source changed.',
      'features':features,'actions':actions,'pages':{u:small_page(p) for u,p in raw['pages'].items()},
      'failure_cases':{u:{'aborted':v.get('aborted',[]),'excerpt':[line for line in v.get('state',{}).get('body','').splitlines() if any(t in line.lower() for t in ['could not','failed','unavailable','retry'])]} for u,v in raw['failure_cases'].items()},
      'archive':{'raw_capture':str(dest),'raw_sha256':digest(dest.read_bytes()),'compare':str(diff),'compare_sha256':digest(compare_bytes)},
      'result':'All 24 verdicts unchanged; source corpus pin retained and served deployment separately recorded.'}
    receipt=OUT/'cellstructuremech-redeployment-skeptic.json';receipt.write_text(json.dumps(report,indent=2)+'\n')
    summary_path=OUT/'group-a-skeptic-b.json';summary=json.loads(summary_path.read_text())
    summary.setdefault('redeployment_addenda',{})['CellStructureMech']={'report':str(receipt),'deployed_revision':DEPLOYED,'corpus_pin':PIN,'checked_at':raw['finished_at'],'verdicts':24,'disagreements':[]}
    summary_path.write_text(json.dumps(summary,indent=2)+'\n')
    path.unlink() # full capture verified in archive; compact excerpt remains
    print(json.dumps({'deployment':raw['deployment_after'],'routes':len(raw['pages']),'verdicts':len(features),'disagreements':[]}))

if __name__=='__main__':main()
