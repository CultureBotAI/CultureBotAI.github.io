#!/usr/bin/env python3
"""Summarize retained Group B live browser receipts for human review, 2026-11-19.

Input: owned revalidation JSON receipts. Output: compact stdout only.
Serves the November 19 feature-only refresh; never rewrites raw receipts.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '_fleet/reviews/site-features-20261119/group-b'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--page')
    parser.add_argument('--body', action='store_true')
    args = parser.parse_args()
    data = json.loads((OUT / (args.name.lower() + '.json')).read_text())
    if args.page:
        for url, page in data['pages'].items():
            if args.page not in url: continue
            print(url)
            if args.body:
                print(page.get('body', '')); continue
            print(json.dumps({k: page.get(k) for k in ['headings', 'footer', 'suite_links', 'graph', 'selects', 'buttons']}, indent=2))
            for link in page.get('relevant_links', []):
                print(link['text'], link['url'])
        return
    result = {'mech': data['mech'], 'complete': data.get('complete'),
      'deployment': data.get('deployment_after'),
      'pages': [{ 'url': u, 'status': p.get('http_status'), 'error': p.get('error'),
        'mobile': [p.get('resized_390', {}).get('scroll_width'), p.get('fresh_390', {}).get('scroll_width')],
        'theme': p.get('theme'), 'styles': p.get('styles'), 'graph': p.get('graph'),
        'counts': p.get('counts'), 'body_start': p.get('body', '')[:800],
        'footer': p.get('footer', '')} for u,p in data['pages'].items()],
      'actions': {k: {f:v.get(f) for f in ['url','counts','controls','checked','first_results','error']} for k,v in data['actions'].items()},
      'failure_cases': {u:{'aborted':v.get('aborted'), 'error':v.get('error'),
        'failed_body_start':v.get('failed',{}).get('body','')[:2000],
        'failed_messages':v.get('failed',{}).get('load_messages'),
        'recovered_messages':v.get('recovered',{}).get('load_messages')}
        for u,v in data.get('failure_cases',{}).items()},
      'bulk':{u:{'status':v.get('http_status'),'bytes':v.get('bytes'),'data':v.get('data')}
        for u,v in data.get('bulk',{}).items()}}
    # Avoid printing whole embedded catalogue metadata while retaining its counts.
    for item in result['bulk'].values():
        for key, value in (item.get('data') or {}).items():
            if isinstance(value,dict) and len(json.dumps(value))>1500:
                item['data'][key] = {'keys':list(value), 'count':value.get('count'),
                                     'record_count':value.get('record_count')}
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
