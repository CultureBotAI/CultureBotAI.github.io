#!/usr/bin/env python3
"""Package immutable Nov19 browser receipts without repeating large DOM text.

Inputs: explicit JSON paths; outputs: deterministic gzip copies and SHA index.
For the feature revalidation PR, 2026-11-19. Originals are preserved unchanged.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    assert not args.index.exists(), 'Use a fresh index path'
    receipts = []
    for path in args.input:
        original = path.read_bytes()
        value = json.loads(original)
        assert value.get('complete', bool(value.get('finished_at'))), path
        archive = path.with_suffix(path.suffix + '.gz')
        compressed = gzip.compress(original, compresslevel=9, mtime=0)
        if archive.exists():
            assert archive.read_bytes() == compressed, 'Existing archive differs'
        else:
            archive.write_bytes(compressed)
        assert gzip.decompress(archive.read_bytes()) == original
        receipts.append({'source': str(path.relative_to(ROOT)) if path.is_absolute() else str(path),
                         'archive': str(archive.relative_to(ROOT)) if archive.is_absolute() else str(archive),
                         'source_sha256': hashlib.sha256(original).hexdigest(),
                         'archive_sha256': hashlib.sha256(compressed).hexdigest(),
                         'source_bytes': len(original), 'archive_bytes': len(compressed),
                         'deployment': value.get('deployment_after')})
    args.index.write_text(json.dumps({'format': 'gzip-json; decompress before resolving JSON pointers',
                                    'artifacts': receipts}, indent=2) + '\n')
    assert len(json.loads(args.index.read_text())['artifacts']) == len(args.input)
    print(json.dumps({'index': str(args.index), 'receipts': len(receipts), 'compressed_bytes': sum(r['archive_bytes'] for r in receipts)}))


if __name__ == '__main__':
    main()
