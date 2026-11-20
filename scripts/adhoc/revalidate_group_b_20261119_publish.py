#!/usr/bin/env python3
"""Package Group B Nov19 receipts without altering original raw evidence.

Inputs: owned completed JSON browser receipts. Outputs: deterministic gzip copies,
SHA-256 inventory and compact summary beside them. The uncompressed originals
remain untouched locally; stage the gzip files and summaries for the audit PR.
"""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'_fleet/reviews/site-features-20261119/group-b'
NAMES=['culturemech','mediaingredientmech','proteintraitsmech','dufmech','naturalproductmech','cmmmech']

def main():
    inventory={};summary={}
    for name in NAMES:
        for suffix in ['', '-supplement', '-controls']:
            path=OUT/(name+suffix+'.json')
            if not path.exists():continue
            payload=path.read_bytes();data=json.loads(payload);assert data['complete'],str(path)
            archive=path.with_suffix('.json.gz');compressed=gzip.compress(payload,compresslevel=9,mtime=0)
            if archive.exists():assert archive.read_bytes()==compressed,str(archive)
            else:archive.write_bytes(compressed)
            assert gzip.decompress(archive.read_bytes())==payload
            inventory[str(path.relative_to(ROOT))]={'archive':str(archive.relative_to(ROOT)),
              'uncompressed_bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),
              'gzip_bytes':len(compressed),'gzip_sha256':hashlib.sha256(compressed).hexdigest()}
            pages={u:{'http_status':p.get('http_status'),'error':p.get('error'),
                'title':p.get('title'),'headings':p.get('headings'), 'footer':p.get('footer'),
                'mobile_widths':{'fresh':p.get('fresh_390',{}).get('scroll_width'),'resized':p.get('resized_390',{}).get('scroll_width')},
                'theme':p.get('theme'),'suite_links':p.get('suite_links'),'graph':p.get('graph'),
                'detail_characters':len(p.get('populated_detail',''))} for u,p in data.get('pages',{}).items()}
            actions={k:{'url':a.get('url'),'counts':a.get('counts'),'controls':a.get('controls'),'checked':a.get('checked'),'error':a.get('error')} for k,a in data.get('actions',{}).items()}
            summary[path.stem]={'archive':str(archive.relative_to(ROOT)),'deployment_before':data.get('deployment_before'),
              'deployment_after':data.get('deployment_after'),'complete':data['complete'],'pages':pages,'actions':actions,
              'failure_cases':{u:{'aborted':v.get('aborted'),'error':v.get('error'),
                  'failed_messages':v.get('failed',{}).get('load_messages'),'recovered_messages':v.get('recovered',{}).get('load_messages')}
                  for u,v in data.get('failure_cases',{}).items()},'checks_available':list(data.get('checks',{}))}
    (OUT/'raw-artifacts.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (OUT/'receipts-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'raw_files':len(inventory),'raw_bytes':sum(v['uncompressed_bytes'] for v in inventory.values()),'gzip_bytes':sum(v['gzip_bytes'] for v in inventory.values())}))

if __name__=='__main__':main()
