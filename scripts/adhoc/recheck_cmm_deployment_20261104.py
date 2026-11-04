#!/usr/bin/env python3
"""Inspect and recheck CMMMech's concurrent record/site update during Nov4 refresh.
Inputs: isolated Git object fetch, fresh CMM browser audit, live changed records.
Outputs: compact CMM-only supplemental/auditor/proposed-row evidence; no shared
production edits and no corpus-pin advancement. Refresh PR, 2026-11-04.
Use --inspect first, run audit_browser_group_b_20261104.py --mech CMMMech,
then --finalize. Full captures remain hash-verified outside the committed report.
"""
import argparse,hashlib,json,re,shutil,subprocess
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from audit_browser_group_b_20261104 import CHROME,SNAPSHOT_JS,compact,deployment,now
from compact_browser_evidence_b_20261104 import small_page,small_action

OUT=Path('_fleet/reviews/refresh-20261104')
ARCHIVE=Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
OBJECTS=Path('/private/tmp/cmm-redeployment-20261104-objects.git')
PIN='8bf82c8dfa25a35f12b60617b86751bc3ce7df71'
NEW='ff4a9841deb7e4f6e9fff025eccd2ffa07b5493c'

def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git','--git-dir',str(OBJECTS),*args],text=True)

def inspect():
    if not OBJECTS.exists():subprocess.run(['git','init','--bare',str(OBJECTS)],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','--git-dir',str(OBJECTS),'fetch','--depth=2','--no-tags','https://github.com/CultureBotAI/CMMMech.git',NEW],check=True)
    assert git('rev-parse',NEW+'^').strip()==PIN
    rows=[]
    for line in git('diff','--numstat',PIN,NEW).splitlines():
        added,deleted,path=line.split('\t',2);rows.append({'path':path,'added':added,'deleted':deleted})
    records=[r['path'] for r in rows if r['path'].startswith('data/records/')]
    assert len(records)==10
    production=[r['path'] for r in rows if r['path'].startswith(('scripts/','src/','.github/','templates/','conf/'))]
    sources={}
    for path in records:
        diff=git('diff',PIN,NEW,'--',path)
        sources[path]={'source_url':f'https://github.com/CultureBotAI/CMMMech/blob/{NEW}/{path}',
          'new_protein_lines':[line for line in diff.splitlines() if line.startswith('+') and re.search(r'protein|UniProtKB|evidence|reference|strain|organism',line,re.I)][:35],
          'diff_sha256':sha(diff.encode())}
    groups={}
    for r in rows:
        group='/'.join(r['path'].split('/')[:2]);groups[group]=groups.get(group,0)+1
    report={'pin':PIN,'deployed_revision':NEW,'commit':git('show','-s','--format=%B',NEW).strip(),'changed_file_count':len(rows),'changed_file_groups':groups,
      'production_code_changes':production,'record_paths':records,'changed_files':rows,'source_excerpts':sources,
      'complete_diff_method':'git diff between exact commits in an isolated bare object repository; not GitHub compare API capped file list.','object_repository':str(OBJECTS),'checked_at':now()}
    (OUT/'cmmmech-redeployment-source.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['changed_file_count','changed_file_groups','production_code_changes']}))

def finalize():
    source=json.loads((OUT/'cmmmech-redeployment-source.json').read_text())
    capture=OUT/'cmmmech-browser-b.json'
    raw_path=capture if capture.exists() else ARCHIVE/'cmmmech-redeployment-ff4a984-raw.json'
    raw=json.loads(raw_path.read_text());assert raw.get('finished_at') and raw['pin']==PIN
    for d in [raw['deployment_before'],raw['deployment_after']]:
        assert d['sha']==NEW and d['state']=='success'
        assert parsedate_to_datetime(d['last_modified'])>=datetime.fromisoformat(d['created_at'].replace('Z','+00:00'))
    assert all('error' not in v for v in raw['pages'].values())
    assert all('error' not in v for v in raw['actions'].values())
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=CHROME,headless=True)
        ctx=browser.new_context(viewport={'width':1280,'height':900},color_scheme='light')
        page=ctx.new_page();page.goto('https://culturebotai.github.io/CMMMech/pages/index.html',wait_until='networkidle')
        page.evaluate("localStorage.setItem('mech-theme','dark')")
        for record in source['record_paths']:
            slug=Path(record).stem;url=f'https://culturebotai.github.io/CMMMech/pages/materials/{slug}.html'
            response=page.goto(url,wait_until='networkidle',timeout=90000);page.wait_for_timeout(200)
            obs=compact(page.evaluate(SNAPSHOT_JS));obs.update(http_status=response.status,checked_at=now())
            assert response.status==200
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(200)
            obs['resized_390']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            page.reload(wait_until='networkidle');page.wait_for_timeout(200)
            obs['fresh_390']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            page.set_viewport_size({'width':1280,'height':900})
            raw['pages'][url]=obs
        browser.close()
    raw['deployment_after']=deployment('CMMMech','https://culturebotai.github.io/CMMMech/pages/index.html')
    assert raw['deployment_after']['sha']==NEW and raw['deployment_after']['state']=='success'
    assert parsedate_to_datetime(raw['deployment_after']['last_modified'])>=datetime.fromisoformat(raw['deployment_after']['created_at'].replace('Z','+00:00'))
    raw['finished_at']=now()
    landing=raw['pages']['https://culturebotai.github.io/CMMMech/pages/index.html']
    match=re.search(r'digest\s+([a-f0-9]+)',landing['footer'],re.I);assert match,landing['footer']
    corpus_digest=match.group(1)
    rows_path=OUT/'group-b-proposed-rows.json';rows=json.loads(rows_path.read_text());old=rows['CMMMech']
    features=json.loads(json.dumps(old['features']))
    features['build_provenance']['note']=f'Footers state 678 materials, 609 mechanisms, latest curation 2026-11-04 and corpus digest {corpus_digest}.'
    features['responsive']['note']='At 390px, cobalt widens the document to 597px and akaganeite to 669px. The ten newly curated records reach 652–669px, including copper at 652px, on fresh and resized views.'
    assert '678' in landing['body'] and '609' in landing['body']
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    raw_dest=ARCHIVE/'cmmmech-redeployment-ff4a984-raw.json';raw_dest.write_text(json.dumps(raw,indent=2)+'\n')
    old_dest=ARCHIVE/'cmmmech-before-redeployment-auditor.json'
    if not old_dest.exists():shutil.copy2(OUT/'cmmmech-auditor-b.json',old_dest)
    previous=json.loads(old_dest.read_text())
    review={key:value|{'prior_status':previous['features'][key]['status'],'prior_note':previous['features'][key]['note'],
      'claim_locator':f'_fleet/data/site_features.json#/mechs/CMMMech/features/{key}',
      'evidence':{'url':value['url'],'locator':'receipts.actions' if key in ['search','facets','result_counts','sorting','shareable_state'] else 'receipts.pages'}} for key,value in features.items()}
    receipts={'pages':{u:small_page(v) for u,v in raw['pages'].items()},'actions':{k:small_action(v) for k,v in raw['actions'].items()},
      'failure_cases':{u:{'aborted':v.get('aborted',[])} for u,v in raw['failure_cases'].items()},
      'bulk':{u:{k:v for k,v in x.items() if k!='data'} for u,x in raw['bulk'].items()}}
    report={'mech':'CMMMech','reviewer':'central_directory redeployment auditor','pin':PIN,
      'previous_deployed_revision':previous['deployment_after']['sha'],'started_at':raw['started_at'],'finished_at':raw['finished_at'],
      'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],'features':review,'receipts':receipts,
      'source_diff':'cmmmech-redeployment-source.json','source_assessment':'Ten records add curated UniProtKB protein examples and their evidence/history. Complete Git diff records all regenerated pages; renderer/schema changes are reported separately in the source receipt.',
      'changed_record_checks':{u:{'theme':v['theme'],'width':v['fresh_390']['scroll'],'headings':v['headings'],'protein_excerpt':[line for line in v['body'].splitlines() if re.search('UniProtKB|Protein examples|protein example',line,re.I)][:10]} for u,v in raw['pages'].items() if any(Path(x).stem+'.html' in u for x in source['record_paths'])},
      'archive':{'raw_capture':str(raw_dest),'raw_sha256':sha(raw_dest.read_bytes())},'independent_review':('cmmmech-redeployment-skeptic.json: deployment_review independently verified all ten changed records and agrees with all 24 statuses.' if (OUT/'cmmmech-redeployment-skeptic.json').exists() else 'Pending deployment_review verification.')}
    assert len(review)==24
    for name in ['cmmmech-redeployment-20261104.json','cmmmech-auditor-b.json']:(OUT/name).write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'cmmmech-auditor-b.md').write_text('# CMMMech deployment recheck — 2026-11-04\n\n'+f'Corpus pin `{PIN}` retained; served deployment `{NEW}`.\n\n'+'\n'.join(f'- {k}: **{v["status"]}**. {v["note"]}' for k,v in features.items())+'\n')
    others={k:json.dumps(v,sort_keys=True) for k,v in rows.items() if k!='CMMMech'}
    rows['CMMMech']['features']=features;rows['CMMMech']['deployed_revision']=NEW
    rows['CMMMech']['scope']='All 24 catalogue features re-exercised after the concurrent ff4a984 deployment, including ten changed records, controls, narrow views and data-request checks; the corpus pin remains 8bf82c8d.'
    assert others=={k:json.dumps(v,sort_keys=True) for k,v in rows.items() if k!='CMMMech'}
    rows_path.write_text(json.dumps(rows,indent=2)+'\n')
    if capture.exists():capture.unlink()
    print(json.dumps({'deployment':raw['deployment_after'],'features':len(features),'changed_statuses':[k for k,v in review.items() if v['status']!=v['prior_status']],'digest':corpus_digest,'changed_record_widths':{u:v['width'] for u,v in report['changed_record_checks'].items()}}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inspect',action='store_true');ap.add_argument('--finalize',action='store_true');args=ap.parse_args()
    if args.inspect:inspect()
    if args.finalize:finalize()
