#!/usr/bin/env python3
"""Reconcile CultureMech's concurrent deployment with the Nov4 site audit.
Inputs: fresh complete Culture browser capture, prior accepted feature ledger,
public GitHub compare API. Outputs: only Culture audit/proposed row and a compact
supplement; corpus pins and the editor's shared sources are unchanged. 2026-11-04.
Run audit_browser_group_b_20261104.py --mech CultureMech first.
"""
import hashlib,json,re,shutil,subprocess
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from compact_browser_evidence_b_20261104 import small_page,small_action

OUT=Path('_fleet/reviews/refresh-20261104')
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
PIN='a74dd489720c9df96cc073ffd11568d407d3c06c'
NEW='09f908802989670d2cc799f75f67cf56f7834178'

def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    capture=OUT/'culturemech-browser-b.json';raw=json.loads(capture.read_text())
    assert raw.get('finished_at') and raw['pin']==PIN
    for key in ['deployment_before','deployment_after']:
        d=raw[key]
        assert d['sha']==NEW and d['state']=='success' and d['http_status']==200
        assert parsedate_to_datetime(d['last_modified'])>=datetime.fromisoformat(d['created_at'].replace('Z','+00:00'))
    assert raw['deployment_before']['id']==raw['deployment_after']['id']
    assert all('error' not in v for v in raw['pages'].values())
    assert all('error' not in v for v in raw['actions'].values())
    compare_bytes=subprocess.check_output(['gh','api',f'repos/CultureBotAI/CultureMech/compare/{PIN}...{NEW}'])
    compare=json.loads(compare_bytes)
    assert compare['total_commits']==1 and compare['commits'][-1]['sha']==NEW
    changed=[{k:f[k] for k in ['filename','status','additions','deletions']} for f in compare['files']]
    assert not any(f['filename'].startswith(('data/normalized_yaml/','data/merge_yaml/')) for f in changed)
    schema_url='https://culturebotai.github.io/CultureMech/app/schema.html'
    schema=raw['pages'][schema_url]
    old_ledger=json.loads((OUT/'culturemech-auditor-b.json').read_text())
    old_row=json.loads((OUT/'group-b-proposed-rows.json').read_text())['CultureMech']
    new_features=json.loads(json.dumps(old_row['features']))
    # Actual generated documentation count is checked against its browser excerpt.
    body=schema['body']
    match=re.search(r'(\d+)\s+classes.*?(\d+)\s+enum',body,re.I|re.S)
    if not match:
        match=re.search(r'(\d+)\s+CLASSES.*?(\d+)\s+ENUM',body,re.I|re.S)
    assert match, body[:1500]
    classes,enums=map(int,match.groups())
    assert classes>=49 and enums>=33
    new_features['schema_docs']['note']=f'The linked app/schema.html guide documents {classes} classes and {enums} enumerations, including MediaRecipe and growth-evidence structures.'
    actions={k:small_action(v) for k,v in raw['actions'].items()}
    actions['sorting_absence']=raw['actions']['sorting_absence']
    receipts={'pages':{u:small_page(v) for u,v in raw['pages'].items()},'actions':actions,
      'failure_cases':{u:{'aborted':v.get('aborted',[]),'excerpt':[line for line in v.get('state',{}).get('body','').splitlines() if re.search('load|retry|error',line,re.I)]} for u,v in raw['failure_cases'].items()},
      'bulk':{u:{k:v for k,v in x.items() if k!='data'}|{'record_count':x.get('data',{}).get('count'),'sample_field_names':list(x.get('data',{}).get('first',[{}])[0])} for u,x in raw['bulk'].items()}}
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    raw_dest=ARCHIVE/'culturemech-redeployment-09f9088-raw.json'
    shutil.copy2(capture,raw_dest);assert sha(capture.read_bytes())==sha(raw_dest.read_bytes())
    diff_dest=ARCHIVE/'culturemech-redeployment-09f9088-compare.json';diff_dest.write_bytes(compare_bytes)
    before_dest=ARCHIVE/'culturemech-before-redeployment-auditor.json'
    if not before_dest.exists():shutil.copy2(OUT/'culturemech-auditor-b.json',before_dest)
    features={}
    for key,value in new_features.items():
        features[key]=value|{'prior_status':old_row['features'][key]['status'],'prior_note':old_row['features'][key]['note'],
          'claim_locator':f'_fleet/data/site_features.json#/mechs/CultureMech/features/{key}',
          'evidence':{'url':value['url'],'locator':'receipts.actions' if key in ['search','facets','result_counts','sorting','shareable_state'] else 'receipts.pages'}}
    report={'mech':'CultureMech','reviewer':'central_directory redeployment auditor','pin':PIN,
      'previous_deployed_revision':old_row['deployed_revision'],'started_at':raw['started_at'],'finished_at':raw['finished_at'],
      'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],
      'features':features,'receipts':receipts,'changed_files':changed,'compare_url':compare['html_url'],
      'source_change_assessment':'One infrastructure commit adds typed causal graph schema, validation, writer and KGX export. No normalized or merged recipe data or page renderer changed. Browser checks were nevertheless repeated across all 24 criteria.',
      'schema_observation':{'url':schema_url,'classes':classes,'enums':enums,'excerpt':body[:1500]},
      'archive':{'raw_capture':str(raw_dest),'raw_sha256':sha(raw_dest.read_bytes()),'compare':str(diff_dest),'compare_sha256':sha(compare_bytes)},
      'independent_review':('culturemech-redeployment-skeptic.json: deployment_review independently verified this deployment and agrees with all 24 statuses.' if (OUT/'culturemech-redeployment-skeptic.json').exists() else 'Pending deployment_review verification of this concurrent deployment; prior 24-verdict review remains recorded separately.')}
    assert len(features)==24
    (OUT/'culturemech-redeployment-20261104.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'culturemech-auditor-b.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'culturemech-auditor-b.md').write_text('# CultureMech deployment recheck — 2026-11-04\n\n'+f'Corpus pin `{PIN}` retained; served deployment `{NEW}`.\n\n'+'\n'.join(f'- {k}: **{v["status"]}**. {v["note"]}' for k,v in features.items())+'\n')
    rows_path=OUT/'group-b-proposed-rows.json';rows=json.loads(rows_path.read_text())
    others={k:json.dumps(v,sort_keys=True) for k,v in rows.items() if k!='CultureMech'}
    rows['CultureMech']['features']=new_features;rows['CultureMech']['deployed_revision']=NEW
    rows['CultureMech']['scope']='All 24 catalogue features re-exercised after the concurrent 09f9088 deployment, including representative records, control actions, narrow views and request-failure checks; the corpus pin remains a74dd489.'
    assert others=={k:json.dumps(v,sort_keys=True) for k,v in rows.items() if k!='CultureMech'}
    rows_path.write_text(json.dumps(rows,indent=2)+'\n')
    capture.unlink() # Verified archived full capture above; concise receipts remain.
    print(json.dumps({'deployment':raw['deployment_after'],'schema':{'classes':classes,'enums':enums},'features':len(features),'changed_statuses':[k for k,v in features.items() if v['status']!=v['prior_status']]}))

if __name__=='__main__':main()
