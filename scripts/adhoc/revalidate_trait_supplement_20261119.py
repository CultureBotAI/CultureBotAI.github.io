#!/usr/bin/env python3
"""Verify TraitMech public downloads and record handoff for the Nov19 audit PR.

Inputs: completed live audit; outputs: immutable hash/count/link receipt.
No record text is republished. Date: 2026-11-19.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

from revalidate_root_sites_20261119 import deployment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    raw = json.loads(args.input.read_text())
    assert raw['complete']
    landing = 'https://culturebotai.github.io/TraitMech/pages/index.html'
    before = deployment('TraitMech', landing)
    assert before['sha'] == raw['deployment_after']['sha']
    urls = set()
    for page in raw['pages'].values():
        for request in page.get('requests', []):
            if request['url'].endswith('.json') and 'TraitMech/' in request['url']:
                urls.add(request['url'])
        for link in page.get('desktop', {}).get('links', []):
            if link['url'].endswith('.json') or 'PathwayMech/pages/records/' in link['url'] or link['text'] == 'Schema':
                urls.add(link['url'])
    receipts = []
    for url in sorted(urls):
        with urllib.request.urlopen(url, timeout=60) as response:
            body = response.read()
            receipt = {'url': url, 'status': response.status, 'final_url': response.url,
                       'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
        if url.endswith('.json'):
            value = json.loads(body)
            receipt['top_type'] = type(value).__name__
            if isinstance(value, list):
                receipt['rows'] = len(value)
                receipt['first_record_keys'] = sorted(value[0]) if value and isinstance(value[0], dict) else []
            else:
                receipt['keys'] = list(value)
                receipt['list_counts'] = {k: len(v) for k, v in value.items() if isinstance(v, list)}
                receipt['first_record_keys'] = {k: sorted(v[0]) for k, v in value.items() if isinstance(v, list) and v and isinstance(v[0], dict)}
        receipts.append(receipt)
    after = deployment('TraitMech', landing)
    assert before['sha'] == after['sha'] and before['id'] == after['id']
    result = {'mech': 'TraitMech', 'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'deployment_before': before, 'deployment_after': after, 'downloads_and_links': receipts, 'complete': True}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    assert json.loads(args.output.read_text())['complete']
    print(json.dumps({'output': str(args.output), 'links': len(receipts)}))


if __name__ == '__main__':
    main()
