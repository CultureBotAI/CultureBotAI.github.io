#!/usr/bin/env python3
"""Check central Mech card/Explore URL reachability for the Nov 4 refresh PR.

Inputs: maintained template URLs; HTTP HEAD requests. Outputs:
hand-claims-links[-canary].json. HEAD does not prove a visual works; independent
browser audits provide that evidence. Use --limit 1 before the full pass.
Date: 2026-11-04. No source edits or shared-checkout writes.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    template = (ROOT / '_fleet/mechs_template.md').read_bytes()
    urls = sorted(set(html.unescape(url) for url in re.findall(r'https://culturebotai\.github\.io/[^\s\"<>)]+', template.decode())))
    if args.limit:
        urls = urls[:args.limit]
    result = {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'template_sha256': hashlib.sha256(template).hexdigest(), 'method': 'HTTP HEAD; browser behavior checked separately', 'urls': []}
    for url in urls:
        try:
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'xmech-refresh-audit'})
            with urllib.request.urlopen(req, timeout=30) as response:
                row = {'url': url, 'status': response.status, 'final_url': response.url,
                       'last_modified': response.headers.get('Last-Modified')}
        except Exception as exc:
            row = {'url': url, 'error': str(exc)}
        result['urls'].append(row)
        print(row.get('status', 'ERROR'), url, flush=True)
    suffix = '-canary' if args.limit else ''
    path = ROOT / f'_fleet/reviews/refresh-20261104/hand-claims-links{suffix}.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    assert path.stat().st_size > 100 and result['urls']
    print(f'Verified receipt: {path} ({path.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
